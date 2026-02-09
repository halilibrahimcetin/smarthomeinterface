import time
import threading
import paho.mqtt.client as paho
from paho import mqtt
import RPi.GPIO as gpio
import adafruit_dht
import board
import cv2 
from flask import Flask, render_template_string, Response # Flask eklendi


gpio.setmode(gpio.BCM)

# DHT sensörü
DHT_PIN = board.D24
try:
    dht_device = adafruit_dht.DHT11(DHT_PIN)
except Exception as e:
    print(f"DHT11 başlatma hatası: {e}. Sensör döngüsü başlatılmayacak.")
    dht_device = None

# Pin 
heater_pin = 2
in1 = 20
in2 = 16
ena = 12
window_pin = 17
door_pin = 27
buzzer_pin = 22
flame_pin = 21
gas_pin = 14
LED1 = 1
LED2 = 7
LED3 = 8

gpio.setup(heater_pin, gpio.OUT)
gpio.setup(in1, gpio.OUT)
gpio.setup(in2, gpio.OUT)
gpio.setup(ena, gpio.OUT)
gpio.setup(window_pin, gpio.OUT)
gpio.setup(door_pin, gpio.OUT)
gpio.setup(buzzer_pin, gpio.OUT)
gpio.output(in1, gpio.HIGH) 
gpio.output(in2, gpio.LOW)
gpio.setup(flame_pin, gpio.IN)
gpio.setup(gas_pin,gpio.IN)
gpio.setup([LED1,LED2,LED3],gpio.OUT)

#   LED
PWM_FREQ = 1000
led1pwm=gpio.PWM(LED1, PWM_FREQ)
led2pwm=gpio.PWM(LED2, PWM_FREQ)
led3pwm=gpio.PWM(LED3, PWM_FREQ)
led1pwm.start(0)
led2pwm.start(0)
led3pwm.start(0)

#   FAN
fan_pwm = gpio.PWM(ena, 100) 
fan_pwm.start(0)

#   SERVO
window_control = gpio.PWM(window_pin, 50) 
window_control.start(0)
door_control = gpio.PWM(door_pin, 50) 
door_control.start(0)

alarmbool = False


app = Flask(__name__)
HTML_PAGE = """
<!DOCTYPE html>
<html>
      <head>
      </head>
      <body height="274" width="488" >
        <img src="/video_feed" width="460" height="250">
      </body>
    </html>
"""

def generate_frames():
    # Index 0 genelde varsayılandır. Çalışmazsa -1 veya 1 dene.
    camera = cv2.VideoCapture(0) 
    
    # Kamera açıldı mı kontrol et
    if not camera.isOpened():
        print("!!! HATA: Kamera açılamadı! Bağlantıyı veya Legacy modunu kontrol et.")
        return

    # Kamera çözünürlüğü
    camera.set(3, 640)
    camera.set(4, 480)

    while True:
        success, frame = camera.read()
        if not success:
            print("!!! HATA: Görüntü karesi okunamadı (Frame drop or camera disconnected).")
            break
        else:
            # Görüntüyü çevir (Mirror effect - isteğe bağlı)
            # frame = cv2.flip(frame, 1) 
            
            # Görüntüyü JPEG formatına çevir
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    camera.release()

@app.route('/')


@app.route('/video_feed')
def video_feed():
    """Video akış rotası"""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask():
    """Flask uygulamasını thread içinde çalıştırır."""
    # 0.0.0.0 ile ağdaki tüm cihazlardan erişime izin ver
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# --- Aktüatör Fonksiyonları (MEVCUT KOD) ---

def window_angle(angle):
    duty = 2 + (angle / 18) 
    gpio.output(window_pin, True)
    window_control.ChangeDutyCycle(duty)
    time.sleep(0.5)
    gpio.output(window_pin, False)
    window_control.ChangeDutyCycle(0)

def door_angle(angle):
    duty = 2 + (angle / 18)
    gpio.output(door_pin, True)
    door_control.ChangeDutyCycle(duty)
    time.sleep(0.5)
    gpio.output(door_pin, False)
    door_control.ChangeDutyCycle(0)

def set_led_brightness(pwm_obj, payload):
    try:
        brightness = int(payload)
        if 0 <= brightness <= 100:
            pwm_obj.ChangeDutyCycle(brightness)
            print(f"-> Parlaklık %{brightness} olarak ayarlandı.")
        else:
            print(f"Hata: Geçersiz parlaklık değeri: {brightness}")
    except ValueError:
        print(f"Hata: Gelen mesaj tamsayıya çevrilemedi: {payload}")


# --- Sensör Döngüleri ve Alarm ---

def alarm_loop():
    global alarmbool
    while alarmbool:
        gpio.output(buzzer_pin, gpio.HIGH)
        time.sleep(0.2)
        gpio.output(buzzer_pin, gpio.LOW)
        time.sleep(0.2)

