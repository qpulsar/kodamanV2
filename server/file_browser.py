import os
import logging

# Paylaşılacak dosya uzantıları
ALLOWED_EXTENSIONS = [
    '.txt', '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.js', '.html', '.css',
    '.json', '.xml', '.md', '.csv', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp3', '.mp4', '.wav', '.avi'
]

# Gönderilemeyecek klasörler
EXCLUDED_DIRECTORIES = [
    '__pycache__', 'venv', '.venv', 'env', '.env', '.git', '.idea', '.vscode', 
    'node_modules', 'dist', 'build', '.pytest_cache', '.ipynb_checkpoints'
]

# Gönderilemeyecek dosya uzantıları
EXCLUDED_EXTENSIONS = [
    '.pyc', '.pyo', '.so', '.dll', '.exe', '.bin', '.dat', '.db', '.sqlite', '.sqlite3'
]

# Logger oluştur
logger = logging.getLogger('FileServer.Browser')

def set_allowed_extensions(extensions):
    """
    İzin verilen dosya uzantılarını ayarla
    """
    global ALLOWED_EXTENSIONS
    ALLOWED_EXTENSIONS = extensions
    logger.info(f"İzin verilen dosya uzantıları güncellendi: {ALLOWED_EXTENSIONS}")

def set_excluded_directories(directories):
    """
    Hariç tutulacak klasörleri ayarla
    """
    global EXCLUDED_DIRECTORIES
    EXCLUDED_DIRECTORIES = directories
    logger.info(f"Hariç tutulan klasörler güncellendi: {EXCLUDED_DIRECTORIES}")

def set_excluded_extensions(extensions):
    """
    Hariç tutulacak dosya uzantılarını ayarla
    """
    global EXCLUDED_EXTENSIONS
    EXCLUDED_EXTENSIONS = extensions
    logger.info(f"Hariç tutulan dosya uzantıları güncellendi: {EXCLUDED_EXTENSIONS}")

def is_safe_path(base_dir, rel_path):
    """
    Güvenlik kontrolü: Verilen yolun base_dir dışına çıkıp çıkmadığını kontrol eder.
    Sembolik bağlantıları da dikkate alır.
    """
    # Önce base_dir'in mutlak yolunu al ve normalize et
    base_dir = os.path.normpath(os.path.realpath(os.path.abspath(base_dir)))
    
    # Tam yolu hesapla ve normalize et
    requested_path = os.path.normpath(os.path.realpath(os.path.abspath(os.path.join(base_dir, rel_path))))
    
    # Güvenlik kontrolü: Hesaplanan yol base_dir ile başlıyor mu?
    is_safe = requested_path.startswith(base_dir)
    
    if not is_safe:
        logger.warning(f"Güvenlik ihlali girişimi tespit edildi: {rel_path} yolu base_dir dışına çıkmaya çalışıyor")
    
    return is_safe


