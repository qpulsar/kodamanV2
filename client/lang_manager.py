import json
import logging
import os
from typing import Dict, Any

logger = logging.getLogger('FileClient.LangManager')

class LangManager:
    def __init__(self, lang_dir: str):
        self.lang_dir = lang_dir
        self.current_lang = "tr"  # Default dil
        self.translations: Dict[str, Dict[str, Any]] = {}
        self._load_translations()

    def _load_translations(self):
        """Tüm dil dosyalarını yükle"""
        for lang_file in ["tr.json", "en.json"]:
            lang_code = lang_file.split('.')[0]
            file_path = os.path.join(self.lang_dir, lang_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                logger.info(f"{lang_code} dil dosyası yüklendi")
            except Exception as e:
                logger.error(f"{lang_code} dil dosyası yüklenemedi: {str(e)}")
                self.translations[lang_code] = {}

    def set_language(self, lang_code: str) -> bool:
        """Aktif dili değiştir"""
        if lang_code in self.translations:
            self.current_lang = lang_code
            logger.info(f"Dil değiştirildi: {lang_code}")
            return True
        logger.error(f"Geçersiz dil kodu: {lang_code}")
        return False

    def get_text(self, key: str, *args) -> str:
        """Belirtilen anahtara ait metni getir"""
        # Nokta notasyonunu kullanarak iç içe sözlüklerde gezin
        keys = key.split('.')
        value = self.translations.get(self.current_lang, {})
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, key)
            else:
                return key
                
        if isinstance(value, str):
            try:
                return value.format(*args)
            except:
                return value
        return key