def fire_loop():
    last_state = None
    while True:
        flame_detected = gpio.input(flame_pin) 
        if flame_detected != last_state:
            client.publish("sensor/fire", payload="0" if flame_detected else "1", qos=0)
            print("SAFE" if flame_detected else "Fire DETECTED!!")
            last_state = flame_detected
        time.sleep(1)

def temp_loop():
    if dht_device is None:
        print("Sıcaklık sensörü başlatılamadığı için temp_loop atlanıyor.")
        return
        
    while True:
        try:
            temperature = dht_device.temperature
            humidity = dht_device.humidity
            
            if temperature is not None:
                client.publish("sensor/temperature/interior", f"{temperature}", qos=0)
            if humidity is not None:
                client.publish("sensor/temperature/outside", f"{humidity}", qos=0)
                
        except RuntimeError:
            pass
        except Exception as e:
            print(f"?? Beklenmedik DHT Hata: {e}")
            
        time.sleep(5)

def gas_loop():
    last_state = None
    while True:
        gas_detected = gpio.input(gas_pin)
        if gas_detected != last_state:
            client.publish("sensor/gas",payload="0" if gas_detected else "1",qos=0)
            print("SAFE" if gas_detected else "LEAK!")
            last_state = gas_detected
        time.sleep(1)


# --- MQTT Fonksiyonları ---

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code " + str(rc))
    client.subscribe("temp/heater", qos=0)
    client.subscribe("temp/fan/value", qos=0)
    client.subscribe("temp/fan", qos=0)
    client.subscribe("temp/window", qos=0)
    client.subscribe("temp/door", qos=0)
    client.subscribe("security/test", qos=0)
    client.subscribe("sensor/temp",qos=0)
    client.subscribe("lights/room1",qos=0)
    client.subscribe("lights/room2",qos=0)
    client.subscribe("lights/room3",qos=0)
    

def on_message(client, userdata, msg):
    global alarmbool
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"Topic: {topic}, Message: {payload}")

    if topic == "temp/heater":
        if payload == "1":
            gpio.output(heater_pin, gpio.HIGH)
            print("Heater ON")
        elif payload == "0":
            gpio.output(heater_pin, gpio.LOW)
            print("Heater OFF")

    elif topic == "temp/fan":
        if payload == "1":
            fan_pwm.ChangeDutyCycle(10)
            print("Fan started at 10% power")
        elif payload == "0":
            fan_pwm.ChangeDutyCycle(0)
            print("Fan OFF")

    elif topic == "temp/fan/value":
        try:
            speed = int(payload)
            if 0 <= speed <= 100:
                fan_pwm.ChangeDutyCycle(speed)
                print(f"Fan speed set to {speed}%")
            else:
                print("Invalid fan value")
        except ValueError:
            print("Invalid fan value (Must be 0-100 integer)")

    elif topic == "temp/window":
        if payload == "1":
            window_angle(120) 
        else:
            window_angle(0) 

    elif topic == "temp/door":
        if payload == "1":
            door_angle(120) 
        else:
            door_angle(0) 

    elif topic == "security/test":
        if payload == "1":
            if not alarmbool:
                alarmbool = True
                threading.Thread(target=alarm_loop, daemon=True).start()
                print("Alarm thread started")
        elif payload == "0":
            alarmbool = False
            gpio.output(buzzer_pin, gpio.LOW)
            print("Alarm deactivated")

    elif topic == "lights/room1":
        set_led_brightness(led1pwm, payload)
    elif topic == "lights/room2":
        set_led_brightness(led2pwm, payload)
    elif topic == "lights/room3":
        set_led_brightness(led3pwm, payload)
    

def on_publish(client, userdata, mid, properties=None):
    pass

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed:", str(mid), str(granted_qos))

# --- Ana Çalışma Alanı ---

client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_subscribe = on_subscribe

client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set("raspberrysender", "123456789Aa")
client.connect("b791a9e55d664f41aad1a008215d6281.s1.eu.hivemq.cloud", 8883)

# Sensör thread'lerini başlat
threading.Thread(target=fire_loop, daemon=True).start()
threading.Thread(target=gas_loop,daemon=True).start()

if dht_device is not None:
    threading.Thread(target=temp_loop, daemon=True).start()

# --- FLASK KAMERA YAYININI BAŞLAT (YENİ) ---
print("Kamera sunucusu başlatılıyor (Port 5000)...")
threading.Thread(target=run_flask, daemon=True).start()

# Ana thread'i MQTT döngüsüne ayır
try:
    print("Sistem başlatıldı. Sensörler, Kamera ve MQTT aktif.")
    client.loop_forever()

except KeyboardInterrupt:
    print("\nProgram sonlandırılıyor...")

finally:
    led1pwm.stop()
    led2pwm.stop()
    led3pwm.stop()
    fan_pwm.stop()
    window_control.stop()
    door_control.stop()
    gpio.cleanup()
    
    # Kamerayı serbest bırak (eğer global tanımlandıysa)
    # cv2.destroyAllWindows() 
    print("GPIO temizlendi ve program sonlandı.")
