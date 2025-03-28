import socket
import threading
import logging
import os
import sys

# Modül yolunu ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from file_browser import build_tree, read_file, is_safe_path, set_excluded_directories, set_excluded_extensions, set_allowed_extensions
from shared import protocol

# Logging ayarları
logging.basicConfig(
    level=logging.DEBUG,  # Debug seviyesine çektim
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ]
)
logger = logging.getLogger('FileServer')

# Konfig
HOST = '0.0.0.0'
PORT = 9009
BASE_DIR = '/Users/emin/PycharmProjects/Kodaman2/'  # Bu yol GUI ile secilebilir hale getirilecek

# Başlangıçta base_dir'i normalize et
BASE_DIR = os.path.normpath(os.path.realpath(os.path.abspath(BASE_DIR)))

running = None

def handle_client(conn, addr):
    """Client bağlantısını işle"""
    logger.info(f"[+] Yeni bağlantı: {addr}")
    
    try:
        buffer = ""
        while True:
            # Veri al
            data = conn.recv(1024).decode("utf-8")
            if not data:
                logger.info(f"[-] Bağlantı kapandı: {addr}")
                break
                
            buffer += data
            
            # Mesajları işle
            while protocol.MESSAGE_DELIMITER in buffer:
                message, buffer = buffer.split(protocol.MESSAGE_DELIMITER, 1)
                
                # Mesajı parse et
                try:
                    msg = protocol.parse_message(message)
                    if not msg:
                        logger.warning(f"Geçersiz mesaj formatı: {message[:50]}...")
                        continue
                        
                    logger.info(f"Mesaj alındı: {addr} - {msg.get('command', 'bilinmeyen komut')}")
                    logger.debug(f"Mesaj detayları: {msg}")
                    
                    # Komutları işle
                    if msg.get("command") == "get_tree":
                        # Dosya ağacını gönder
                        tree_data = build_tree(BASE_DIR)
                        response = protocol.make_tree_response(tree_data)
                        conn.sendall(response.encode("utf-8"))
                        logger.info(f"Dosya ağacı gönderildi: {addr}")
                        
                    elif msg.get("command") == "get_file":
                        # Dosya içeriğini gönder
                        rel_path = msg.get("path", "")
                        
                        # Path güvenlik kontrolü
                        if not is_safe_path(BASE_DIR, rel_path):
                            error_msg = f"Güvenlik ihlali: '{rel_path}' yoluna erişim engellendi"
                            logger.warning(f"{error_msg} - {addr}")
                            conn.sendall(protocol.make_error_response(error_msg).encode("utf-8"))
                            continue
                        
                        # Dosyayı oku
                        try:
                            content, error = read_file(BASE_DIR, rel_path)
                            if error:
                                logger.warning(f"Dosya okuma hatası: {error} - {addr}")
                                conn.sendall(protocol.make_error_response(error).encode("utf-8"))
                            else:
                                logger.info(f"Dosya gönderildi: {rel_path} - {addr}")
                                conn.sendall(protocol.make_file_response(rel_path, content).encode("utf-8"))
                        except Exception as e:
                            error_msg = f"Dosya okuma hatası: {str(e)}"
                            logger.error(f"{error_msg} - {addr}")
                            conn.sendall(protocol.make_error_response(error_msg).encode("utf-8"))
                    
                    elif msg.get("command") == "update_settings":
                        # Ayarları güncelle
                        try:
                            excluded_dirs = msg.get("excluded_dirs", [])
                            excluded_exts = msg.get("excluded_exts", [])
                            allowed_exts = msg.get("allowed_exts", [])
                            
                            logger.info(f"Ayarlar güncelleniyor: {len(excluded_dirs)} klasör, {len(excluded_exts)} uzantı hariç tutuluyor, {len(allowed_exts)} uzantı izin veriliyor")
                            logger.debug(f"Hariç tutulan klasörler: {excluded_dirs}")
                            logger.debug(f"Hariç tutulan uzantılar: {excluded_exts}")
                            logger.debug(f"İzin verilen uzantılar: {allowed_exts}")
                            
                            # file_browser.py'deki ayarları güncelle
                            set_excluded_directories(excluded_dirs)
                            set_excluded_extensions(excluded_exts)
                            set_allowed_extensions(allowed_exts)
                            
                            # Başarılı yanıt gönder
                            response = protocol.make_settings_response(True, "Ayarlar başarıyla güncellendi")
                            conn.sendall(response.encode("utf-8"))
                            logger.info(f"Ayarlar güncellendi: {addr}")
                        except Exception as e:
                            error_msg = f"Ayarları güncelleme hatası: {str(e)}"
                            logger.error(f"{error_msg} - {addr}")
                            conn.sendall(protocol.make_error_response(error_msg).encode("utf-8"))
                    
                    else:
                        # Bilinmeyen komut
                        error_msg = f"Bilinmeyen komut: {msg.get('command', 'komut yok')}"
                        logger.warning(f"{error_msg} - {addr}")
                        conn.sendall(protocol.make_error_response(error_msg).encode("utf-8"))
                        
                except Exception as e:
                    # Genel hata durumu
                    error_msg = f"Sunucu hatası: {str(e)}"
                    logger.error(f"{error_msg} - {addr}")
                    try:
                        conn.sendall(protocol.make_error_response(error_msg).encode("utf-8"))
                    except:
                        pass
    
    except ConnectionError:
        logger.info(f"[-] Bağlantı kesildi: {addr}")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {str(e)} - {addr}")
    finally:
        conn.close()
        logger.info(f"[-] Bağlantı kapatıldı: {addr}")


def start_server(base_dir=None):
    global BASE_DIR, running
    
    # Eğer base_dir belirtilmişse, güvenlik kontrollerini uygula
    if base_dir:
        # Path'i normalize et ve mutlak yola dönüştür
        base_dir = os.path.normpath(os.path.realpath(os.path.abspath(base_dir)))
        
        # Dizinin var olduğunu kontrol et
        if not os.path.isdir(base_dir):
            logger.error(f"[SERVER] Belirtilen dizin mevcut değil: {base_dir}")
            return False
            
        # Dizinin okunabilir olduğunu kontrol et
        if not os.access(base_dir, os.R_OK):
            logger.error(f"[SERVER] Belirtilen dizin okunamıyor: {base_dir}")
            return False
            
        BASE_DIR = base_dir
        logger.info(f"[SERVER] Paylaşılan dizin: {BASE_DIR}")
    
    logger.info(f"[SERVER] Başlatılıyor: {HOST}:{PORT}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            s.settimeout(1)  # 1 saniye timeout ile soket dinleme
            logger.info("[SERVER] Dinleniyor...")
            running = True

            while running:
                try:
                    conn, addr = s.accept()
                    thread = threading.Thread(target=handle_client, args=(conn, addr))
                    thread.daemon = True  # Ana program sonlandığında thread'lerin de sonlanmasını sağlar
                    thread.start()
                except socket.timeout:
                    # Timeout olduğunda running değişkenini kontrol et
                    continue
                except Exception as e:
                    logger.error(f"[SERVER] Bağlantı kabul hatası: {e}")
            
            logger.info("[SERVER] Durduruldu")
            return True
    except Exception as e:
        logger.error(f"[SERVER] Başlatma hatası: {e}")
        return False

def stop_server():
    global running
    logger.info("[SERVER] Durdurma isteği alındı")
    running = False

if __name__ == '__main__':
    start_server()
