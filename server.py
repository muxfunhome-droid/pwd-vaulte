import socket
import sqlite3
import threading

DB = 'vault_storage.db'

def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS secrets (
            login TEXT,
            email TEXT,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def udp_discovery_server():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp.bind(('0.0.0.0', 5555))
    while True:
        try:
            data, addr = udp.recvfrom(1024)
            if data == b"DISCOVER_VAULT_SERVER":
                udp.sendto(b"I_AM_VAULT_SERVER", addr)
        except Exception:
            continue

def save_password(raw_data):
    try:
        main_part, login = raw_data.rsplit(';', 1)
        login = login.strip()
        email, password = main_part.strip().split(None, 1)
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO secrets VALUES (?, ?, ?)', (login, email, password))
        conn.commit()
        conn.close()
        return f"OK: saved for '{login}'"
    except ValueError:
        return "ERROR: bad format. Use 'email password; login'"

def get_passwords_by_login(login):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute('SELECT email, password FROM secrets WHERE login = ?', (login,))
    results = cursor.fetchall()
    conn.close()
    if results:
        lines = [f"Found {len(results)} record(s) for '{login}':"]
        for email, pwd in results:
            lines.append(f"{email} | {pwd}")
        return '\n'.join(lines)
    else:
        return f"No records for '{login}'."

def handle_client_request(message):
    parts = message.split(' ', 1)
    command = parts[0].upper()
    if command == "SAVE" and len(parts) > 1:
        return save_password(parts[1])
    elif command == "GET" and len(parts) > 1:
        return get_passwords_by_login(parts[1].strip())
    else:
        return "ERROR: Unknown command"

def start_main_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', 6666))  # TCP on 6666
    server_sock.listen(5)
    print("TCP server listening on 6666")

    while True:
        client_conn, addr = server_sock.accept()
        threading.Thread(target=handle_tcp_client, args=(client_conn, addr), daemon=True).start()

def handle_tcp_client(client_conn, addr):
    with client_conn:
        try:
            client_conn.send(b"I_AM_VAULT_SERVER")  # handshake
            # read client's request
            raw_data = client_conn.recv(4096).decode('utf-8')
            if not raw_data:
                return
            response = handle_client_request(raw_data)
            client_conn.send(response.encode('utf-8'))
        except Exception as e:
            print("Client error:", e)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=udp_discovery_server, daemon=True).start()
    start_main_server()