def build_tree(base_dir):
    """
    Belirtilen klasörden başlayarak dosya ve klasör ağacını döner.
    Sadece isim ve alt klasör bilgisi içerir.
    Güvenlik kontrolü yaparak base_dir dışına çıkmayı engeller.
    Sadece izin verilen uzantılara sahip dosyaları içerir.
    Hariç tutulan klasörleri ve dosya uzantılarını atlar.
    """
    logger.info(f"Dosya ağacı oluşturuluyor: {base_dir}")
    
    # Base_dir'i normalize et
    base_dir = os.path.normpath(os.path.realpath(os.path.abspath(base_dir)))
    
    tree = {}
    total_files = 0
    allowed_files = 0
    excluded_dirs = 0
    excluded_files = 0
    
    for root, dirs, files in os.walk(base_dir):
        # Hariç tutulan klasörleri dirs listesinden çıkar
        # Bu, os.walk'ın bu klasörlere girmesini engeller
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRECTORIES]
        
        # Güvenlik kontrolü: Bu klasör base_dir içinde mi?
        rel_path_to_root = os.path.relpath(root, base_dir)
        if not is_safe_path(base_dir, rel_path_to_root):
            logger.warning(f"Güvenlik kontrolü başarısız: {rel_path_to_root}")
            continue
            
        # Göreli path
        rel_path = os.path.relpath(root, base_dir)
        
        # Klasör hariç tutulanlar listesinde mi kontrol et
        if any(excluded_dir in rel_path.split(os.sep) for excluded_dir in EXCLUDED_DIRECTORIES):
            logger.debug(f"Hariç tutulan klasör atlandı: {rel_path}")
            excluded_dirs += 1
            continue
        
        # Kök dizin için özel işlem
        if rel_path == ".":
            # Sadece izin verilen uzantılara sahip dosyaları filtrele
            filtered_files = []
            for file in files:
                total_files += 1
                _, ext = os.path.splitext(file)
                
                # Hariç tutulan uzantıları kontrol et
                if ext.lower() in EXCLUDED_EXTENSIONS:
                    logger.debug(f"Hariç tutulan uzantı: {file} (uzantı: {ext})")
                    excluded_files += 1
                    continue
                
                if ext.lower() in ALLOWED_EXTENSIONS:
                    filtered_files.append(file)
                    allowed_files += 1
                    logger.debug(f"İzin verilen dosya: {file}")
                else:
                    logger.debug(f"Filtrelenen dosya: {file} (uzantı: {ext})")
            
            # Kök dizin için dosyaları ve alt klasörleri ayarla
            tree["files"] = filtered_files
            tree["children"] = {}
            continue
        
        # Alt dizinler için
        path_parts = rel_path.split(os.sep)
        current = tree
        
        # Dizin yolunu oluştur
        for i, part in enumerate(path_parts):
            if i < len(path_parts) - 1:
                current = current.setdefault("children", {}).setdefault(part, {})
            else:
                # Son dizin
                if "children" not in current:
                    current["children"] = {}
                if part not in current["children"]:
                    current["children"][part] = {"files": [], "children": {}}
                
                # Sadece izin verilen uzantılara sahip dosyaları filtrele
                filtered_files = []
                for file in files:
                    total_files += 1
                    _, ext = os.path.splitext(file)
                    
                    # Hariç tutulan uzantıları kontrol et
                    if ext.lower() in EXCLUDED_EXTENSIONS:
                        logger.debug(f"Hariç tutulan uzantı: {os.path.join(rel_path, file)} (uzantı: {ext})")
                        excluded_files += 1
                        continue
                    
                    if ext.lower() in ALLOWED_EXTENSIONS:
                        filtered_files.append(file)
                        allowed_files += 1
                        #logger.debug(f"İzin verilen dosya: {os.path.join(rel_path, file)}")
                    else:
                        pass
                        #logger.debug(f"Filtrelenen dosya: {os.path.join(rel_path, file)} (uzantı: {ext})")
                
                current["children"][part]["files"] = filtered_files

    logger.info(f"Dosya ağacı oluşturuldu. Toplam dosya: {total_files}, İzin verilen: {allowed_files}, Hariç tutulan klasör: {excluded_dirs}, Hariç tutulan dosya: {excluded_files}")
    logger.debug(f"Ağaç yapısı: {str(tree)[:500]}...")
    return tree


def read_file(base_dir, rel_path):
    """
    Belirli bir dosyanın içeriğini readonly okur.
    base_dir dışına çıkmaya çalışırsa hata verir.
    """
    logger.info(f"Dosya okunuyor: {rel_path}")
    
    # Güvenlik kontrolü
    if not is_safe_path(base_dir, rel_path):
        logger.warning(f"Güvenlik ihlali: {rel_path} yolu base_dir dışına çıkmaya çalışıyor")
        return None, "Güvenlik ihlali: Yetkisiz erişim girişimi"
    
    # Klasör hariç tutulanlar listesinde mi kontrol et
    if any(excluded_dir in rel_path.split(os.sep) for excluded_dir in EXCLUDED_DIRECTORIES):
        logger.warning(f"Hariç tutulan klasöre erişim girişimi: {rel_path}")
        return None, "Bu klasöre erişim izni yok"
    
    # Tam yolu hesapla
    full_path = os.path.join(base_dir, rel_path)
    
    # Dosya var mı kontrol et
    if not os.path.isfile(full_path):
        logger.error(f"Dosya bulunamadı: {full_path}")
        return None, "Dosya bulunamadı"
    
    try:
        # Dosya uzantısını kontrol et
        _, ext = os.path.splitext(full_path)
        
        # Hariç tutulan uzantıları kontrol et
        if ext.lower() in EXCLUDED_EXTENSIONS:
            logger.warning(f"Hariç tutulan dosya uzantısına erişim girişimi: {ext}")
            return None, f"Bu dosya uzantısına ({ext}) erişim izni yok"
        
        if ext.lower() not in ALLOWED_EXTENSIONS:
            logger.warning(f"İzin verilmeyen dosya uzantısı: {ext}")
            return None, f"Bu dosya uzantısına ({ext}) erişim izni yok"
        
        # Dosyayı oku
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Dosya başarıyla okundu: {rel_path} ({len(content)} byte)")
        return content, None
    except Exception as e:
        logger.error(f"Dosya okuma hatası: {str(e)}")
        return None, f"Dosya okuma hatası: {str(e)}"