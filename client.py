"""
pip install ahk
pip install ahk[binary]
pip install tinyec
"""

import threading
import socket
import sys
from ahk import AHK
from ahk.window import Window
from tinyec import registry
from tinyec import ec
import secrets
import hashlib
import random

##############################

class SAFE_ZONE:
    pass

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
    def encrypt(message, key):
        return ''.join(chr((ord(c) + key.x) % Encryption.modulo) for c in message)

    @staticmethod
    def decrypt(message, key):
        return ''.join(chr((ord(c) - key.x) % Encryption.modulo) for c in message)

    @staticmethod
    def send_exchange_keys(client, nickname):
        ecc_pv = Encryption.create_pv_key()
        ecc_pb = Encryption.create_pub_key(ecc_pv)
        client.send(f"//KEY[{nickname}]->{ecc_pb.x},{ecc_pb.y}".encode('utf-8'))
        ecc_user_pb = client.recv(1024).decode('utf-8').split("->")[1].split(",")
        ecc_user_pb = Encryption.force_create_point(int(ecc_user_pb[0]), int(ecc_user_pb[1]))
        ecc_shared = ecc_pv * ecc_user_pb
        return ecc_shared

    @staticmethod
    def recieve_exchange_keys(client, ecc_client_pb):
        ecc_pv = Encryption.create_pv_key()
        ecc_pb = Encryption.create_pub_key(ecc_pv)
        client.send(f"//RES->{ecc_pb.x},{ecc_pb.y}".encode('utf-8'))
        ecc_shared = ecc_client_pb * ecc_pv
        return ecc_shared

    @staticmethod
    def hash_sha(data):
        sha256 = hashlib.sha256()
        sha256.update(data.encode("utf-8"))
        return sha256.hexdigest()

##############################

class Client_side:

    @staticmethod
    def create_token():
        result = ""

        for _ in range(12):
            choice = random.randint(0, 100)
            if choice <= 25:
                char = chr(random.randint(ord("a"), ord("z")))
            elif choice <= 50:
                char = chr(random.randint(ord("A"), ord("Z")))
            else:
                char = str(random.randint(0, 10) % 10)
            result += char
        return result

    @staticmethod
    def create_id(login):

        def checksum(root, start, end):
            output = 0
            for x in root[start:end]:
                output += int(x) * 2
            return output % 10

        result = ""

        for i in range(8):
            if i >= len(login) - 1:
                result += (str(random.randint(0, 1000) % 10))
            else:
                if i % 2 == 0:
                    result += (str((ord(login[i] ) + random.randint(0, 1000)) % 10))
                else:
                    result += (str(ord(login[i] ) % 10))

        checksum_1 = checksum(result, 0, 4)
        checksum_2 = checksum(result, 4, 8)

        return f"{result[0:4]}-{result[4:8]}-{checksum_1}{checksum_2}"

    @staticmethod
    def disconnect(client):
        print("\n" + "-"*20 + "\nEXITING...")
        client.send("//EXIT".encode('utf-8'))
        client.close()
        exit(0)

    @staticmethod
    def login(client):
        client.send("//LOGIN".encode('utf-8'))
        print("\n" + "-"*20 + "\nLOGIN")
        login = input(str("LOGIN -> "))
        password = input(str("PASSWORD -> "))
        client.send(f"{login}^^{Encryption.hash_sha(password)}".encode('utf-8'))
        return login

    @staticmethod
    def register(client):
        client.send("//REGISTER".encode('utf-8'))
        print("\n" + "-"*20 + "\nSIGN UP")
        login = input(str("LOGIN -> "))
        password = Encryption.hash_sha(input(str("PASS -> ")))
        password_confirm = Encryption.hash_sha(input(str("CONFIRM PASS -> ")))
        user_id = Client_side.create_id(login)
        token = Client_side.create_token()
        if password != password_confirm:
            print("PASSWORD AND CONFIRMATION DOES NOT MATCH!")
            client.send(f"//ERROR".encode('utf-8'))
            return ""
        else:
            client.send(f"{login}^^{password}^^{password_confirm}^^{user_id}^^{Encryption.hash_sha(token)}".encode('utf-8'))
        print(f"THIS IS YOUR RECOVERY KEY, NEVER FORGET IT:  {token}")
        return login

    @staticmethod
    def recover_password(client):
        client.send("//FORGOT".encode('utf-8'))
        print("\n" + "-"*20 + "\nPASSWORD RECOVERY")
        token = input(str("TOKEN -> "))
        client.send(f"{Encryption.hash_sha(token)}".encode('utf-8'))
        match client.recv(1024).decode("utf-8"):
            case "//OK":
                password = Encryption.hash_sha(input(str("NEW PASSWORD -> ")))
                password_confirm = Encryption.hash_sha(input(str("CONFIRM PASSWORD -> ")))
                if password != password_confirm:
                    print("PASSWORD AND CONFIRMATION DOES NOT MATCH!")
                    return False
                else:
                    client.send(f"{password}".encode('utf-8'))
            case "//INVALID":
                print("INVALID TOKEN!")
                return False
        return True


