import socket

def start_discovery_server():
    # Создаем UDP сокет
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Привязываемся ко всем интерфейсам на порт 5555
    sock.bind(('0.0.0.0', 5555))
    
    print("Сервер поиска запущен и ждет клиента...")
    
    while True:
        # Получаем данные и адрес отправителя
        data, addr = sock.recvfrom(1024)
        message = data.decode('utf-8')
        
        if message == "DISCOVER_VAULT_SERVER":
            print(f"Запрос от клиента {addr}, отправляю подтверждение...")
            # Отправляем ответ «Я сервер»
            sock.sendto("I_AM_VAULT_SERVER".encode('utf-8'), addr)

if __name__ == "__main__":
    start_discovery_server()

