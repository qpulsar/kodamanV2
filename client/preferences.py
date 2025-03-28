import json
import os
import logging

logger = logging.getLogger('FileClient.Preferences')

class Preferences:
    def __init__(self, config_dir):
        self.config_file = os.path.join(config_dir, 'preferences.json')
        self.defaults = {
            'connection': {
                'ip': '0.0.0.0',
                'port': 9009
            },
            'ui': {
                'language': 'tr',
                'theme': 'dark_purple.xml'
            }
        }
        self.current = self.load()

    def load(self):
        """Tercihleri yükle, dosya yoksa varsayılanları kullan"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    logger.info("Tercihler yüklendi")
                    return self._merge_with_defaults(prefs)
        except Exception as e:
            logger.error(f"Tercihler yüklenirken hata oluştu: {str(e)}")
        
        return self.defaults.copy()

    def save(self):
        """Mevcut tercihleri kaydet"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.current, f, indent=4, ensure_ascii=False)
            logger.info("Tercihler kaydedildi")
            return True
        except Exception as e:
            logger.error(f"Tercihler kaydedilirken hata oluştu: {str(e)}")
            return False

    def get(self, key, default=None):
        """Tercih değerini getir"""
        keys = key.split('.')
        value = self.current
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key, value):
        """Tercih değerini ayarla"""
        keys = key.split('.')
        target = self.current
        
        # Son anahtara kadar ilerle
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        # Son anahtarı güncelle
        target[keys[-1]] = value
        return self.save()

    def _merge_with_defaults(self, prefs):
        """Yüklenen tercihleri varsayılanlarla birleştir"""
        result = self.defaults.copy()
        
        def merge_dict(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(target[key], value)
                else:
                    target[key] = value
        
        merge_dict(result, prefs)
        return result
