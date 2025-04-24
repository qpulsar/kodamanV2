import socket

def get_local_ip_addresses():
    """
    Makinenin sahip olduğu tüm IPv4 adreslerini ve bazı sabit yerel adresleri döndürür.
    """
    ip_list = set()
    # Yerel alternatifler
    ip_list.update(["127.0.0.1", "localhost", "0.0.0.0"])
    try:
        for interface in socket.getaddrinfo(socket.gethostname(), None):
            ip = interface[4][0]
            # Sadece IPv4 ve localhost olmayanları ekle
            if "." in ip and not ip.startswith("127."):
                ip_list.add(ip)
    except Exception:
        pass
    # Aktif ağ arayüzlerinden de ekle
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_list.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    return sorted(ip_list)

if __name__ == "__main__":
    for ip in get_local_ip_addresses():
        print(ip)
