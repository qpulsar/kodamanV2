import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QRadioButton, QPushButton, 
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QButtonGroup,
    QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

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

class KodamanLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Tercihler yöneticisini oluştur
        config_dir = os.path.dirname(__file__)
        self.preferences = Preferences(config_dir)
        
        # Uygulama tipini tercihlere ekle (eğer yoksa)
        if self.preferences.get('app.type') is None:
            self.preferences.set('app.type', 'client')
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Kodaman Başlatıcı")
        self.setFixedSize(400, 300)
        
        # Ana container
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("Kodaman")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Alt başlık
        subtitle_label = QLabel("Lütfen çalıştırmak istediğiniz modu seçin")
        subtitle_label.setFont(QFont("Arial", 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # Ayırıcı çizgi
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Radio butonlar için container
        radio_container = QWidget()
        radio_layout = QHBoxLayout()
        radio_layout.setContentsMargins(30, 10, 30, 10)
        radio_layout.setSpacing(20)
        
        # Radio buton grubu
        self.button_group = QButtonGroup(self)
        
        # İstemci (Client) radio butonu
        self.client_radio = QRadioButton("İstemci (Client)")
        self.client_radio.setFont(QFont("Arial", 12))
        self.button_group.addButton(self.client_radio, 1)
        radio_layout.addWidget(self.client_radio)
        
        # Sunucu (Server) radio butonu
        self.server_radio = QRadioButton("Sunucu (Server)")
        self.server_radio.setFont(QFont("Arial", 12))
        self.button_group.addButton(self.server_radio, 2)
        radio_layout.addWidget(self.server_radio)
        
        # Kayıtlı tercihe göre radio butonu seç
        app_type = self.preferences.get('app.type')
        if app_type == 'server':
            self.server_radio.setChecked(True)
        else:
            self.client_radio.setChecked(True)
        
        radio_container.setLayout(radio_layout)
        main_layout.addWidget(radio_container)
        
        # Başlat butonu
        self.start_button = QPushButton("Başlat")
        self.start_button.setFont(QFont("Arial", 14))
        self.start_button.setFixedHeight(50)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.launch_application)
        main_layout.addWidget(self.start_button)
        
        # Boşluk ekle
        main_layout.addStretch(1)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        logger.info("Kodaman Başlatıcı arayüzü hazırlandı")
    
    def launch_application(self):
        # Seçilen modu kaydet
        if self.server_radio.isChecked():
            app_type = 'server'
            logger.info("Sunucu modu seçildi")
        else:
            app_type = 'client'
            logger.info("İstemci modu seçildi")
        
        # Tercihlere kaydet
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
