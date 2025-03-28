# 📚 Öğretmen Dosya Paylaşım Sistemi (Python + Socket + PyQt)

Bu proje, yazılım geliştirme eğitimi sırasında **öğretmenin kendi bilgisayarındaki bir klasörü sadece öğrencilerin görebileceği şekilde paylaşmasını** sağlar. Öğrenciler, ağ üzerinden paylaşılan bu klasörü görüp içindeki dosyaları sadece *okuyabilir*.

---

## 🚀 Özellikler

- 👨‍🏫 Öğretmen, bir klasörü sunucu olarak paylaşır.
- 👩‍🎓 Öğrenciler istemci GUI üzerinden klasör yapısını ağaç (Tree View) şeklinde görür.
- 📄 Dosya içeriğini salt-okunur (read-only) olarak görüntüler.
- 🔐 Güvenli klasör erişimi (path traversal engeli).
- 🎨 Kullanıcı dostu PyQt arayüzü.

---

## 🧰 Kullanılan Teknolojiler

- Python 3
- `socket` – TCP bağlantısı için
- `PyQt5` – Grafik arayüz için
- `json` – Veri mesajlaşması için

---

## 🗂️ Proje Yapısı
project/
├── server/
│   ├── server.py           # Socket sunucu
│   └── file_browser.py     # Dosya tarayıcı
│
├── client/
│   ├── client.py           # Socket istemci sınıfı
│   └── gui.py              # PyQt GUI uygulaması
│
├── shared/
│   └── protocol.py         # Mesaj protokolü (JSON tabanlı)
│
└── README.md


---

## 📦 Kurulum

### 1. Gerekli kütüphaneler

```bash
pip install pyqt5

