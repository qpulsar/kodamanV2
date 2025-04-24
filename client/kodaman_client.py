import sys
import logging
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QTextEdit, QVBoxLayout, QWidget, \
    QMessageBox, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFrame, QSplitter, QStyle, QDialog, QListWidget, \
    QListWidgetItem, QDialogButtonBox, QGridLayout, QInputDialog, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor
from qt_material import apply_stylesheet, QtStyleTools, list_themes
from client import ClientConnection
from css_highlighter import CssHighlighter
from js_highlighter import JsHighlighter
from html_higlighter import HtmlHighlighter
from python_highlighter import PythonHighlighter
from lang_manager import LangManager
from preferences import Preferences

# Logging ayarları
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gui.log')
    ]
)
logger = logging.getLogger('FileClient.GUI')

class ReceiverThread(QThread):
    message_received = pyqtSignal(dict)
    connection_lost = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.running = True

    def run(self):
        for msg in self.client.receive_messages():
            if not self.running:
                break
                
            if msg.get("type") == "connection_lost":
                # Bağlantı koptu
                logger.warning("Bağlantı koptu")
                self.connection_lost.emit()
                break
            elif msg.get("type") == "error":
                # Hata mesajı
                error_message = msg.get("message", "Bilinmeyen hata")
                logger.error(f"Hata: {error_message}")
                self.error_occurred.emit(error_message)
            else:
                # Normal mesaj
                self.message_received.emit(msg)

    def stop(self):
        self.running = False
        self.quit()
        #self.wait()


