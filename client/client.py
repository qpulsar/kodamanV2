import sys
import socket
import json
import logging
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import protocol

# Logging ayarları
logging.basicConfig(
    level=logging.DEBUG,  # Debug seviyesine çektim
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('client.log')
    ]
)
logger = logging.getLogger('FileClient')

class ClientConnection:
    running = None
    def __init__(self, host='127.0.0.1', port=9009):
        self.host = host
        self.port = port
        self.sock = None
        self._create_socket()
        self.buffer = ""
        logger.info(f"Client bağlantısı oluşturuldu: {host}:{port}")

    def _create_socket(self):
        """Yeni bir soket oluştur"""
        if self.sock:
            self.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.debug("Yeni soket oluşturuldu")

    def connect(self):
        """Sunucuya bağlan"""
        # Eğer soket yoksa veya kapalıysa yeni bir soket oluştur
        if not self.sock:
            self._create_socket()
        try:
            logger.info(f"Sunucuya bağlanılıyor: {self.host}:{self.port}")
            self.sock.connect((self.host, self.port))
            self.running = True
            logger.info(f"Sunucuya bağlanıldı: {self.host}:{self.port}")
        except Exception as e:
            # Bağlantı hatası durumunda soketi temizle ve hatayı yeniden yükselt
            logger.error(f"Bağlantı hatası: {str(e)}")
            self.close()
            raise e

    def close(self):
        """Bağlantıyı kapat"""
        self.running = False
        if self.sock:
            try:
                # Gracefully shutdown the socket
                logger.debug("Soket kapatılıyor...")
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                # Socket already closed
                logger.debug("Soket zaten kapalı")
                pass
            finally:
                # Ensure socket is closed
                self.sock.close()
                self.sock = None
                logger.info("Bağlantı kapatıldı")

    def send(self, message):
        try:
            logger.debug(f"Gönderilen mesaj: {message[:100]}...")
            self.sock.sendall(message.encode("utf-8"))
            logger.debug(f"Mesaj gönderildi: {message[:50]}...")
        except Exception as e:
            logger.error(f"Mesaj gönderme hatası: {str(e)}")
            raise

    def receive_messages(self):
        """
        Socket'tan gelen verileri okur ve \n ile ayrılmış JSON mesajlarını yield eder.
        """
        logger.info("Mesaj dinleme başladı")
        while self.running:
            try:
                data = self.sock.recv(1024).decode("utf-8")
                if not data:  # Sunucu bağlantıyı kapattı
                    logger.warning("Sunucu bağlantıyı kapattı")
                    self.running = False
                    break
                
                logger.debug(f"Ham veri alındı: {data[:100]}...")
                self.buffer += data
                
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    message = protocol.parse_message(line)
                    if message:
                        logger.debug(f"İşlenen mesaj: {str(message)[:200]}...")
                        
                        # Hata yanıtlarını işle
                        if message.get("response") == "error":
                            error_msg = message.get("error", "Bilinmeyen hata")
                            logger.warning(f"Sunucu hatası: {error_msg}")
                            yield {"type": "error", "message": error_msg}
                        elif message.get("response") == "tree":
                            logger.info("Dosya ağacı alındı")
                            tree_data = message.get("data", {})
                            logger.debug(f"Ağaç verisi: {str(tree_data)[:200]}...")
                            yield message
                        elif message.get("response") == "file":
                            path = message.get("path", "")
                            content_length = len(message.get("content", ""))
                            logger.info(f"Dosya alındı: {path} ({content_length} karakter)")
                            yield message
                        else:
                            logger.info(f"Diğer mesaj alındı: {message.get('response', 'bilinmeyen')}")
                            yield message
            except (ConnectionError, OSError, socket.error) as e:
                # Bağlantı hatası oluştu
                logger.error(f"Bağlantı hatası: {str(e)}")
                self.running = False
                yield {"type": "error", "message": f"Bağlantı hatası: {str(e)}"}
                break
        
        # Bağlantı koptuğunda soketi temizle
        logger.info("Mesaj dinleme sonlandı")
        self.close()
        yield {"type": "connection_lost", "message": "Sunucu bağlantısı kesildi"}

    # === Yardımcı metodlar ===
    def request_tree(self):
        """Dosya ağacını iste"""
        try:
            logger.info("Dosya ağacı isteniyor")
            self.send(protocol.make_get_tree_message())
        except Exception as e:
            logger.error(f"Dosya ağacı isteme hatası: {str(e)}")
            raise

    def request_file(self, rel_path):
        """Dosya içeriğini iste"""
        try:
            # Path güvenlik kontrolü - client tarafında da kontrol edelim
            if ".." in rel_path.split("/"):
                logger.warning(f"Güvenlik uyarısı: Dosya yolu '..' içeriyor: {rel_path}")
                return False
                
            logger.info(f"Dosya isteniyor: {rel_path}")
            self.send(protocol.make_get_file_message(rel_path))
            return True
        except Exception as e:
            logger.error(f"Dosya isteme hatası: {str(e)}")
            raise