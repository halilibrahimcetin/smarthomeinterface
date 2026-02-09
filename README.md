# Raspberry Pi 4 & MQTT Tabanlı Akıllı Ev Kontrol Sistemi

Bu proje; Aralık 2025 tarihinde geliştirilmiş, Raspberry Pi 4'ün merkezde bulunduğu ve MQTT protokolü üzerinden haberleşen kapsamlı bir IoT ekosistemidir. C# Windows Form arayüzü ile tüm sistem yerel ağ üzerinden kontrol edilebilmektedir.

## 🚀 Projenin Amacı
Geleneksel sistemlerin aksine, bu projede **Raspberry Pi 4** merkezi kontrol ünitesi (Gateway) olarak kullanılmıştır. Temel amaç; MQTT protokolünün düşük gecikmeli ve güvenli mesajlaşma altyapısını kullanarak, evdeki sensör verilerini bir C# arayüzünde toplamak ve cihazları uzaktan yönetmektir.

## 🛠 Teknik Mimari & Protokoller
- **Ana Kontrol Ünitesi:** Raspberry Pi 4 (Linux tabanlı kontrol merkezi)
- **Haberleşme Protokolü:** MQTT (Message Queuing Telemetry Transport)
- **Kullanıcı Arayüzü:** C# .NET Framework (Windows Forms)
- **Broker:** Mosquitto MQTT Broker (RPi 4 üzerinde kurulu)

## 📦 Donanım ve Yazılım Bileşenleri
* **Raspberry Pi 4 4GB
* **MQTT Broker:** Sistemler arası veri trafiğini yöneten merkez.
* **C# Dashboard:** MQTT kütüphanesi (M2Mqtt vb.) kullanılarak geliştirilmiş, görselleştirme odaklı arayüz.
* **Sensör İstasyonları:** RPi 4'ün GPIO pinlerine veya ağa bağlı diğer birimlere entegre sensörler.
* **Röle Kartları:** Evdeki yüksek voltajlı cihazların (ışık, klima vb.) kontrolü için.

## 📋 Teknik Özellikler
- **MQTT Entegrasyonu:** Yayınla/Abone Ol (Pub/Sub) mimarisi sayesinde veriler anlık ve minimum yükle iletilir.
- **Çoklu Cihaz Desteği:** Raspberry Pi sayesinde sisteme birden fazla sensör ve kontrolcü kolayca dahil edilebilir.
- **Log Sistemi:** (Opsiyonel olarak eklediysek) Geçmiş verilerin RPi üzerinde saklanması ve arayüzden takip edilmesi.

## 📝 Mühendislik Notu
Aralık 2025'teki geliştirme sürecinde, Raspberry Pi 4'ün sunduğu Linux altyapısı sayesinde sistemin 7/24 kesintisiz çalışması hedeflenmiştir. MQTT mimarisi, projenin ilerleyen aşamalarda internet üzerinden kontrole (Cloud) açılmasına olanak sağlayacak şekilde tasarlanmıştır.
