# Öğretmen Dosya Paylaşım Sistemi (Python + Socket + PyQt)

Bu proje, yazılım geliştirme eğitimi sırasında **öğretmenin kendi bilgisayarındaki bir klasörü sadece öğrencilerin görebileceği şekilde paylaşmasını** sağlar. Öğrenciler, ağ üzerinden paylaşılan bu klasörü görüp içindeki dosyaları sadece *okuyabilir*.

---

## Temel Özellikler

- Öğretmen tarafında klasör paylaşımı
  - Belirtilen klasörü ağ üzerinden paylaşma
  - Gerçek zamanlı dosya değişiklik takibi
  - İzin yönetimi (salt okunur erişim)

- Öğrenci istemci fonksiyonları
  - Ağaç yapısında dosya gezgini
  - Dosya içeriği önizleme
  - Güvenli içerik görüntüleme (path traversal koruması)

- Sistem Özellikleri
  - Çoklu dil desteği (Türkçe/İngilizce)
  - Otomatik sunucu keşfi (Broadcast)
  - Detaylı loglama sistemi

---

## Teknik Altyapı

![System Architecture](docs/architecture.png) 

```
Python 3.8+
│
├── Socket Programming - Temel ağ iletişimi
├── PyQt5 - Grafik kullanıcı arayüzü
├── JSON - Veri serialization
└── Logging - Sistem olayları takibi
```

---

## Kurulum & Çalıştırma

### Gereksinimler
```bash
pip install -r requirements.txt
```

### Sunucu Başlatma
```bash
# Öğretmen bilgisayarında
python server/server.py --path /paylaşılacak/klasör
```

### İstemci Başlatma
```bash
# Öğrenci bilgisayarında
python client/gui.py
```

---

## Yapılandırma

`config/client_preferences.ini` dosyası üzerinden:
```ini
[NETWORK]
server_ip = 192.168.1.100
server_port = 5000

[UI]
language = tr
theme = dark
```

---

## Güvenlik

- Sıkı path validation kontrolü
- İstemcide dosya yazma yetkisi yok
- Tüm iletişim şifrelenmiş JSON formatında
- Whitelist tabanlı dosya uzantıları:
  ```python
  ALLOWED_EXTENSIONS = ['.py', '.txt', '.md', '.json', '.ini']
  ```

---

## Katkı

1. Repoyu fork edin
2. Özellik branch'i oluşturun (`git checkout -b feature/awesome-feature`)
3. Değişiklikleri commit edin (`git commit -m 'Add awesome feature'`)
4. Branch'i pushlayın (`git push origin feature/awesome-feature`)
5. Pull Request açın

---

## Lisans

MIT Lisansı - Detaylar için [LICENSE](LICENSE) dosyasına bakınız.