##############################

class Background:
    pass

##############################

class Chat:
    AHK = AHK()
    WINDOW = AHK.active_window

    @staticmethod
    def send_message(client):
        global ex_msg, ecc_shared

        while True:
            message = '{}: {}'.format(nickname, input('Message -> \033[0;11'))

            if '\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1' in message:
                print('\033[F\r', end='')
                print('\033[K', end='')
            elif "//EXIT" in message:
                #client.send(Encryption.encrypt(f"USER {nickname} LEFT CHAT", ecc_shared).encode('utf-8')) --COMMMENTED--- THIS SHOULD BE WORKING
                client.send("//EXIT".encode('utf-8')) #NOT ENCRYPTED!!! (FOR SURE)
                break
            else:

                if ex_msg == 3:
                    ecc_shared = Encryption.send_exchange_keys(client, nickname)
                    ex_msg = 0

                client.send(Encryption.encrypt(message, ecc_shared).encode('utf-8'))
                print('\033[K\r', end='')
                ex_msg += 1
        return

    @staticmethod
    def recieve_messages(client):
        global nickname, WINDOW, AHK, ex_msg, ecc_shared

        while True:
            try:
                recieved = client.recv(1024).decode('utf-8')

                if "//KEY" in recieved and nickname not in recieved:
                    ecc_client_pb = recieved.split("->")[1].split(",")
                    ecc_client_pb = Encryption.force_create_point(int(ecc_client_pb[0]), int(ecc_client_pb[1]))
                    ecc_shared = Encryption.recieve_exchange_keys(client, ecc_client_pb)
                    ex_msg = 0
                elif "//EXIT" in recieved:
                    break
                elif recieved == "//NICKNAME" or recieved == "//CHATROOM" or "//RES" in recieved or ("//KEY" in recieved and nickname in recieved):
                    pass
                else:
                    recieved = Encryption.decrypt(recieved, ecc_shared)

                    if f"{nickname}: " in recieved:
                        print(f"\033[F\033[K{recieved}" + ' '*spaces)
                    else:
                        spaces = 11-len(recieved)
                        if 11-len(recieved) <= 0:
                            spaces = 0
                        print(f"\r\033[K{recieved}" + ' '*spaces)
                        del recieved

                        if not Chat.WINDOW.exists:
                            Chat.WINDOW.activate()
                            Chat.AHK.type("\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1\n")
                            Chat.WINDOW.minimize()

                        Chat.WINDOW.activate()
                        Chat.AHK.type('\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1\n')
                        ex_msg += 1

            except:
                print("An ERROR occured!")
                client.close()
                return
        return


##############################