class NavBar(QWidget):
    # Sinyaller
    connection_status_changed = pyqtSignal(str)
    connection_successful = pyqtSignal()
    language_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_gui = None  # Ana GUI referansı
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(10)
        self.setLayout(self.layout)
        
        # IP adresi girişi
        ip_container = QWidget()
        ip_layout = QHBoxLayout(ip_container)
        ip_layout.setContentsMargins(0, 0, 0, 0)
        ip_layout.setSpacing(5)
        
        ip_label = QLabel("IP:")
        ip_label.setFont(QFont("Arial", 9))
        ip_layout.addWidget(ip_label)
        
        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("connection.placeholders.ip")  # Will be translated
        self.ip_input.setToolTip("connection.tooltips.ip")  # Will be translated
        ip_layout.addWidget(self.ip_input)
        
        self.layout.addWidget(ip_container)
        
        # Port girişi
        port_container = QWidget()
        port_layout = QHBoxLayout(port_container)
        port_layout.setContentsMargins(0, 0, 0, 0)
        port_layout.setSpacing(5)
        
        port_label = QLabel("Port:")
        port_label.setFont(QFont("Arial", 9))
        port_layout.addWidget(port_label)
        
        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText("connection.placeholders.port")  # Will be translated
        self.port_input.setToolTip("connection.tooltips.port")  # Will be translated
        port_layout.addWidget(self.port_input)
        
        self.layout.addWidget(port_container)
        
        # Kullanıcı adı girişi
        user_container = QWidget()
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(5)
        user_label = QLabel("Name:")
        user_layout.addWidget(user_label)
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Kullanıcı adı")
        user_layout.addWidget(self.name_input)
        self.layout.addWidget(user_container)
        
        # Ayırıcı çizgi
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(separator)
        
        # Bağlan butonu
        self.connect_button = QPushButton("connection.connect", self)  # Will be translated
        self.connect_button.setCursor(Qt.PointingHandCursor)
        self.connect_button.setToolTip("connection.tooltips.connect")  # Will be translated
        self.connect_button.clicked.connect(self.toggle_connection)
        self.layout.addWidget(self.connect_button)
        
        # Durum göstergesi
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)
        
        self.status_label = QLabel(self)
        self.status_label.setFixedSize(16, 16)
        self.status_label.setToolTip("connection.status.disconnected")  # Will be translated
        status_layout.addWidget(self.status_label)
        
        self.status_text = QLabel("connection.status.disconnected", self)  # Will be translated
        self.status_text.setFont(QFont("Arial", 9))
        status_layout.addWidget(self.status_text)
        
        self.layout.addWidget(status_container)
        
        # Sağa doğru boşluk ekle
        self.layout.addStretch(1)
        
        # Dil seçim ComboBox'ı
        self.lang_combo = QComboBox(self)
        self.lang_combo.setToolTip("ui.language")  # Will be translated
        self.lang_combo.setFixedWidth(100)
        # ComboBox öğelerinin yüksekliğini azalt
        self.lang_combo.setStyleSheet("""
            QComboBox {
                padding: 2px 4px;
            }
            QComboBox::drop-down {
                border: none;
                padding: 0px;
            }
            QComboBox QAbstractItemView {
                padding: 0px;
                show-decoration-selected: 1;
                outline: none;
                font-size: 12pt;
            }
            QComboBox QAbstractItemView::item {
                padding: 2px;
                min-height: 18px;
            }
        """)
        
        # Dilleri ekle
        self.lang_combo.addItem("Türkçe", "tr")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        
        self.layout.addWidget(self.lang_combo)
        
        # Tema seçim ComboBox'ı
        self.theme_combo = QComboBox(self)
        self.theme_combo.setToolTip("ui.theme")  # Will be translated
        self.theme_combo.setFixedWidth(100)
        
        # ComboBox öğelerinin yüksekliğini azalt
        self.theme_combo.setStyleSheet("""
            QComboBox {
                padding: 2px 4px;
            }
            QComboBox::drop-down {
                border: none;
                padding: 0px;
            }
            QComboBox QAbstractItemView {
                padding: 0px;
                show-decoration-selected: 1;
                outline: none;
                font-size: 12pt;
            }
            QComboBox QAbstractItemView::item {
                padding: 2px;
                min-height: 18px;
            }
        """)

        # Temaları ekle
        all_themes = list_themes()
        dark_themes = [theme for theme in all_themes if theme.startswith('dark_')]
        light_themes = [theme for theme in all_themes if theme.startswith('light_')]
        
        # Tema isimlerini düzenle
        for theme in dark_themes:
            name = theme.replace('dark_', '').replace('.xml', '').capitalize()
            self.theme_combo.addItem(f"Koyu {name}", theme)
            
        for theme in light_themes:
            name = theme.replace('light_', '').replace('.xml', '').replace('_500', '').capitalize()
            self.theme_combo.addItem(f"Açık {name}", theme)
            
        self.theme_combo.currentIndexChanged.connect(self._on_theme_selected)
        self.layout.addWidget(self.theme_combo)
        
        # Tema değiştirme butonu
        self.theme_button = QPushButton(self)
        self.theme_button.setToolTip("ui.theme_change")  # Will be translated
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.setFixedSize(30, 30)
        self.layout.addWidget(self.theme_button)
        
        # Font boyutu ayar butonları
        font_size_container = QWidget()
        font_size_layout = QHBoxLayout()
        font_size_layout.setContentsMargins(0, 0, 0, 0)
        font_size_layout.setSpacing(5)
        
        decrease_font = QPushButton("-")
        decrease_font.setFixedSize(32, 32)
        decrease_font.clicked.connect(self.decrease_font_size)
        font_size_layout.addWidget(decrease_font)
        
        increase_font = QPushButton("+")
        increase_font.setFixedSize(32, 32)
        increase_font.clicked.connect(self.increase_font_size)
        font_size_layout.addWidget(increase_font)
        
        font_size_container.setLayout(font_size_layout)
        self.layout.addWidget(font_size_container)
        
        self.setMaximumHeight(50)
        self.setMinimumHeight(50)
        
        # Client ve bağlantı durumu
        self.client = None
        self.connection_status = "disconnected"
        self.receiver_thread = None
        
        # Başlangıç durumunu ayarla
        self.set_status("disconnected")
    
    def set_client(self, client):
        """Client nesnesini ayarla"""
        self.client = client
        
    def set_main_gui(self, main_gui):
        """Ana GUI referansını ayarla"""
        self.main_gui = main_gui
        
    def toggle_connection(self):
        """Bağlantı durumunu değiştir"""
        if not self.client:
            QMessageBox.warning(self, "Hata", "Client nesnesi tanımlanmamış!")
            return
            
        if self.connection_status == "connected":
            # Bağlantıyı kes
            try:
                self.client.close()
                self.set_status("disconnected")
            except Exception as e:
                logger.error(f"Bağlantı kesme hatası: {str(e)}")
                QMessageBox.critical(self, "Bağlantı Kesme Hatası", str(e))
        else:
            # Bağlan
            try:
                self.set_status("connecting")
                
                # IP, port ve kullanıcı adını al
                host = self.ip_input.text().strip()
                port = int(self.port_input.text().strip())
                username = self.name_input.text().strip()
                # Tercihleri kaydet
                if self.main_gui:
                    self.main_gui.preferences.set('connection.ip', host)
                    self.main_gui.preferences.set('connection.port', port)
                    self.main_gui.preferences.set('connection.username', username)
                
                # Client'ı günculle
                self.client.host = host
                self.client.port = port
                
                # Bağlantıyı kur
                self.client.connect()
                self.set_status("connected")
                
                # Gönder login mesaj
                # Kullanıcı adını kullanarak login mesajı gönder
                if username:
                    from shared import protocol
                    self.client.send(protocol.make_login_message(username))
                
                # Bağlantı başarılı sinyali gönder
                self.connection_successful.emit()
                
                # Receiver thread'i başlat
                if self.receiver_thread:
                    self.receiver_thread.stop()
                
                self.receiver_thread = ReceiverThread(self.client)
                # Ana GUI'ye bağlan
                if self.main_gui:
                    self.receiver_thread.message_received.connect(self.main_gui.handle_message)
                    self.receiver_thread.connection_lost.connect(self.main_gui.handle_connection_lost)
                    self.receiver_thread.error_occurred.connect(self.main_gui.handle_error)
                
                self.receiver_thread.start()
                
            except Exception as e:
                logger.error(f"Bağlantı hatası: {str(e)}")
                self.set_status("disconnected")
                QMessageBox.critical(self, "Bağlantı Hatası", str(e))
    
    def set_status(self, status):
        """Bağlantı durumunu ayarla ve görsel olarak güncelle"""
        self.connection_status = status
        
        # Durum metni ve rengi
        if status == "connected":
            status_text = "Bağlı" if not self.main_gui else self.main_gui.lang_manager.get_text("connection.status.connected")
            button_text = "Bağlantıyı Kes" if not self.main_gui else self.main_gui.lang_manager.get_text("connection.disconnect")
            self.status_text.setText(status_text)
            self.status_label.setStyleSheet("background-color: #4CAF50; border-radius: 8px;")
            self.connect_button.setText(button_text)
        elif status == "connecting":
            status_text = "Bağlanıyor..." if not self.main_gui else self.main_gui.lang_manager.get_text("connection.status.connecting")
            button_text = "İptal" if not self.main_gui else self.main_gui.lang_manager.get_text("connection.cancel")
            self.status_text.setText(status_text)
            self.status_label.setStyleSheet("background-color: #FFC107; border-radius: 8px;")
            self.connect_button.setText(button_text)
        else:  # disconnected
            status_text = "Bağlantı Yok" if not self.main_gui else self.main_gui.lang_manager.get_text("connection.status.disconnected")
            button_text = "Bağlan" if not self.main_gui else self.main_gui.lang_manager.get_text("connection.connect")
            self.status_text.setText(status_text)
            self.status_label.setStyleSheet("background-color: #F44336; border-radius: 8px;")
            self.connect_button.setText(button_text)
        
        # Durum değişikliği sinyali gönder
        self.connection_status_changed.emit(status)

    def _on_language_changed(self, index):
        """Dil değiştiğinde çağrılır"""
        lang_code = self.lang_combo.itemData(index)
        if self.main_gui and self.main_gui.lang_manager.set_language(lang_code):
            # Tercihleri günculle
            self.main_gui.preferences.set('ui.language', lang_code)
            self.language_changed.emit(lang_code)
            self.update_texts()  # Metinleri güncelle

    def _on_theme_selected(self, index):
        """
        Tema seçildiğinde çağrılır ve kullanıcı tercihi olarak kaydedilir.
        """
        theme = self.theme_combo.itemData(index)
        if self.main_gui:
            self.main_gui.current_theme = theme
            # Tercihleri güncelle
            self.main_gui.preferences.set('ui.theme', theme)
            self.theme_changed.emit(theme)

    def load_preferences(self):
        """Kullanıcı tercihlerini yükle"""
        if not self.main_gui:
            return
            
        prefs = self.main_gui.preferences
        
        # IP, port ve kullanıcı adı
        self.ip_input.setText(prefs.get('connection.ip'))
        self.port_input.setText(str(prefs.get('connection.port')))
        self.name_input.setText(prefs.get('connection.username', ''))
        
        # Dil
        lang = prefs.get('ui.language')
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == lang:
                self.lang_combo.setCurrentIndex(i)
                break
        # Tema
        theme = prefs.get('ui.theme')
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme:
                self.theme_combo.setCurrentIndex(i)
                break

    def update_texts(self):
        """Tüm metinleri güncelle"""
        if not self.main_gui:
            return
            
        lm = self.main_gui.lang_manager
        
        # Placeholder ve tooltip metinlerini güncelle
        self.ip_input.setPlaceholderText(lm.get_text("connection.placeholders.ip"))
        self.ip_input.setToolTip(lm.get_text("connection.tooltips.ip"))
        
        self.port_input.setPlaceholderText(lm.get_text("connection.placeholders.port"))
        self.port_input.setToolTip(lm.get_text("connection.tooltips.port"))
        
        # ComboBox tooltiplerini güncelle
        self.lang_combo.setToolTip(lm.get_text("ui.language"))
        self.theme_combo.setToolTip(lm.get_text("ui.theme"))
        
        # Bağlantı durumunu güncelle (buton ve durum metni)
        self.set_status(self.connection_status)

    def increase_font_size(self):
        """Font boyutunu artır"""
        if self.main_gui:
            font_size = self.main_gui.preferences.get('font.size', 12)
            if font_size < 24:  # Maksimum boyut
                font_size += 2
                self.main_gui.font_size = font_size  # font_size değişkenini güncelle
                self.main_gui.preferences.set('font.size', font_size)
                self.main_gui.update_font_size()

    def decrease_font_size(self):
        """Font boyutunu azalt"""
        if self.main_gui:
            font_size = self.main_gui.preferences.get('font.size', 12)
            if font_size > 8:  # Minimum boyut
                font_size -= 2
                self.main_gui.font_size = font_size  # font_size değişkenini güncelle
                self.main_gui.preferences.set('font.size', font_size)
                self.main_gui.update_font_size()


