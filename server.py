import threading
import socket
import time
import secrets
import sys
import signal
import os
import hashlib

try:
    from tinyec import ec
    from tinyec import registry
    import pymongo
    from dotenv import dotenv_values, set_key, unset_key
except ImportError:
    print("\n" + "-"*20 + "\nLibraries NOT found! \nTry running file like this: 'python3 server.py -setup'" + "\n" + "-"*20 + "\nEXITING...")
    exit(0)

##############################

class SAFE_ZONE:

    @staticmethod
    def __get_key(time: str) -> int:
        element = time.split('.')[1]
        random = sum([int(digit) for digit in element]) % 100
        return random

    @staticmethod
    def __decrypt(data: str, key: int) -> str:
        result = bytes([byte ^ key for byte in bytes.fromhex(data)])
        return result.hex()

    @staticmethod
    def __version():
        try:
            return dotenv_values("version.env")
        except Exception as e:
            print("\n" + "-"*20 + "\nPlease chcek if you have version.env file in this directory!")
            exit(0)
            return

    @staticmethod
    def auth(data: str, time: int) -> bool:
        key = SAFE_ZONE.__get_key(time)
        decrypted = Encryption.hash_sha(SAFE_ZONE.__decrypt(data, key))
        if decrypted == SAFE_ZONE.__version()["KEY"]:
            return True
        return False # ---COMMENTED---
        #return True

##############################

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
    def encrypt(message: str, key) -> str:
        return ''.join(chr((ord(c) + key.x) % Encryption.modulo) for c in message)

    @staticmethod
    def decrypt(message: str, key) -> str:
        return ''.join(chr((ord(c) - key.x) % Encryption.modulo) for c in message)

    @staticmethod
    def hash_sha(data: str) -> str:
        sha256 = hashlib.sha256()
        sha256.update(data.encode("utf-8"))
        return sha256.hexdigest()

##############################

class Database:

    @staticmethod
    def connect():
        DB_CLIENT = pymongo.MongoClient("mongodb://localhost:27017/")

        DB = DB_CLIENT["database"]

        COLLECTION = DB["users"]

        if len(DB_CLIENT.list_database_names()) > 0:
            print("Connected with DATABASE...")

        return COLLECTION

    @staticmethod
    def start():
        Database.COLLECTION = Database.connect()

    @staticmethod
    def register(login: str, password: str, confirmation: str, user_id: str, token: str):
        if password != confirmation:
            return

        data = {"user_id" : user_id, "username" : login, "password" : password, "token" : token, "friends" : []}
        Database.COLLECTION.insert_one(data)

    @staticmethod
    def login(login: str, password: str) -> bool:
        result = Database.COLLECTION.find({"username" : login, "password" : password})
        try:
            if result[0]["username"] == login:
                return True
            else:
                return False
        except:
            return False

    @staticmethod
    def password_recovery(token: str, password: str):
        Database.COLLECTION.update_one({"token" : token}, { "$set" : {"password" : password}})
        print(Database.COLLECTION.find({"token" : token})[0])
        return

    @staticmethod
    def get_friends(username: str) -> list:
        result = Database.COLLECTION.find_one({"username" : username})
        friends = []
        for i in range(len(result["friends"])):
            friends.append(f"{result['friends'][i][1]} | {result['friends'][i][0]}")
        return friends

    @staticmethod
    def add_friend(username: str, friend_id: str, friend_name: str):
        result = Database.COLLECTION.find_one({"username" : friend_name, "user_id" : friend_id})
        try:
            if result["user_id"] == friend_id:
                Database.COLLECTION.update_one({"username" : username}, { "$push" : {"friends" : [friend_id, friend_name]}})
                print(f"Successfully added new friend {friend_name}")
                # TODO: SEND TO USER FRIEND LIST AND SEND SUCCESS
            else:
                print("USER NOT FOUND!")
                # TODO: SEND ERROR
        except:
            print("USER NOT FOUND!")
            # TODO: SEND ERROR

    @staticmethod
    def get_user_id(username: str) -> str:
        return Database.COLLECTION.find_one({"username" : username})["user_id"]

##############################

class Background:

    @staticmethod
    def ctrl_c_handler(sig, frame):
        print("\n" + "-"*20 + "\nThank's for using SAFE CHAT APP SERVER!")
        print("SERVER STOPPED...")
        print("EXITING...")
        exit(0)


