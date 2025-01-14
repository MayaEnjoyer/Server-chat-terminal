import socket
import threading
import random
import os

def generate_color():
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#6d59b6', '#f39c12']
    return random.choice(colors)

rooms = {
    'general': [],
    'python': [],
    'random': [],
    'gaming': [],
    'music': []
}
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_log_file(room_name):
    return os.path.join(LOG_DIR, f"{room_name}.log")

def append_to_log(room_name, message):
    with open(get_log_file(room_name), 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def get_room_history(room_name):
    log_file = get_log_file(room_name)
    if not os.path.exists(log_file):
        return ''
    with open(log_file, 'r', encoding='utf-8') as f:
        return f.read()

def broadcast(room, message, sender_socket=None):
    for (client_socket, color, username, current_room) in room:
        if client_socket != sender_socket:
            try:
                client_socket.send((message + '\n').encode('utf-8'))
            except:
                pass

    if room:
        room_name = room[0][3]
        append_to_log(room_name, message)

def send_userlist(room_name):
    users = [c[2] for c in rooms[room_name]]
    userlist_msg = 'USERLIST:' + room_name + ':' + ','.join(users) + '\n'
    for (client_socket, color, username, current_room) in rooms[room_name]:
        try:
            client_socket.send(userlist_msg.encode('utf-8'))
        except:
            pass

def send_room_history(client_socket, room_name):
    history = get_room_history(room_name)
    history_msg = f"HISTORY:{room_name}:{history}"
    client_socket.send(history_msg.encode('utf-8') + b'\n')

def move_client_to_room(client_socket, color, username, old_room, new_room):
    if old_room in rooms and new_room in rooms:
        for c in rooms[old_room]:
            if c[0] == client_socket:
                rooms[old_room].remove(c)
                break
        rooms[new_room].append((client_socket, color, username, new_room))
        join_msg = f"{color}: [SYSTEM] {username} joined the room {new_room}."
        broadcast(rooms[new_room], join_msg, client_socket)
        send_userlist(new_room)
        send_userlist(old_room)
        send_room_history(client_socket, new_room)


def handle_client(client_socket, color):
    username = 'Nameless'
    current_room = 'general'
    rooms['general'].append((client_socket, color, username, current_room))
    client_socket.send(f"COLOR:{color}\n".encode('utf-8'))
    available_rooms = ','.join(rooms.keys())
    client_socket.send(f"ROOMS:{available_rooms}\n".encode('utf-8'))
    send_userlist('general')
    send_room_history(client_socket, 'general')

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
                    for i, c in enumerate(rooms[current_room]):
                        if c[0] == client_socket:
                            rooms[current_room][i] = (client_socket, color, username, current_room)
                            break
                    join_msg = f"{color}: [SYSTEM] {username} joined the chat in the room {current_room}!"
                    broadcast(rooms[current_room], join_msg, client_socket)
                    send_userlist(current_room)

                elif line.startswith('SWITCHROOM:'):
                    new_room = line.split(':', 1)[1]
                    if new_room in rooms and new_room != current_room:
                        old_room = current_room
                        leave_msg = f"{color}: [SYSTEM] {username} left the room {old_room}."
                        broadcast(rooms[old_room], leave_msg, client_socket)
                        move_client_to_room(client_socket, color, username, old_room, new_room)
                        current_room = new_room

                elif line.startswith('FILE:'):
                    filename = line.split(':', 1)[1]
                    filesize_line = client_socket.recv(1024).decode('utf-8')
                    filesize_line = filesize_line.strip()
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
                        for (c_socket, c_color, c_username, c_room) in rooms[current_room]:
                            if c_socket != client_socket:
                                c_socket.send(f"FILE:{filename}\n".encode('utf-8'))
                                c_socket.send(f"FILESIZE:{filesize}\n".encode('utf-8'))
                                c_socket.send(file_data)
                        file_msg = f"{color}: [{username}] sent file: {filename}"
                        broadcast(rooms[current_room], file_msg, client_socket)
                else:
                    msg = f"{color}: {line}"
                    broadcast(rooms[current_room], msg, client_socket)
        except:
            break

    for room_name, client_list in rooms.items():
        for c in client_list:
            if c[0] == client_socket:
                username = c[2]
                client_list.remove(c)
                exit_msg = f"{color}: [SYSTEM] {username} left the chat."
                broadcast(client_list, exit_msg)
                send_userlist(room_name)
                break
    client_socket.close()