class Interface:

    @staticmethod
    def welcome(client):
        global ecc_shared

        print(r"""
   _____         ______ ______        _____ _    _       _______             _____  _____
  / ____|  /\   |  ____|  ____|      / ____| |  | |   /\|__   __|      /\   |  __ \|  __ \
 | (___   /  \  | |__  | |__        | |    | |__| |  /  \  | |        /  \  | |__) | |__) |
  \___ \ / /\ \ |  __| |  __|       | |    |  __  | / /\ \ | |       / /\ \ |  ___/|  ___/
  ____) / ____ \| |    | |____      | |____| |  | |/ ____ \| |      / ____ \| |    | |
 |_____/_/    \_\_|    |______|      \_____|_|  |_/_/    \_\_|     /_/    \_\_|    |_|
 """)

        while True:
            print("\n" + "-"*20 + "\nCHOOSE OPTION: " + "\n1. Login \n2. Register \n3. Forgotten password \n4. EXIT")
            option = int(input(str("> ")))

            match option:
                case 1:
                    login = Client_side.login(client)
                    if client.recv(1024).decode('utf-8') == "//OK":
                        break
                    else:
                        print("INVALID LOGIN OR PASSWORD!")
                        continue

                case 2:
                    login = Client_side.register(client)
                    if login == "":
                        continue
                    break

                case 3:
                    Client_side.recover_password(client)
                    continue

                case 4:
                    Client_side.disconnect()

                case default:
                    print("WRONG OPTION!")
                    continue
        return login

    @staticmethod
    def choose_chat(client, nickname):

        friends = eval(client.recv(1024).decode('utf-8')) #recieve

        while True:
            print("\n" + "-"*20 + "\nPICK CHAT:")
            i = 1
            for _ in range(len(friends)):
                print(f"{i}. {friends[_]}")
                i += 1

            print(f"{i}. NEW USER \n{i+1}. SETTINGS \n{i+2}. EXIT")
            choice = int(input(str("> ")))

            if choice == i+2:
                print("\n" + "-"*20 +"\nEXITING...")
                client.send("//EXIT".encode('utf-8'))
                exit(0)
            elif choice == i+1:
                print("\n" + "-"*20 +"\nSETTINGS")
                break
            elif choice == i:
                print("\n" + "-"*20 +"ADD NEW USER")
                client.send("//NEW[USER]".encode('utf-8'))
                friend_name = input(str("FRIEND LOGIN -> "))
                friend_id = input(str("FRIEND ID -> "))
                client.send(f"{friend_id}^^{friend_name}".encode('utf-8'))
                friends = eval(client.recv(1024).decode('utf-8'))
                continue
            elif choice < i and choice >= 1:
                print("\n" + "-"*20 + f"\nChatting with user {friends[choice-1]}")
                client.send("//PICK".encode('utf-8'))
                chat = friends[choice-1]  # TODO: send it to server
                break
            else:
                print("\nINVALID OPTION!")
        return chat

##############################

if __name__ == "__main__":

    ADDRESS = "127.0.0.1"
    PORT = 9999

    ex_msg = 2 # ex_msg -> exchanged messages

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ADDRESS, PORT))

    ecc_pv = Encryption.create_pv_key()
    ecc_pb = Encryption.create_pub_key(ecc_pv)

    request = client.recv(1024).decode('utf8')

    if "//KEY" in request:
        ecc_server_pb = request.split("->")[1].split(",")
        ecc_server_pb = Encryption.force_create_point(int(ecc_server_pb[0]), int(ecc_server_pb[1]))
        client.send(f"{ecc_pb.x},{ecc_pb.y}".encode('utf-8'))

        ecc_shared = ecc_server_pb * ecc_pv

        print(f"X: {ecc_shared.x} \nY: {ecc_shared.y}")

    nickname = Interface.welcome(client)

    if Encryption.decrypt(client.recv(1024).decode('utf8'), ecc_shared) == "//NICKNAME":
        client.send(Encryption.encrypt(nickname, ecc_shared).encode('utf-8'))

    ecc_shared_server = ecc_shared

    while True:

        recieved = Encryption.decrypt(client.recv(1024).decode('utf-8') , ecc_shared_server)

        if "//CHATROOM" in recieved:
            print("CHOOSE CHATTT")
            chat_room = Interface.choose_chat(client, nickname)
            client.send(Encryption.encrypt(chat_room, ecc_shared_server).encode('utf-8'))

        print(f"\033[K{client.recv(1024).decode('utf-8')}")

        write_process = threading.Thread(target=Chat.send_message, args=(client,))
        recieve_messages = threading.Thread(target=Chat.recieve_messages, args=(client,))

        write_process.start()
        recieve_messages.start()

        write_process.join()
        recieve_messages.join()

        chat_room = ""

    exit(0)
