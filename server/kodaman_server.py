import sys
import threading
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget,
    QLabel, QLineEdit, QListWidget, QHBoxLayout, QMessageBox, QComboBox, QTabWidget
)

from . import server
from .settings_manager import SettingsManager


class ServerControlWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📡 Sunucu Kontrol Paneli")
        self.setFixedSize(600, 500)

        # Ayarlar yöneticisini başlat
        self.settings_manager = SettingsManager()

        # Sunucu bilgileri - ayarlardan yükle
        self.base_dir = self.settings_manager.get_setting("base_dir", "")
        self.allowed_extensions = self.settings_manager.get_setting("allowed_extensions", [])
        self.excluded_directories = self.settings_manager.get_setting("excluded_directories", [
            '__pycache__', 'venv', '.venv', 'env', '.env', '.git', '.idea', '.vscode',
            'node_modules', 'dist', 'build', '.pytest_cache', '.ipynb_checkpoints'
        ])
        self.excluded_extensions = self.settings_manager.get_setting("excluded_extensions", [
            '.pyc', '.pyo', '.so', '.dll', '.exe', '.bin', '.dat', '.db', '.sqlite', '.sqlite3'
        ])

        # Sunucu host ve port bilgilerini ayarlardan yükle
        server.HOST = self.settings_manager.get_setting("host", "0.0.0.0")
        server.PORT = self.settings_manager.get_setting("port", 9009)

        self.server_thread = None
        self.server_running = False

        # Language Extensions
        self.language_extensions = {
            'Python': ['.py', '.pyw', '.pyc', '.pyd', '.pyo'],
            'JavaScript': ['.js', '.jsx', '.ts', '.tsx'],
            'HTML/CSS': ['.html', '.htm', '.css', '.scss'],
            'Java': ['.java', '.class', '.jar'],
            'C/C++': ['.c', '.cpp', '.h', '.hpp'],
            'Text': ['.txt', '.md', '.csv', '.json']
        }

        # Ana container
        main_layout = QVBoxLayout()

        # Tab widget oluştur
        self.tab_widget = QTabWidget()

        # Tab 1: Genel Ayarlar
        general_tab = QWidget()
        general_layout = QVBoxLayout()

        # Klasör Seçimi
        self.dir_label = QLabel(f"Paylaşılacak klasör: {self.base_dir if self.base_dir else 'Henüz seçilmedi'}")
        self.select_dir_btn = QPushButton("Klasör Seç")
        self.select_dir_btn.clicked.connect(self.select_directory)

        # Sunucu IP ve Port ayarları
        ip_port_layout = QHBoxLayout()

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("IP:"))
        # IP seçimi için QComboBox kullan
        self.ip_combo = QComboBox()
        self.ip_combo.setEditable(True)
        self.ip_combo.setInsertPolicy(QComboBox.InsertAtTop)
        # IP listesini doldur
        self.ip_list = self.get_local_ip_addresses()
        self.ip_combo.addItems(self.ip_list)
        # Eğer ayarlarda kayıtlı bir IP varsa onu seçili yap
        if server.HOST in self.ip_list:
            self.ip_combo.setCurrentText(server.HOST)
        else:
            self.ip_combo.setCurrentText(server.HOST)
        self.ip_combo.currentTextChanged.connect(self.update_server_host)
        ip_layout.addWidget(self.ip_combo)
        # Kullanıcı yeni IP eklediğinde combobox'a ekle
        self.ip_combo.lineEdit().editingFinished.connect(self._add_ip_if_new)

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit(str(server.PORT))
        self.port_input.setPlaceholderText("9009")
        self.port_input.textChanged.connect(self.update_server_port)
        port_layout.addWidget(self.port_input)

        ip_port_layout.addLayout(ip_layout)
        ip_port_layout.addLayout(port_layout)

        general_layout.addWidget(self.dir_label)
        general_layout.addWidget(self.select_dir_btn)
        general_layout.addLayout(ip_port_layout)
        general_layout.addStretch()

        general_tab.setLayout(general_layout)

        # Tab 2: İzin Verilen Uzantılar
        allowed_tab = QWidget()
        allowed_layout = QVBoxLayout()

        # Language Combobox
        self.language_combo = QComboBox()
        self.language_combo.addItems(self.language_extensions.keys())
        self.language_combo.currentTextChanged.connect(self.update_extensions)

        # Uzantı Listesi
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText("Paylaşılacak uzantılar (örn: .py)")
        self.ext_list = QListWidget()

        ext_layout = QHBoxLayout()
        self.add_ext_btn = QPushButton("Ekle")
        self.add_ext_btn.clicked.connect(self.add_extension)
        self.remove_ext_btn = QPushButton("Sil")
        self.remove_ext_btn.clicked.connect(self.remove_extension)
        ext_layout.addWidget(self.add_ext_btn)
        ext_layout.addWidget(self.remove_ext_btn)

        allowed_layout.addWidget(QLabel("Dil Seçimi:"))
        allowed_layout.addWidget(self.language_combo)
        allowed_layout.addWidget(QLabel("Paylaşılacak Uzantılar:"))
        allowed_layout.addWidget(self.ext_input)
        allowed_layout.addLayout(ext_layout)
        allowed_layout.addWidget(self.ext_list)

        allowed_tab.setLayout(allowed_layout)

        # Tab 3: Hariç Tutulan Uzantılar
        excluded_ext_tab = QWidget()
        excluded_ext_layout = QVBoxLayout()

        self.excluded_ext_input = QLineEdit()
        self.excluded_ext_input.setPlaceholderText("Hariç tutulacak uzantı (örn: .exe)")
        self.excluded_ext_list = QListWidget()

        excluded_ext_btn_layout = QHBoxLayout()
        self.add_excluded_ext_btn = QPushButton("Ekle")
        self.add_excluded_ext_btn.clicked.connect(self.add_excluded_extension)
        self.remove_excluded_ext_btn = QPushButton("Sil")
        self.remove_excluded_ext_btn.clicked.connect(self.remove_excluded_extension)
        excluded_ext_btn_layout.addWidget(self.add_excluded_ext_btn)
        excluded_ext_btn_layout.addWidget(self.remove_excluded_ext_btn)

        excluded_ext_layout.addWidget(QLabel("Hariç Tutulacak Uzantılar:"))
        excluded_ext_layout.addWidget(self.excluded_ext_input)
        excluded_ext_layout.addLayout(excluded_ext_btn_layout)
        excluded_ext_layout.addWidget(self.excluded_ext_list)

        excluded_ext_tab.setLayout(excluded_ext_layout)

        # Tab 4: Hariç Tutulan Klasörler
        excluded_dir_tab = QWidget()
        excluded_dir_layout = QVBoxLayout()

        self.excluded_dir_input = QLineEdit()
        self.excluded_dir_input.setPlaceholderText("Hariç tutulacak klasör (örn: node_modules)")
        self.excluded_dir_list = QListWidget()

        excluded_dir_btn_layout = QHBoxLayout()
        self.add_excluded_dir_btn = QPushButton("Ekle")
        self.add_excluded_dir_btn.clicked.connect(self.add_excluded_directory)
        self.remove_excluded_dir_btn = QPushButton("Sil")
        self.remove_excluded_dir_btn.clicked.connect(self.remove_excluded_directory)
        excluded_dir_btn_layout.addWidget(self.add_excluded_dir_btn)
        excluded_dir_btn_layout.addWidget(self.remove_excluded_dir_btn)

        excluded_dir_layout.addWidget(QLabel("Hariç Tutulacak Klasörler:"))
        excluded_dir_layout.addWidget(self.excluded_dir_input)
        excluded_dir_layout.addLayout(excluded_dir_btn_layout)
        excluded_dir_layout.addWidget(self.excluded_dir_list)

        excluded_dir_tab.setLayout(excluded_dir_layout)

        # Tab 5: Giriş Yapan Kullanıcılar
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)
        self.users_list = QListWidget()
        users_layout.addWidget(QLabel("Giriş Yapanlar:"))
        users_layout.addWidget(self.users_list)

        # Tabları ekle
        self.tab_widget.addTab(general_tab, "Genel")
        self.tab_widget.addTab(users_tab, "Giriş Yapanlar")
        self.tab_widget.addTab(allowed_tab, "İzin Verilen Uzantılar")
        self.tab_widget.addTab(excluded_ext_tab, "Hariç Tutulan Uzantılar")
        self.tab_widget.addTab(excluded_dir_tab, "Hariç Tutulan Klasörler")


        # Sunucu Kontrolleri
        self.start_btn = QPushButton("Sunucuyu Başlat")
        self.start_btn.clicked.connect(self.toggle_server)

        # Ana layout'a ekleme
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.start_btn)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Aktif kullanıcıları periyodik güncelle
        from PyQt5.QtCore import QTimer
        def refresh_users():
            self.users_list.clear()
            for addr, name in server.active_users.items():
                self.users_list.addItem(f"{name} - {addr[0]}:{addr[1]}")
        timer = QTimer(self)
        timer.timeout.connect(refresh_users)
        timer.start(1000)

        # Varsayılan listeleri doldur
        if not self.allowed_extensions:
            self.update_extensions(self.language_combo.currentText())
        else:
            self.populate_extension_list()

        self.populate_excluded_lists()

    def get_local_ip_addresses(self):
        """
        Makinenin sahip olduğu tüm IPv4 adreslerini ve bazı sabit yerel adresleri döndürür.
        """
        import socket
        ip_list = set()
        ip_list.update(["127.0.0.1", "localhost", "0.0.0.0"])
        try:
            for interface in socket.getaddrinfo(socket.gethostname(), None):
                ip = interface[4][0]
                if "." in ip and not ip.startswith("127."):
                    ip_list.add(ip)
        except Exception:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_list.add(s.getsockname()[0])
            s.close()
        except Exception:
            pass
        return sorted(ip_list)

    def update_server_host(self, host):
        """
        Sunucu IP adresini günceller.
        Args:
            host (str): Seçilen veya girilen IP adresi
        """
        server.HOST = host
        self.settings_manager.set_setting("host", host)

    def _add_ip_if_new(self):
        """
        Kullanıcı combobox'a yeni bir IP girerse, onu listeye ekler.
        """
        ip = self.ip_combo.currentText().strip()
        if ip and ip not in self.ip_list:
            self.ip_combo.addItem(ip)
            self.ip_list.append(ip)

        """
        Makinenin sahip olduğu tüm IPv4 adreslerini ve bazı sabit yerel adresleri döndürür.
        """
        import socket
        ip_list = set()
        ip_list.update(["127.0.0.1", "localhost", "0.0.0.0"])
        try:
            for interface in socket.getaddrinfo(socket.gethostname(), None):
                ip = interface[4][0]
                if "." in ip and not ip.startswith("127."):
                    ip_list.add(ip)
        except Exception:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_list.add(s.getsockname()[0])
            s.close()
        except Exception:
            pass
        return sorted(ip_list)

    def populate_extension_list(self):
        """İzin verilen uzantılar listesini doldur"""
        self.ext_list.clear()
        for ext in self.allowed_extensions:
            self.ext_list.addItem(ext)

    def populate_excluded_lists(self):
        """Hariç tutulan uzantı ve klasör listelerini doldur"""
        # Uzantılar
        self.excluded_ext_list.clear()
        for ext in self.excluded_extensions:
            self.excluded_ext_list.addItem(ext)

        # Klasörler
        self.excluded_dir_list.clear()
        for dir_name in self.excluded_directories:
            self.excluded_dir_list.addItem(dir_name)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Klasör Seç")
        if directory:
            self.base_dir = directory
            self.dir_label.setText(f"Paylaşılacak klasör: {directory}")
            # Ayarları kaydet
            self.settings_manager.set_setting("base_dir", directory)

    def add_extension(self):
        ext = self.ext_input.text().strip()
        if ext and ext not in self.allowed_extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            self.allowed_extensions.append(ext)
            self.ext_list.addItem(ext)
            self.ext_input.clear()
            # Ayarları kaydet
            self.settings_manager.set_setting("allowed_extensions", self.allowed_extensions)

    def remove_extension(self):
        selected = self.ext_list.currentItem()
        if selected:
            ext = selected.text()
            self.allowed_extensions.remove(ext)
            self.ext_list.takeItem(self.ext_list.row(selected))
            # Ayarları kaydet
            self.settings_manager.set_setting("allowed_extensions", self.allowed_extensions)

    def add_excluded_extension(self):
        ext = self.excluded_ext_input.text().strip()
        if ext and ext not in self.excluded_extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            self.excluded_extensions.append(ext)
            self.excluded_ext_list.addItem(ext)
            self.excluded_ext_input.clear()
            # Ayarları kaydet
            self.settings_manager.set_setting("excluded_extensions", self.excluded_extensions)

    def remove_excluded_extension(self):
        selected = self.excluded_ext_list.currentItem()
        if selected:
            ext = selected.text()
            self.excluded_extensions.remove(ext)
            self.excluded_ext_list.takeItem(self.excluded_ext_list.row(selected))
            # Ayarları kaydet
            self.settings_manager.set_setting("excluded_extensions", self.excluded_extensions)

    def add_excluded_directory(self):
        dir_name = self.excluded_dir_input.text().strip()
        if dir_name and dir_name not in self.excluded_directories:
            self.excluded_directories.append(dir_name)
            self.excluded_dir_list.addItem(dir_name)
            self.excluded_dir_input.clear()
            # Ayarları kaydet
            self.settings_manager.set_setting("excluded_directories", self.excluded_directories)

    def remove_excluded_directory(self):
        selected = self.excluded_dir_list.currentItem()
        if selected:
            dir_name = selected.text()
            self.excluded_directories.remove(dir_name)
            self.excluded_dir_list.takeItem(self.excluded_dir_list.row(selected))
            # Ayarları kaydet
            self.settings_manager.set_setting("excluded_directories", self.excluded_directories)

    def update_extensions(self, language):
        self.ext_list.clear()
        self.allowed_extensions.clear()
        for ext in self.language_extensions[language]:
            self.allowed_extensions.append(ext)
            self.ext_list.addItem(ext)
        # Ayarları kaydet
        self.settings_manager.set_setting("allowed_extensions", self.allowed_extensions)

    def toggle_server(self):
        if not self.server_running:
            if not self.base_dir or not os.path.isdir(self.base_dir):
                QMessageBox.warning(self, "Uyarı", "Lütfen geçerli bir klasör seçin.")
                return

            server.BASE_DIR = self.base_dir

            # Uzantı ve klasör ayarlarını file_browser modülüne aktar
            from file_browser import set_allowed_extensions, set_excluded_directories, set_excluded_extensions

            # Ayarları güncelle
            set_allowed_extensions(self.allowed_extensions)
            set_excluded_directories(self.excluded_directories)
            set_excluded_extensions(self.excluded_extensions)

            self.server_thread = threading.Thread(target=server.start_server, daemon=True)
            self.server_thread.start()

            self.server_running = True
            self.start_btn.setText("Sunucuyu Durdur")
        else:
            server.stop_server()  # Sunucu tarafında uygulanmalı
            self.server_running = False
            self.start_btn.setText("Sunucuyu Başlat")

    def update_server_port(self, port):
        """
        Sunucu port numarasını günceller.
        Args:
            port (str): Girilen port numarası
        """
        try:
            port_num = int(port)
            server.PORT = port_num
            self.settings_manager.set_setting("port", port_num)
        except ValueError:
            pass  # Geçersiz port numarası, güncelleme yapmaß

    def closeEvent(self, event):
        # Sunucu çalışıyorsa düzgün şekilde kapat
        if self.server_running:
            server.stop_server()
            self.server_running = False

        # Tüm ayarları son kez kaydet
        self.settings_manager.save_settings({
            "base_dir": self.base_dir,
            "host": server.HOST,
            "port": server.PORT,
            "allowed_extensions": self.allowed_extensions,
            "excluded_directories": self.excluded_directories,
            "excluded_extensions": self.excluded_extensions
        })

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ServerControlWindow()
    win.show()
    sys.exit(app.exec_())
