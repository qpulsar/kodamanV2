import json
import os
import logging

# Logger oluştur
logger = logging.getLogger('FileServer.Settings')

class SettingsManager:
    """
    Sunucu ayarlarını saklamak ve yüklemek için kullanılan sınıf.
    """
    def __init__(self, settings_file="server_settings.json"):
        """
        Ayarlar yöneticisini başlat.
        
        Args:
            settings_file (str): Ayarların saklanacağı dosya yolu
        """
        self.settings_file = settings_file
        self.default_settings = {
            "base_dir": os.path.expanduser("~"),  # Varsayılan olarak kullanıcı klasörü
            "host": "0.0.0.0",
            "port": 9009,
            "allowed_extensions": [
                '.txt', '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.js', '.html', '.css',
                '.json', '.xml', '.md', '.csv', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp3', '.mp4', '.wav', '.avi'
            ],
            "excluded_directories": [
                '__pycache__', 'venv', '.venv', 'env', '.env', '.git', '.idea', '.vscode', 
                'node_modules', 'dist', 'build', '.pytest_cache', '.ipynb_checkpoints'
            ],
            "excluded_extensions": [
                '.pyc', '.pyo', '.so', '.dll', '.exe', '.bin', '.dat', '.db', '.sqlite', '.sqlite3'
            ]
        }
        self.settings = self.load_settings()
        
    def load_settings(self):
        """
        Ayarları dosyadan yükle, dosya yoksa varsayılan ayarları kullan.
        
        Returns:
            dict: Yüklenen ayarlar
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"Ayarlar yüklendi: {self.settings_file}")
                return settings
            else:
                logger.info(f"Ayar dosyası bulunamadı, varsayılan ayarlar kullanılıyor: {self.settings_file}")
                return self.default_settings.copy()
        except Exception as e:
            logger.error(f"Ayarlar yüklenirken hata oluştu: {str(e)}")
            return self.default_settings.copy()
    
    def save_settings(self, settings=None):
        """
        Ayarları dosyaya kaydet.
        
        Args:
            settings (dict, optional): Kaydedilecek ayarlar. None ise mevcut ayarlar kullanılır.
        
        Returns:
            bool: Başarılı ise True, değilse False
        """
        if settings is not None:
            self.settings = settings
            
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            logger.info(f"Ayarlar kaydedildi: {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Ayarlar kaydedilirken hata oluştu: {str(e)}")
            return False
    
    def get_setting(self, key, default=None):
        """
        Belirli bir ayarı getir.
        
        Args:
            key (str): Ayar anahtarı
            default: Ayar bulunamazsa dönecek değer
            
        Returns:
            Ayar değeri veya default
        """
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """
        Belirli bir ayarı güncelle.
        
        Args:
            key (str): Ayar anahtarı
            value: Ayar değeri
            
        Returns:
            bool: Başarılı ise True
        """
        self.settings[key] = value
        return self.save_settings()
    
    def update_settings(self, new_settings):
        """
        Birden fazla ayarı güncelle.
        
        Args:
            new_settings (dict): Güncellenecek ayarlar
            
        Returns:
            bool: Başarılı ise True
        """
        self.settings.update(new_settings)
        return self.save_settings()
