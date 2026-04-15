import socket
from cryptography.fernet import Fernet
import os

KEY_FILE = '.key'

def load_or_generate_key():
    # Проверяем, существует ли файл
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        # Генерируем новый ключ
        key = Fernet.generate_key()
        # Сохраняем его в файл
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key
def encrypt_message(message):
    key = load_or_generate_key()
    f = Fernet(key)
    return f.encrypt(message.encode()).decode()

# Расшифровка
def decrypt_message(encrypted_text):
    key = load_or_generate_key()
    f = Fernet(key)
    # Если строка (base64), оставляем как есть
    # Если bytes, декодируем в строку
    if isinstance(encrypted_text, bytes):
        encrypted_text = encrypted_text.decode('utf-8')
    return f.decrypt(encrypted_text)  # Возвращаем bytes

def find_server():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.settimeout(2.0)
    try:
        udp_sock.sendto(b"DISCOVER_VAULT_SERVER", ('255.255.255.255', 5555))
        data, addr = udp_sock.recvfrom(1024)
        if data == b"I_AM_VAULT_SERVER":
            return addr[0]
    except socket.timeout:
        return None
    finally:
        udp_sock.close()

def send_request(ip, message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
            tcp_sock.connect((ip, 6666))
            greeting = tcp_sock.recv(1024)
            tcp_sock.send(message.encode('utf-8'))
            response = tcp_sock.recv(8192)
            
            # Декодируем bytes в строку
            response_text = response.decode('utf-8')
            
            # Разделяем на заголовок и зашифрованные данные
            lines = response_text.split('\n')
            print(f"\n[SERVER]: {lines[0]}")  # Выводим заголовок
            
            # Расшифровываем остальные строки (если они есть)
            for line in lines[1:]:
                if line.strip():  # Пропускаем пустые строки
                    parts = line.split(' | ')
                    try:
                        email = decrypt_message(parts[0].strip()).decode('utf-8')
                        pwd = decrypt_message(parts[1].strip()).decode('utf-8')
                        print(f"  Email: {email} | Password: {pwd}")
                    except Exception as e:
                        print(f"  [Ошибка расшифровки]: {repr(e)}")
    except Exception as e:
        print("Connection error:", repr(e))

def main():
    server_ip = find_server()
    if not server_ip:
        print("Server not found.")
        return
    print("Connected to:", server_ip)

    while True:
        choice = input("1-SAVE 2-GET 3-EXIT > ").strip().lower()
        if choice in ('1','save'):
            email = encrypt_message(input("email/service: "))
            pwd = encrypt_message(input("password: "))
            login = input("login id: ")
            full_msg = f"SAVE {email} {pwd}; {login}"
            send_request(server_ip, full_msg)
        elif choice in ('2','get'):
            login = input("login to search: ")
            send_request(server_ip, f"GET {login}")
        elif choice in ('3','exit'):
            break
        else:
            print("Unknown command")

if __name__ == "__main__":
    main()

