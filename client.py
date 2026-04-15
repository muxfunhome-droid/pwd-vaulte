import socket

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
            # read handshake first
            greeting = tcp_sock.recv(1024)
            # now send request
            tcp_sock.send(message.encode('utf-8'))
            response = tcp_sock.recv(8192).decode('utf-8')
            print(f"\n[SERVER]: {response}")
    except Exception as e:
        print("Connection error:", e)

def main():
    server_ip = find_server()
    if not server_ip:
        print("Server not found.")
        return
    print("Connected to:", server_ip)

    while True:
        choice = input("1-SAVE 2-GET 3-EXIT > ").strip().lower()
        if choice in ('1','save'):
            email = input("email/service: ")
            pwd = input("password: ")
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

