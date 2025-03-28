import json

# Her mesaj satır sonu ile bitmeli (TCP stream ayrımı icin)
MESSAGE_DELIMITER = '\n'

# === Mesaj Olusturucular ===
def make_get_tree_message():
    return json.dumps({"command": "get_tree"}) + MESSAGE_DELIMITER

def make_get_file_message(path):
    return json.dumps({"command": "get_file", "path": path}) + MESSAGE_DELIMITER

def make_update_settings_message(excluded_dirs, excluded_exts):
    """
    Sunucu ayarlarını güncellemek için mesaj oluşturur.
    """
    return json.dumps({
        "command": "update_settings", 
        "excluded_dirs": excluded_dirs, 
        "excluded_exts": excluded_exts
    }) + MESSAGE_DELIMITER

def make_tree_response(data):
    return json.dumps({"response": "tree", "data": data}) + MESSAGE_DELIMITER

def make_file_response(path, content):
    return json.dumps({"response": "file", "path": path, "content": content}) + MESSAGE_DELIMITER

def make_error_response(error_message):
    """
    Hata mesajı oluşturur. Güvenlik ihlali, dosya bulunamama gibi durumlar için kullanılır.
    """
    return json.dumps({"response": "error", "error": error_message}) + MESSAGE_DELIMITER

def make_settings_response(success, message=""):
    """
    Ayarlar güncellemesi yanıtı oluşturur.
    """
    return json.dumps({
        "response": "settings_updated", 
        "success": success, 
        "message": message
    }) + MESSAGE_DELIMITER

# === Mesaj Ayrıştırıcı ===
def parse_message(message_str):
    try:
        return json.loads(message_str)
    except json.JSONDecodeError:
        return None
