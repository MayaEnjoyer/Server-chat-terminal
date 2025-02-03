import socket
import threading
import random
import os
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_color():
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#6d59b6', '#f39c12']
    return random.choice(colors)

class ChatServer:
    def __init__(self, host='192.168.100.98', port=5555):
        self.host = host
        self.port = port
        self.rooms = defaultdict(list)
        self.log_dir = 'logs'
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def get_log_file(self, room_name):
        return os.path.join(self.log_dir, f"{room_name}.log")

    def append_to_log(self, room_name, message):
        with open(self.get_log_file(room_name), 'a', encoding='utf-8') as f:
            f.write(message + '\n')

    def get_room_history(self, room_name):
        log_file = self.get_log_file(room_name)
        if not os.path.exists(log_file):
            return ''
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.read()

    def broadcast(self, room, message, sender_socket=None):
        for client in room:
            if client[0] != sender_socket:
                try:
                    client[0].send((message + '\n').encode('utf-8'))
                except Exception as e:
                    logging.error(f"Error broadcasting message: {e}")
        if room:
            room_name = room[0][3]
            self.append_to_log(room_name, message)

    def send_userlist(self, room_name):
        users = [c[2] for c in self.rooms[room_name]]
        userlist_msg = f"USERLIST:{room_name}:" + ','.join(users) + '\n'
        for client in self.rooms[room_name]:
            try:
                client[0].send(userlist_msg.encode('utf-8'))
            except Exception as e:
                logging.error(f"Error sending userlist: {e}")

    def send_room_history(self, client_socket, room_name):
        history = self.get_room_history(room_name)
        history_msg = f"HISTORY:{room_name}:{history}"
        client_socket.send(history_msg.encode('utf-8') + b'\n')

    def move_client_to_room(self, client_socket, color, username, old_room, new_room):
        if old_room in self.rooms and new_room in self.rooms:
            for c in self.rooms[old_room]:
                if c[0] == client_socket:
                    self.rooms[old_room].remove(c)
                    break
            self.rooms[new_room].append((client_socket, color, username, new_room))
            join_msg = f"{color}: [SYSTEM] {username} joined the room {new_room}."
            self.broadcast(self.rooms[new_room], join_msg, client_socket)
            self.send_userlist(new_room)
            self.send_userlist(old_room)
            self.send_room_history(client_socket, new_room)

    def handle_client(self, client_socket, color):
        username = 'Nameless'
        current_room = 'general'
        self.rooms['general'].append((client_socket, color, username, current_room))
        client_socket.send(f"COLOR:{color}\n".encode('utf-8'))
        available_rooms = ','.join(self.rooms.keys())
        client_socket.send(f"ROOMS:{available_rooms}\n".encode('utf-8'))
        self.send_userlist('general')
        self.send_room_history(client_socket, 'general')
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                lines = data.decode('utf-8').split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('USERNAME:'):
                        username = line.split(':', 1)[1]
                        for i, c in enumerate(self.rooms[current_room]):
                            if c[0] == client_socket:
                                self.rooms[current_room][i] = (client_socket, color, username, current_room)
                                break
                        join_msg = f"{color}: [SYSTEM] {username} joined the chat in the room {current_room}!"
                        self.broadcast(self.rooms[current_room], join_msg, client_socket)
                        self.send_userlist(current_room)
                    elif line.startswith('SWITCHROOM:'):
                        new_room = line.split(':', 1)[1]
                        if new_room in self.rooms and new_room != current_room:
                            old_room = current_room
                            leave_msg = f"{color}: [SYSTEM] {username} left the room {old_room}."
                            self.broadcast(self.rooms[old_room], leave_msg, client_socket)
                            self.move_client_to_room(client_socket, color, username, old_room, new_room)
                            current_room = new_room
                    elif line.startswith('FILE:'):
                        filename = line.split(':', 1)[1]
                        filesize_line = client_socket.recv(1024).decode('utf-8').strip()
                        if filesize_line.startswith('FILESIZE:'):
                            filesize = int(filesize_line.split(':', 1)[1])
                            file_data = b''
                            received = 0
                            while received < filesize:
                                chunk = client_socket.recv(min(4096, filesize - received))
                                if not chunk:
                                    break
                                file_data += chunk
                                received += len(chunk)
                            for c in self.rooms[current_room]:
                                if c[0] != client_socket:
                                    c[0].send(f"FILE:{filename}\n".encode('utf-8'))
                                    c[0].send(f"FILESIZE:{filesize}\n".encode('utf-8'))
                                    c[0].send(file_data)
                            file_msg = f"{color}: [{username}] sent file: {filename}"
                            self.broadcast(self.rooms[current_room], file_msg, client_socket)
                    else:
                        msg = f"{color}: {line}"
                        self.broadcast(self.rooms[current_room], msg, client_socket)
            except Exception as e:
                logging.error(f"Client handling error: {e}")
                break
        for room_name, clients in self.rooms.items():
            for c in clients:
                if c[0] == client_socket:
                    username = c[2]
                    clients.remove(c)
                    exit_msg = f"{color}: [SYSTEM] {username} left the chat."
                    self.broadcast(clients, exit_msg)
                    self.send_userlist(room_name)
                    break
        client_socket.close()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        logging.info("The server is running and listening....")
        while True:
            client_socket, _ = server_socket.accept()
            client_color = generate_color()
            thread = threading.Thread(target=self.handle_client, args=(client_socket, client_color))
            thread.start()

if __name__ == '__main__':
    server = ChatServer()
    server.start_server()