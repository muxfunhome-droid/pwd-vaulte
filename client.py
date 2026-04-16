import socket
from cryptography.fernet import Fernet
import os
import sys
import argparse

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
    # Настройка парсера аргументов
    parser = argparse.ArgumentParser(description="Менеджер паролей (клиент)")
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # Команда SAVE: python3 test.py SAVE email password login
    save_parser = subparsers.add_parser('SAVE', help='Сохранить данные')
    save_parser.add_argument('email', help='Email или название сервиса')
    save_parser.add_argument('password', help='Пароль')
    save_parser.add_argument('login', help='ID пользователя / Логин')

    # Команда GET: python3 test.py GET login
    get_parser = subparsers.add_parser('GET', help='Получить данные по логину')
    get_parser.add_argument('login', help='Логин для поиска')

    # Парсим аргументы из sys.argv
    args = parser.parse_args()

    # Поиск сервера
    server_ip = find_server()
    if not server_ip:
        print("Server not found.")
        return

    # Логика выполнения команд
    if args.command == 'SAVE':
        email_enc = encrypt_message(args.email)
        pwd_enc = encrypt_message(args.password)
        full_msg = f"SAVE {email_enc} {pwd_enc}; {args.login}"
        send_request(server_ip, full_msg)
        print(f"Данные для {args.login} отправлены.")

    elif args.command == 'GET':
        send_request(server_ip, f"GET {args.login}")

    else:
        # Если запущен без аргументов, выводим справку
        parser.print_help()

if __name__ == "__main__":
    main()

