import threading
import socket
import time
from tinyec import registry
import secrets

class Encryption:

    curve = registry.get_curve('brainpoolP256r1')

    @staticmethod
    def create_pv_key():
        return secrets.randbelow(Encryption.curve.field.n)

    @staticmethod
    def create_pub_key(pv_key):
        return pv_key * Encryption.curve.g

class Background:
    pass

class Client():
    client = ''
    ip = ''
    username = ''
    chat_id = ''

    def __init__(self, client, ip, username, chat_room):
        self.client = client
        self.ip = ip
        self.username = username
        self.chat_id = chat_room

    @staticmethod
    def connect():
        while True:

            client, addr = server.accept()

            client.send(f"//NICKNAME".encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            nicknames.append(nickname)

            client.send(f"//CHATROOM".encode('utf-8'))
            chat_id = client.recv(1024).decode('utf-8')
            new_client = Client(client, addr, nickname, chat_id)

            print(f"Connected with {str(addr)} as {nickname} to chat {new_client.chat_id}.")

            rooms_ids = [room.id for room in rooms]

            if new_client.chat_id in rooms_ids:
                print("SAME ROOM")
                room = rooms[rooms_ids.index(new_client.chat_id)]
                room.add_user(new_client)
                #room_id_index = rooms_ids.index(new_client.chat_id)#  TĘPA  KURWA  #
                room_id_index = 0
            else:
                print("NEW ROOM")
                rooms.append(Room(new_client.chat_id))
                room_id_index = -1
                rooms[room_id_index].add_user(new_client)
                print(rooms[room_id_index])

            print(f"SZMACIARZU TU SĄ USERZY: {rooms[0].clients}")

            Chat.broadcast(f"{nickname} JOINED CHAT".encode('utf-8'), room_id_index)

            Chat.users.append(new_client)

            thread = threading.Thread(target=Chat.handle, args=(new_client, ))
            thread_pool.append(thread)
            thread.start()

            new_client = ""

            del nickname, new_client, client, addr, room_id_index, rooms_ids
            time.sleep(0.5)

class Room:
    clients = []
    id = ""

    def __init__(self, id):
        self.id = id

    def add_user(self, client):
        self.clients.append(client)

    def del_client(self, client):
        self.clients.remove(client)

class Chat:
    users = []
    name = ""
    id = ""

    def __init__(self, name):
        self.name = name
        self.id = 1

    @staticmethod
    def broadcast(message, chat_id_index):
        print(message)
        print(len(rooms))

        for client in rooms[chat_id_index].clients:
            client.client.send(message)

    @staticmethod
    def handle(client):

        #self.users -> list of clients

        indexx = Chat.users.index(client)
        nickname = nicknames[indexx]

        while True:

            #chat_id_index = [room.id for room in rooms].index(client.chat_id) ---COMMENTED---
            chat_id_index = 0
            print(chat_id_index)

            try:
                recieved = client.client.recv(1024)
                if recieved == "//QUIT".encode('utf-8'):
                    Chat.users.remove(client)
                    rooms[client.chat_id].del_client(client)
                    client.close()
                    nicknames.remove(nickname)
                    Chat.broadcast(f"{nickname} LEFT CHAT".encode('utf-8'), chat_id_index)
                    break
                else:
                    Chat.broadcast(recieved, chat_id_index)
            except:
                print("DELETING USER")
                Chat.users.remove(client)
                client.client.close()
                nicknames.remove(nickname)
                Chat.broadcast(f"{nickname} LEFT CHAT".encode('utf-8'), chat_id_index)
                break


ADDRESS = "127.0.0.1"
PORT = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((ADDRESS, PORT))

clients = []
rooms = []

server.listen()

nicknames = []
thread_pool = []

print("-"*20)
print("Running server...")

Client.connect()