class FileBrowserGUI(QMainWindow, QtStyleTools):
    def __init__(self):
        super().__init__()
        
        # Tercihler yöneticisini oluştur
        config_dir = os.path.dirname(__file__)
        self.preferences = Preferences(config_dir)
        
        # Dil yöneticisini oluştur
        lang_dir = os.path.join(os.path.dirname(__file__), "lang")
        self.lang_manager = LangManager(lang_dir)
        
        self.setWindowTitle("Öğretmen Sunucusu Dosya Görüntüleyici")  # Geçici başlık
        self.resize(1000, 600)
        
        # Tema değişkeni
        self.current_theme = self.preferences.get('ui.theme')
        
        self.navbar = NavBar(self)
        # Navbar sinyallerini bağla
        self.navbar.connection_successful.connect(self.on_connection_successful)
        self.navbar.connection_status_changed.connect(self.on_connection_status_changed)
        self.navbar.language_changed.connect(self._on_language_changed)
        self.navbar.theme_changed.connect(self._on_theme_changed)
        self.navbar.set_main_gui(self)
        
        # Tema butonunu bağla
        self.navbar.theme_button.clicked.connect(self.toggle_theme)
        
        # Splitter oluştur
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Dosya ağacı
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Dosyalar")  # Geçici başlık
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.setFixedWidth(200)
        

        
        # Tree refresh butonu
        # Tree refresh butonu, yenileme simgesi ile
        self.tree_refresh_button = QPushButton()
        self.tree_refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.tree_refresh_button.setFixedSize(30, 30)
        self.tree_refresh_button.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.tree_refresh_button.clicked.connect(self._on_tree_refresh_clicked)
        
        # Tree refresh butonunu konumlandır
        tree_button_layout = QHBoxLayout(self.tree)
        tree_button_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        tree_button_layout.setContentsMargins(0, 5, 5, 0)
        tree_button_layout.addWidget(self.tree_refresh_button)
        
        # Dosya ağacı ve layout stilini temaya göre uygula
        self.apply_tree_theme()

        
        self.splitter.addWidget(self.tree)

        # Metin alanı
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.highlighter = PythonHighlighter(self.text_area.document())
        # Seçim değişince timer başlat, seçim bitince panoya kopyala ve log paneline yaz
        self.text_area.selectionChanged.connect(self.on_text_area_selection_changed)
        self._selection_copy_timer = QTimer(self)
        self._selection_copy_timer.setSingleShot(True)
        self._selection_copy_timer.timeout.connect(self.copy_selection_if_still_selected)
        
        # Refresh butonu
        # İçerik alanı refresh butonu, yenileme simgesi ile
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_button.setFixedSize(30, 30)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                background-color: #2196F3;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        
        # Refresh butonunu konumlandır
        button_layout = QHBoxLayout(self.text_area)
        button_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        button_layout.setContentsMargins(0, 5, 5, 0)
        button_layout.addWidget(self.refresh_button)
        
        self.splitter.addWidget(self.text_area)
        
        # Log alanı
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        
        # Font boyutu tercihi
        if self.preferences.get('font.size') is None:
            self.preferences.set('font.size', 12)  # Varsayılan font boyutu
        
        self.font_size = self.preferences.get('font.size')
        
        # Ana layout
        layout = QVBoxLayout()
        layout.addWidget(self.navbar)
        layout.addWidget(self.splitter, 1)  # 1 = stretch factor
        layout.addWidget(self.log_area)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Client bağlantısını oluştur
        self.client = ClientConnection()
        self.navbar.set_client(self.client)
        
        # Tercihleri yükle
        self.navbar.load_preferences()
        
        # GUI oluşturulduktan sonra dili ayarla
        self.lang_manager.set_language(self.preferences.get('ui.language'))
        self._update_all_texts()
        
        # Font boyutunu uygula
        self.update_font_size()
        
        # Log mesajı
        self.log_message("Uygulama başlatıldı", "info")
        logger.info("FileBrowserGUI başlatıldı")

        # Dakikada bir otomatik güncelleme başlat
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        self.auto_refresh_timer.start(60000)  # 60 saniye

    def auto_refresh(self):
        """Klasör ve açık dosya içeriğini ve kullanıcı listesini otomatik günceller. Seçili dosya ve scroll korunur."""
        # Seçili dosya path'i (varsa)
        selected_item = self.tree.currentItem()
        selected_path = None
        if selected_item:
            selected_path = selected_item.data(0, Qt.UserRole)
        # TextArea scroll pozisyonu
        scroll_bar = self.text_area.verticalScrollBar()
        scroll_value = scroll_bar.value()
        # Dosya ağacını güncelle
        self.update_tree_structure()
        # Dosya seçiliyse tekrar seç
        if selected_path:
            self.select_tree_item_by_path(selected_path)
            # Seçili dosya açıksa içeriğini tekrar iste
            self.client.request_file(selected_path)
        # Scroll pozisyonunu geri yükle
        QTimer.singleShot(200, lambda: scroll_bar.setValue(scroll_value))
        # Kullanıcı listesini güncelle (sadece bağlantı varsa)
        if self.navbar.connection_status == "connected":
            self.client.request_users()

    def select_tree_item_by_path(self, path):
        """Verilen path'e sahip öğeyi seçer."""
        def recursive_search(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.data(0, Qt.UserRole) == path:
                    self.tree.setCurrentItem(child)
                    return True
                if recursive_search(child):
                    return True
            return False
        root = self.tree.topLevelItem(0)
        if root:
            recursive_search(root)


    def apply_highlighter(self, path, text_edit):
        ext = path.lower().split('.')[-1]

        # Önce eski renklendiriciyi sil
        if hasattr(text_edit, 'highlighter') and text_edit.highlighter is not None:
            text_edit.highlighter.setDocument(None)

        if ext == 'py':
            text_edit.highlighter = PythonHighlighter(text_edit.document())
        elif ext == 'html' or ext == 'htm':
            text_edit.highlighter = HtmlHighlighter(text_edit.document())
        elif ext == 'js':
            text_edit.highlighter = JsHighlighter(text_edit.document())
        elif ext == 'css':
            text_edit.highlighter = CssHighlighter(text_edit.document())
        else:
            text_edit.highlighter = None  # Renklendirme yapılmaz

    def on_text_area_selection_changed(self):
        """Text area'da seçim değişince timer başlat"""
        self._selection_copy_timer.start(400)

    def copy_selection_if_still_selected(self):
        """Seçim hâlâ varsa panoya kopyala ve log paneline yaz"""
        cursor = self.text_area.textCursor()
        selected_text = cursor.selectedText()
        if selected_text:
            QApplication.clipboard().setText(selected_text)
            self.log_message("Seçim kopyalandı", "success")


    def log_message(self, message, level="info"):
        """Log mesajı ekle"""
        # Tema kontrolü
        is_dark_theme = self.current_theme.startswith('dark_')
        
        # Koyu tema için açık renkler, açık tema için koyu renkler
        if is_dark_theme:
            colors = {
                "error": QColor("#FF6B6B"),    # Açık kırmızı
                "warning": QColor("#FFB86C"),   # Açık turuncu
                "success": QColor("#50FA7B"),   # Açık yeşil
                "info": QColor("#F8F8F2")      # Açık gri
            }
        else:
            colors = {
                "error": QColor("#DC143C"),     # Koyu kırmızı
                "warning": QColor("#FF8C00"),   # Koyu turuncu
                "success": QColor("#228B22"),   # Koyu yeşil
                "info": QColor("#2F4F4F")       # Koyu gri
            }
        
        # Mesaj seviyesine göre renk ve prefix seç
        color = colors.get(level, colors["info"])
        prefix = self.lang_manager.get_text(f"log_levels.{level}")
            
        # Mesajı log alanına ekle
        self.log_area.setTextColor(color)
        self.log_area.append(f"[{prefix}] {message}")
        
        # Otomatik kaydır
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

    def handle_message(self, msg):
        """Sunucudan gelen mesajları işle. Kullanıcı listesi güncellemesini de destekler."""
        logger.debug(f"Mesaj alındı: {str(msg)[:200]}...")
        
        if msg.get("response") == "tree":
            # Dosya ağacı yanıtı
            tree_data = msg.get("data", {})
            logger.info("Dosya ağacı alındı, ağaç oluşturuluyor")
            self.populate_tree(tree_data)
            self.log_message("Dosya ağacı güncellendi", "success")
            
        elif msg.get("response") == "file":
            # Dosya içeriği yanıtı
            path = msg.get("path", "")
            content = msg.get("content", "")
            
            # Dosya içeriğini göster
            self.text_area.setPlainText(content)
            self.log_message(f"Dosya yüklendi: {path}", "success")
            logger.info(f"Dosya içeriği gösterildi: {path} ({len(content)} karakter)")
            
        elif msg.get("response") == "users":
            # Kullanıcı listesi yanıtı
            users = msg.get("users", [])
            logger.info(f"Kullanıcı listesi güncellendi: {users}")
            
        elif msg.get("response") == "error":
            # Hata yanıtı
            error_msg = msg.get("error", "Bilinmeyen hata")
            self.handle_error(error_msg)


    def handle_error(self, error_message):
        """Hata mesajlarını işle"""
        logger.error(f"Sunucu hatası: {error_message}")
        
        # Hata mesajını göster
        self.log_message(f"Sunucu hatası: {error_message}", "error")
        
        # Eğer güvenlik hatası ise özel uyarı göster
        if "Yetkisiz erişim" in error_message or "güvenlik" in error_message.lower():
            QMessageBox.warning(self, "Güvenlik Uyarısı", 
                               f"Güvenlik ihlali tespit edildi:\n{error_message}\n\nBu olay kaydedildi.")

    # Sunucu bağlantısı koptuğunda çağrılır
    def handle_connection_lost(self):
        self.navbar.set_status("disconnected")
        self.log_message("Sunucu bağlantısı kesildi", "warning")
        logger.warning("Sunucu bağlantısı kesildi")
        QMessageBox.warning(self, "Bağlantı Kesildi", "Sunucu bağlantısı kesildi.")

    def populate_tree(self, tree_data, parent=None, path_prefix=""):
        """Dosya ağacını doldur"""
        logger.debug(f"Ağaç doldurma başladı: {str(tree_data)[:100]}...")
        
        if parent is None:
            # Kök düğümü temizle
            self.tree.clear()
            parent = self.tree
            
            # Kök klasör öğesi oluştur
            root_item = QTreeWidgetItem(parent)
            root_item.setText(0, "Kök Dizin")
            root_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
            parent = root_item
            logger.debug("Kök dizin öğesi oluşturuldu")
            
            # Kök dizindeki dosyaları ekle
            if "files" in tree_data and isinstance(tree_data["files"], list):
                logger.debug(f"Kök dizin dosya listesi: {tree_data['files']}")
                for file_name in sorted(tree_data["files"]):
                    file_item = QTreeWidgetItem(parent)
                    file_item.setText(0, file_name)
                    file_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
                    #logger.debug(f"Dosya eklendi: {file_name}")
                    
                    # Dosya yolunu sakla
                    file_path = file_name
                    file_item.setData(0, Qt.UserRole, file_path)
                    #logger.debug(f"Dosya yolu ayarlandı: {file_path}")
            
            # Alt klasörleri işle
            if "children" in tree_data and isinstance(tree_data["children"], dict):
                for dir_name, dir_data in tree_data["children"].items():
                    dir_item = QTreeWidgetItem(parent)
                    dir_item.setText(0, dir_name)
                    dir_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
                    #logger.debug(f"Klasör eklendi: {dir_name}")
                    
                    # Alt klasörleri ekle (recursive)
                    self.populate_tree(dir_data, dir_item, dir_name)
        else:
            # Alt klasörlerdeki dosyaları ekle
            if "files" in tree_data and isinstance(tree_data["files"], list):
                logger.debug(f"Klasör dosya listesi: {tree_data['files']}")
                for file_name in sorted(tree_data["files"]):
                    file_item = QTreeWidgetItem(parent)
                    file_item.setText(0, file_name)
                    file_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
                    #logger.debug(f"Dosya eklendi: {file_name}")
                    
                    # Dosya yolunu sakla
                    file_path = f"{path_prefix}/{file_name}"
                    file_item.setData(0, Qt.UserRole, file_path)
                    #logger.debug(f"Dosya yolu ayarlandı: {file_path}")
            
            # Alt klasörleri işle
            if "children" in tree_data and isinstance(tree_data["children"], dict):
                for dir_name, dir_data in tree_data["children"].items():
                    dir_item = QTreeWidgetItem(parent)
                    dir_item.setText(0, dir_name)
                    dir_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
                    #logger.debug(f"Klasör eklendi: {dir_name}")
                    
                    # Alt klasörleri ekle (recursive)
                    new_path_prefix = f"{path_prefix}/{dir_name}" if path_prefix else dir_name
                    self.populate_tree(dir_data, dir_item, new_path_prefix)
        
        # Ağacı genişlet
        self.tree.expandItem(self.tree.topLevelItem(0))
        #logger.debug("Ağaç genişletildi")

    def on_item_clicked(self, item, column):
        """Ağaç öğesi tıklandığında çağrılır"""
        # Dosya yolunu al
        file_path = item.data(0, Qt.UserRole)
        
        # Eğer dosya yolu varsa (klasör değil dosya ise)
        if file_path:
            try:
                # Dosya içeriğini iste
                logger.info(f"Dosya tıklandı: {file_path}")
                if self.client.request_file(file_path):
                    self.log_message(f"Dosya isteniyor: {file_path}", "info")
                else:
                    self.log_message(f"Dosya istenemedi: {file_path}", "error")
            except Exception as e:
                self.log_message(f"Dosya isteme hatası: {str(e)}", "error")
                logger.error(f"Dosya isteme hatası: {str(e)}")
            self.apply_highlighter(file_path, self.text_area)

    # Bağlantı başarılı olduğunda dosya ağacını iste
    def on_connection_successful(self):
        try:
            logger.info("Bağlantı başarılı, dosya ağacı isteniyor")
            self.client.request_tree()
            self.log_message("Dosya ağacı isteniyor...", "info")
        except Exception as e:
            self.log_message(f"Dosya ağacı isteme hatası: {str(e)}", "error")
            logger.error(f"Dosya ağacı isteme hatası: {str(e)}")

    # Bağlantı durumu değiştiğinde UI'ı güncelle
    def on_connection_status_changed(self, status):
        if status == "connected":
            self.log_message("Sunucuya bağlandı", "success")
        elif status == "disconnected":
            self.log_message("Sunucu bağlantısı kesildi", "warning")
            self.tree.clear()
            self.text_area.clear()
        elif status == "connecting":
            self.log_message("Sunucuya bağlanıyor...", "info")
        elif status == "error":
            self.log_message("Bağlantı hatası", "error")

    def resizeEvent(self, event):
        """Pencere yeniden boyutlandırıldığında çağrılır"""
        super().resizeEvent(event)

    def select_current_theme_in_combo(self):
        """ComboBox'ta mevcut temayı seç"""
        combo = self.navbar.theme_combo
        for i in range(combo.count()):
            if combo.itemData(i) == self.current_theme:
                combo.setCurrentIndex(i)
                break

    def on_theme_selected(self, index):
        """Tema seçildiğinde çağrılır"""
        if index < 0:
            return
            
        # Seçilen temayı al
        selected_theme = self.navbar.theme_combo.itemData(index)
        if selected_theme == self.current_theme:
            return
            
        # Temayı günculle
        self.current_theme = selected_theme
        
        # Tema türünü belirle (açık/koyu)
        is_dark = self.current_theme.startswith('dark_')
        
        # Temayı uygula
        self.apply_stylesheet(QApplication.instance(), theme=self.current_theme, invert_secondary=is_dark, extra={
            'density_scale': '0',
            'font_family': 'Roboto',
            'font_size': '12px',
        })
        
        # Koyu tema için ek ayarlar
        if is_dark:
            extra = {
                'primaryColor': '#009688',
                'primaryLightColor': '#52c7b8',
                'secondaryColor': '#232629',
                'secondaryLightColor': '#4f5b62',
                'secondaryDarkColor': '#31363b',
                'primaryTextColor': '#ffffff',
                'secondaryTextColor': '#ffffff',
            }
            self.apply_stylesheet(QApplication.instance(),selected_theme, extra)

        # Tema değişikliği sonrası dosya ağacı ve layout stilini güncelle
        self.apply_tree_theme()
        self.update_theme_button_icon()
        self.log_message(f"Tema değiştirildi: {self.current_theme}", "info")

    def toggle_theme(self):
        """Temayı değiştir (açık/koyu arası geçiş)"""
        # Mevcut temanın açık/koyu durumunu kontrol et
        is_dark = self.current_theme.startswith('dark_')
        
        # Renk adını al (teal, amber, blue vb.)
        color_name = self.current_theme.replace('dark_', '').replace('light_', '').replace('_500', '').replace('.xml', '')
        
        # Yeni tema adını oluştur
        new_theme = f"{'light' if is_dark else 'dark'}_{color_name}.xml"
        
        # ComboBox'ta yeni temayı bul ve seç
        combo = self.navbar.theme_combo
        for i in range(combo.count()):
            if combo.itemData(i) == new_theme:
                combo.setCurrentIndex(i)
                break
    
    def update_theme_button_icon(self):
        """Tema butonunun ikonunu güncelle"""
        is_dark = self.current_theme.startswith('dark_')
        if is_dark:
            # Koyu tema aktif, güneş ikonu göster (açık temaya geçiş için)
            self.navbar.theme_button.setText("☀️")
            self.navbar.theme_button.setToolTip("ui.theme_change_light")  # Will be translated
        else:
            # Açık tema aktif, ay ikonu göster (koyu temaya geçiş için)
            self.navbar.theme_button.setText("🌙")
            self.navbar.theme_button.setToolTip("ui.theme_change_dark")  # Will be translated

    def _update_all_texts(self):
        """Tüm metinleri güncelle"""
        # Pencere başlığını güncelle
        self.setWindowTitle(self.lang_manager.get_text("window_title"))
        
        # Dosya ağacı başlığını güncelle
        self.tree.setHeaderLabel(self.lang_manager.get_text("tree.header"))
        
        # Navbar metinlerini güncelle
        self.navbar.update_texts()

    def _on_language_changed(self, lang_code):
        """Dil değiştiğinde çağrılır"""
        # Pencere başlığını güncelle
        self.setWindowTitle(self.lang_manager.get_text("window_title"))
        
        # Dosya ağacı başlığını güncelle
        self.tree.setHeaderLabel(self.lang_manager.get_text("tree.header"))

    def _on_theme_changed(self, theme):
        """Tema değiştiğinde çağrılır"""
        self.current_theme = theme
        self.apply_stylesheet(QApplication.instance(), theme=theme, invert_secondary=True, extra={
            'density_scale': '-1',
        })
        self.apply_tree_theme()
        self.update_theme_button_icon()
        # Log mesajı
        #self.log_message(f"Tema değiştirildi: {theme}", "info")


    def _on_refresh_clicked(self):
        """Refresh butonuna tıklandığında çağrılır"""
        if self.tree.currentItem():
            self.on_item_clicked(self.tree.currentItem(), 0)

    def _on_tree_refresh_clicked(self):
        """Tree refresh butonuna tıklandığında çağrılır"""
        self.update_tree_structure()

    def update_tree_structure(self):
        try:
            logger.info("Dosya ağacı güncelleniyor...")
            self.client.request_tree()
            self.log_message("Dosya ağacı güncelleniyor...", "info")
        except Exception as e:
            self.log_message(f"Dosya ağacı güncelleme hatası: {str(e)}", "error")
            logger.error(f"Dosya ağacı güncelleme hatası: {str(e)}")

    def update_font_size(self):
        """Font boyutunu güncelle ve kaydet"""
        # TextArea için font boyutu
        font = self.text_area.font()
        font.setPointSize(self.font_size)
        self.text_area.setFont(font)

    def apply_tree_theme(self):
        """
        QTreeWidget ve bulunduğu layout'un stilini temaya göre uygular.
        """
        is_dark = self.current_theme.startswith('dark_')
        if is_dark:
            bg = '#232629'
            border = '#666666'  # Daha belirgin koyu gri
            fg = '#fff'
            sel_bg = '#37474f'
            sel_fg = '#fff'
        else:
            bg = '#f8f8f8'
            border = '#cccccc'  # Açık gri
            fg = '#222'
            sel_bg = '#d0eaff'
            sel_fg = '#222'
        self.tree.setStyleSheet(f'''
            QTreeWidget {{
                background-color: {bg};
                border: 1.5px solid {border};
                font-size: 14px;
                color: {fg};
                selection-background-color: {sel_bg};
                selection-color: {sel_fg};
            }}
            QTreeWidget::item {{
                padding: 4px;
                min-height: 22px;
            }}
            QTreeWidget::branch {{
                padding: 1px;
            }}
        ''')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileBrowserGUI()
    window.apply_stylesheet(app, theme=window.current_theme, invert_secondary=True, extra={
        'density_scale': '-1',
    })
    window.show()
    sys.exit(app.exec_())