##############################

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
    def auth_user(client, addr) -> bool:
        while True:

            recieved = client.recv(1023).decode('utf-8')

            if recieved == "//EXIT":
                print(f"Client {str(addr)} disconnected at the beginning.")
                client.close()
                return False
            else:
                if recieved == "//LOGIN":
                    recieved = client.recv(1024).decode('utf-8').split("^^")
                    login = recieved[0]
                    password = recieved[1]
                    if Database.login(login, password):
                        client.send("//OK".encode('utf-8'))
                        return True
                    else:
                        client.send("//ERROR[LOGIN]".encode('utf-8'))
                        continue
                elif recieved == "//REGISTER":
                    recieved = client.recv(1024).decode('utf-8')
                    if recieved != "//ERROR":
                        recieved = recieved.split("^^")
                        login = recieved[0]
                        password = recieved[1]
                        password_confirm = recieved[2]
                        user_id = recieved[3]
                        token = recieved[4]
                        Database.register(login, password, password_confirm, user_id, token)
                        return True
                    continue
                elif recieved == "//FORGOT":
                    token = client.recv(1024).decode('utf-8')
                    result = Database.COLLECTION.find_one({"token" : token})
                    try:
                        result["token"]
                        client.send("//OK".encode('utf-8'))
                        password = client.recv(1024).decode('utf-8')
                        Database.password_recovery(token, password)
                    except:
                        client.send("//INVALID".encode('utf-8'))
                    continue
                else:
                    client.close()
                    print("CLIENT INPUTED INVALID DATA! - DISCONNECTED")

    @staticmethod
    def generate_chat_id(first_user: str, second_user: str) -> int:
        first_output = 0
        second_output = 0

        if len(first_user) > len(second_user):
            lenght = len(second_user)
        else:
            lenght = len(first_user)

        for i in range(lenght):
            tmp = i * ord(first_user[i])
            first_output += tmp

        for i in range(lenght):
            tmp = i * ord(second_user[i])
            second_output += tmp

        return first_output * second_output

    @staticmethod
    def get_chat_id(client, nickname: str, ecc_shared) -> str:

        client.send(f"{Database.get_friends(nickname)}".encode('utf-8'))

        print(Database.get_friends(nickname))

        while True:

            recieved = client.recv(1024).decode('utf-8')

            if recieved == "//EXIT":
                print(f"User {nickname} disconnected!")
                client.close()
                return ""
            elif recieved == "//NEW[USER]":
                recieved = client.recv(1024).decode('utf-8').split("^^")
                Database.add_friend(nickname, recieved[0], recieved[1])
                client.send(f"{Database.get_friends(nickname)}".encode('utf-8'))
            elif recieved == "//PICK":
                recieved = Encryption.decrypt(client.recv(1024).decode('utf-8'), ecc_shared).split(" | ")[0]
                chat_id = Client.generate_chat_id(nickname, recieved)
                return chat_id
            else:
                client.close()
                return ""

    @staticmethod
    def connect():
        Database.start()

        while True:

            client, addr = server.accept()

            client.send("//AUTH".encode('utf-8'))
            auth = client.recv(1024).decode('utf-8').split("^^")
            if not SAFE_ZONE.auth(auth[0], auth[1]):
                print("Authentication failed! CLIENT DISCONNECTED!")
                client.close()
                continue

            ecc_pv = Encryption.create_pv_key()
            ecc_pb = Encryption.create_pub_key(ecc_pv)

            client.send(f"//KEY->{ecc_pb.x},{ecc_pb.y}".encode('utf-8'))
            ecc_user_pb = client.recv(1024).decode('utf-8').split(",")
            ecc_user_pb = Encryption.force_create_point(int(ecc_user_pb[0]), int(ecc_user_pb[1]))

            ecc_shared =  ecc_user_pb * ecc_pv

            if config["PROTECTED"] == "true":
                client.send(Encryption.encrypt("//PASSWORD", ecc_shared).encode('utf-8'))
                password = Encryption.decrypt(client.recv(1024).decode('utf-8'), ecc_shared)
                if password != config["PASSWORD"]:
                    client.send(Encryption.encrypt("//ERROR", ecc_shared).encode('utf-8'))
                    client.close()
                    continue

            client.send(Encryption.encrypt("//NICKNAME", ecc_shared).encode('utf-8'))
            if not Client.auth_user(client, addr):
                continue
            nickname = Encryption.decrypt(client.recv(1024).decode('utf-8'), ecc_shared)
            nicknames.append(nickname)

            thread = threading.Thread(target=Chat.handle, args=(client, nickname, addr, ecc_shared, ))
            thread_pool.append(thread)
            thread.start()

            del nickname, client, addr,
            time.sleep(0.5)

    @staticmethod
    def disconnect(client):
        pass

##############################

class Room:
    clients = []
    id = ""

    def __init__(self, id):
        self.id = id
        self.clients = []

    def add_client(self, client):
        self.clients.append(client)

    def del_client(self, client):
        self.clients.remove(client)

    def get_clients(self):
        return self.clients

##############################

