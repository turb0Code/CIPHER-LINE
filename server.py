import threading
import socket
import time
from tinyec import registry
import secrets
from tinyec import ec
import sys

class Encryption:

    curve = registry.get_curve('brainpoolP256r1')
    modulo = sys.maxunicode

    @staticmethod
    def create_pv_key():
        return secrets.randbelow(Encryption.curve.field.n)

    @staticmethod
    def create_pub_key(pv_key):
        return pv_key * Encryption.curve.g

    @staticmethod
    def force_create_point(x, y):
        return ec.Point(Encryption.curve, x, y)

    @staticmethod
    def encrypt(message, key):
        return ''.join(chr((ord(c) + key.x) % Encryption.modulo) for c in message)

    @staticmethod
    def decrypt(message, key):
        return ''.join(chr((ord(c) - key.x) % Encryption.modulo) for c in message)

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

            ecc_pv = Encryption.create_pv_key()
            ecc_pb = Encryption.create_pub_key(ecc_pv)

            client.send(f"//KEY->{ecc_pb.x},{ecc_pb.y}".encode('utf-8'))
            ecc_user_pb = client.recv(1024).decode('utf-8').split(",")
            ecc_user_pb = Encryption.force_create_point(int(ecc_user_pb[0]), int(ecc_user_pb[1]))

            ecc_shared =  ecc_user_pb * ecc_pv
            print(f"X: {ecc_shared.x} \nY: {ecc_shared.y}")

            client.send(Encryption.encrypt("//NICKNAME", ecc_shared).encode('utf-8'))
            nickname = Encryption.decrypt(client.recv(1024).decode('utf-8'), ecc_shared)
            nicknames.append(nickname)

            client.send(Encryption.encrypt("//CHATROOM", ecc_shared).encode('utf-8'))
            chat_id = Encryption.decrypt(client.recv(1024).decode('utf-8'), ecc_shared)
            new_client = Client(client, addr, nickname, chat_id)

            print(f"Connected with {str(addr)} as {nickname} to chat {new_client.chat_id}.")

            rooms_ids = [room.id for room in rooms]

            if new_client.chat_id in rooms_ids:
                room = rooms[rooms_ids.index(new_client.chat_id)]
                room.add_user(new_client)
                #room_id_index = rooms_ids.index(new_client.chat_id) ---COMMENTED---
                room_id_index = 0
            else:
                rooms.append(Room(new_client.chat_id))
                room_id_index = -1
                rooms[room_id_index].add_user(new_client)

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
        print(f'MSG: {message}')
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
