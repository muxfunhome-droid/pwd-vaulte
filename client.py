import socket

def find_server():
    # Создаем UDP сокет
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Разрешаем отправку широковещательных пакетов
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Таймаут, чтобы не ждать вечно, если сервера нет
    sock.settimeout(2.0)
    
    server_address = ('255.255.255.255', 5555)
    message = "DISCOVER_VAULT_SERVER".encode('utf-8')
    
    try:
        print("Ищу сервер в локальной сети...")
        sock.sendto(message, server_address)
        
        # Ждем ответа от сервера
        data, addr = sock.recvfrom(1024)
        if data.decode('utf-8') == "I_AM_VAULT_SERVER":
            print(f"Сервер найден! IP-адрес сервера: {addr[0]}")
            return addr[0] # Возвращаем IP для основного подключения (TCP)
            
    except socket.timeout:
        print("Сервер не найден. Проверьте сеть.")
        return None
    finally:
        sock.close()

if __name__ == "__main__":
    server_ip = find_server()