class Chat:
    users = []
    name = ""
    id = ""

    def __init__(self, name):
        self.name = name
        self.id = 1

    @staticmethod
    def broadcast(message: str, chat_id_index: int):
        for client in rooms[chat_id_index].clients:
            client.client.send(message)

    @staticmethod
    def chatting(client, nickname: str) -> bool:
        while True:

            chat_id_index = [room.id for room in rooms].index(client.chat_id)

            try:
                recieved = client.client.recv(1024)
                if "//EXIT".encode('utf-8') in recieved:
                    Chat.broadcast(f"User {nickname} LEFT CHAT".encode('utf-8'), chat_id_index)
                    client.client.send("//EXIT".encode('utf-8'))
                    rooms[chat_id_index].del_client(client)
                    if len(rooms[chat_id_index].get_clients()) == 0:
                        rooms.remove(rooms[chat_id_index])
                    print(f"User {nickname} left chat.")
                    return True
                else:
                    Chat.broadcast(recieved, chat_id_index)
            except:
                print("DELETING USER")
                Chat.users.remove(client)
                client.client.close()
                nicknames.remove(nickname)
                Chat.broadcast(f"{nickname} LEFT CHAT".encode('utf-8'), chat_id_index)
                return False

    @staticmethod
    def handle(client, nickname: str, addr, ecc_shared):

        ecc_shared_user = ecc_shared

        while True:

            client.send(Encryption.encrypt(Database.get_user_id(nickname), ecc_shared_user).encode('utf-8'))

            client.send(Encryption.encrypt("//CHATROOM", ecc_shared_user).encode('utf-8'))
            chat_id = Client.get_chat_id(client, nickname, ecc_shared_user) #TODO: CHANGE IT!
            if chat_id == "":
                break
            new_client = Client(client, addr, nickname, chat_id)

            Chat.users.append(new_client)

            rooms_ids = [room.id for room in rooms]

            if new_client.chat_id in rooms_ids:
                room = rooms[rooms_ids.index(new_client.chat_id)]
                room.add_client(new_client)
                room_id_index = rooms_ids.index(new_client.chat_id)
            else:
                rooms.append(Room(new_client.chat_id))
                room_id_index = -1
                rooms[room_id_index].add_client(new_client)

            print(f"Connected with {str(addr)} as {nickname} to chat {new_client.chat_id}.")

            chat_id_index = [room.id for room in rooms].index(new_client.chat_id) # ---COMMENTED---

            Chat.broadcast(f"{nickname} JOINED CHAT.".encode('utf-8'), chat_id_index)

            if not Chat.chatting(new_client, nickname):
                break
        return

##############################

if __name__ == "__main__":

    print(r"""
   ___ ___ ___ _  _ ___ ___           _    ___ _  _ ___
  / __|_ _| _ \ || | __| _ \   ___   | |  |_ _| \| | __|
 | (__ | ||  _/ __ | _||   /  |___|  | |__ | || .` | _|
  \___|___|_|_|_||_|___|_|_\         |____|___|_|\_|___|
  ___ ___ __ __   __ __ ___
 / __| __| _ \ \ / / __| _ \
 \__ \ _||   /\ V /| _||   /
 |___/___|_|_\ \_/ |___|_|_\
""")


    signal.signal(signal.SIGINT, Background.ctrl_c_handler)

    if len(sys.argv) > 1 and sys.argv[1] == "-setup":
        print("\n" + "-"*20 + "\nSETUP STARTED")
        os.system("pip3 install pymongo")
        os.system("pip3 install tinyec")
        os.system("pip3 install python-dotenv")
        print("\n" + "-"*20 + "\nSERVER CONFIGURATION")
        try:
            config = dotenv_values("server.env")

        except FileNotFoundError:
            with open("server.env") as config:
                pass
        print("SPECIFY SERVER ADRESS: ")
        ADDRESS = input(str("> "))
        set_key("server.env", "ADDRESS", ADDRESS)
        print("SPECIFY SERVER PORT: ")
        PORT = input(str("> "))
        set_key("server.env", "PORT", PORT)
        print("SPECIFY SERVER PASSWORD: (press ENTER to SKIP without PASSWORD)")
        PASSWORD = input(str("> "))
        if len(PASSWORD) < 1:
            set_key("server.env", "PROTECTED", "false")
        else:
            set_key("server.env", "PROTECTED", "true")
            set_key("server.env", "PASSWORD", Encryption.hash_sha(PASSWORD))
        print("\n" + "-"*20 + "\nDONE...")
        exit(0)

    try:
        config = dotenv_values("server.env")

    except FileNotFoundError:
        print("\n" + "-"*20 + f"\nCONFIG file server.env NOT FOUND \nTry running 'python server.py -setup'")
        exit(0)

    ADDRESS = config["ADDRESS"]
    PORT = int(config["PORT"])

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
