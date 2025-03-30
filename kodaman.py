import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QRadioButton, QPushButton, 
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QButtonGroup,
    QFrame, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
from languages import LANGUAGES

# Preferences için gerekli import
sys.path.append(os.path.join(os.path.dirname(__file__), 'client'))
from client.preferences import Preferences

# Logging ayarları
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('kodaman.log')
    ]
)
logger = logging.getLogger('Kodaman.Launcher')

STYLE_SHEET = """
QMainWindow {
    background-color: transparent;
}
QPushButton {
    background-color: #6B4EFF;
    color: white;
    border-radius: 20px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
    min-height: 40px;
}
QPushButton:hover {
    background-color: #5840CC;
}
QRadioButton {
    font-size: 14px;
    color: #333333;
    padding: 8px;
    border-radius: 10px;
    min-height: 30px;
}
QRadioButton::indicator {
    width: 20px;
    height: 20px;
}
QCheckBox {
    font-size: 12px;
    color: #666666;
    background-color: rgba(255, 255, 255, 180);
    border-radius: 8px;
    padding: 5px;
    min-height: 25px;
}
QLabel#title {
    color: #6B4EFF;
    font-size: 32px;
    font-weight: bold;
    background-color: rgba(255, 255, 255, 180);
    border-radius: 15px;
    padding: 10px;
    min-height: 50px;
}
QLabel#subtitle {
    color: #666666;
    font-size: 14px;
    background-color: rgba(255, 255, 255, 180);
    border-radius: 10px;
    padding: 8px;
    min-height: 35px;
}
QWidget#mainContainer {
    background-color: transparent;
}
QComboBox {
    background-color: rgba(255, 255, 255, 180);
    border: 1px solid #6B4EFF;
    border-radius: 10px;
    padding: 5px 10px;
    color: #333333;
    font-size: 12px;
    min-width: 60px;
    min-height: 25px;
}
QComboBox::drop-down {
    border: none;
    width: 15px;
}
QComboBox::down-arrow {
    width: 8px;
    height: 8px;
    background: #6B4EFF;
    border-radius: 4px;
}
QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #6B4EFF;
    selection-background-color: #6B4EFF;
    selection-color: white;
}
"""

class KodamanLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Ana widget oluştur
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(40, 20, 40, 40)
        main_layout.setSpacing(15)
        
        # Arka plan resmi için
        self.background = QLabel(self)
        background_pixmap = QPixmap('images/splash.png')
        self.background.setPixmap(background_pixmap.scaled(600, 400, Qt.KeepAspectRatioByExpanding))
        self.background.setGeometry(0, 0, 600, 400)
        self.background.lower()  # Arka planı en alta al
        
        # Dil seçimi için
        self.lang_combo = QComboBox(self)
        self.lang_combo.addItem("TR", "tr")
        self.lang_combo.addItem("EN", "en")
        self.lang_combo.setFixedWidth(60)
        self.lang_combo.move(520, 10)
        self.lang_combo.raise_()  # ComboBox'ı en üste al
        
        # Tercihler yöneticisini oluştur
        config_dir = os.path.dirname(__file__)
        self.preferences = Preferences(config_dir)
        
        # Dil tercihini kontrol et
        if self.preferences.get('language') is None:
            self.preferences.set('language', 'tr')
        
        self.current_language = self.preferences.get('language')
        self.texts = LANGUAGES[self.current_language]
        
        # Mevcut dili seç
        current_index = 0 if self.current_language == 'tr' else 1
        self.lang_combo.setCurrentIndex(current_index)
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        
        # Diğer tercihler
        if self.preferences.get('app.type') is None:
            self.preferences.set('app.type', 'client')
            
        if self.preferences.get('remember_choice') is None:
            self.preferences.set('remember_choice', False)
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.texts['window_title'])
        self.setFixedSize(600, 400)
        self.setStyleSheet(STYLE_SHEET)
        
        # Ana container
        content_widget = QWidget()
        content_widget.setObjectName("mainContainer")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel(self.texts['title'])
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        
        # Alt başlık
        subtitle_label = QLabel(self.texts['subtitle'])
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle_label)
        
        # Radio butonlar için container
        radio_container = QWidget()
        radio_layout = QVBoxLayout()
        radio_layout.setContentsMargins(100, 10, 100, 10)
        radio_layout.setSpacing(10)
        
        # Radio buton grubu
        self.button_group = QButtonGroup(self)
        
        # İstemci (Client) radio butonu
        self.client_radio = QRadioButton(self.texts['client'])
        self.button_group.addButton(self.client_radio, 1)
        radio_layout.addWidget(self.client_radio)
        
        # Sunucu (Server) radio butonu
        self.server_radio = QRadioButton(self.texts['server'])
        self.button_group.addButton(self.server_radio, 2)
        radio_layout.addWidget(self.server_radio)
        
        # Kayıtlı tercihe göre radio butonu seç
        app_type = self.preferences.get('app.type')
        if app_type == 'server':
            self.server_radio.setChecked(True)
        else:
            self.client_radio.setChecked(True)
        
        radio_container.setLayout(radio_layout)
        content_layout.addWidget(radio_container)
        
        # Seçimi hatırla checkbox'ı
        self.remember_choice = QCheckBox(self.texts['remember_choice'])
        self.remember_choice.setChecked(self.preferences.get('remember_choice'))
        content_layout.addWidget(self.remember_choice, alignment=Qt.AlignCenter)
        
        # Başlat butonu
        self.start_button = QPushButton(self.texts['start'])
        self.start_button.setFixedHeight(45)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.launch_application)
        content_layout.addWidget(self.start_button)
        
        # Boşluk ekle
        content_layout.addStretch(1)
        
        content_widget.setLayout(content_layout)
        self.centralWidget().layout().addWidget(content_widget)
        content_widget.raise_()  # İçerik widget'ını arka planın üzerine al
        
        logger.info("Kodaman Başlatıcı arayüzü hazırlandı")
    
    def change_language(self, index):
        # Yeni dili kaydet
        new_language = self.lang_combo.itemData(index)
        self.preferences.set('language', new_language)
        self.current_language = new_language
        self.texts = LANGUAGES[new_language]
        
        # Arayüz metinlerini güncelle
        self.setWindowTitle(self.texts['window_title'])
        self.findChild(QLabel, "title").setText(self.texts['title'])
        self.findChild(QLabel, "subtitle").setText(self.texts['subtitle'])
        self.client_radio.setText(self.texts['client'])
        self.server_radio.setText(self.texts['server'])
        self.remember_choice.setText(self.texts['remember_choice'])
        self.start_button.setText(self.texts['start'])
        
    def launch_application(self):
        # Seçilen modu kaydet
        if self.server_radio.isChecked():
            app_type = 'server'
            logger.info("Sunucu modu seçildi")
        else:
            app_type = 'client'
            logger.info("İstemci modu seçildi")
        
        # Seçimi hatırlama tercihini kaydet
        remember_choice = self.remember_choice.isChecked()
        self.preferences.set('remember_choice', remember_choice)
        
        # Eğer seçimi hatırla seçiliyse, uygulama tipini kaydet
        if remember_choice:
            self.preferences.set('app.type', app_type)
        
        # Uygulamayı kapat
        self.close()
        
        # Seçilen uygulamayı başlat
        if app_type == 'server':
            logger.info("Sunucu başlatılıyor...")
            server_path = os.path.join(os.path.dirname(__file__), 'server', 'kodaman_server.py')
            os.system(f'python "{server_path}"')
        else:
            logger.info("İstemci başlatılıyor...")
            client_path = os.path.join(os.path.dirname(__file__), 'client', 'kodaman_client.py')
            os.system(f'python "{client_path}"')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KodamanLauncher()
    window.show()
    sys.exit(app.exec_())
