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
        #print(f"X: {ecc_shared.x} \nY: {ecc_shared.y}\n")
        return ecc_shared

    @staticmethod
    def recieve_exchange_keys(client, ecc_client_pb):
        ecc_pv = Encryption.create_pv_key()
        ecc_pb = Encryption.create_pub_key(ecc_pv)
        client.send(f"//HAHA->{ecc_pb.x},{ecc_pb.y}".encode('utf-8'))
        ecc_shared = ecc_client_pb * ecc_pv
        #print(f"X: {ecc_shared.x} \nY: {ecc_shared.y}\n")
        return ecc_shared

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
            #message = '{}: {}'.format(nickname, input('Message -> \033[11C')) ---COMMENTED---

            if ex_msg == 3:
                ecc_shared = Encryption.send_exchange_keys(client, nickname)
                ex_msg = 0

            if '\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1' in message:
                print('\033[F\r', end='')
                print('\033[K', end='')
            else:
                client.send(Encryption.encrypt(message, ecc_shared).encode('utf-8'))
                #client.send(message.encode('utf-8'))
                print('\033[K\r', end='')
                ex_msg += 1

            #print('\r', end='')
            if message == "//QUIT":
                return

    @staticmethod
    def recieve_messages(client):
        global nickname, WINDOW, AHK, ex_msg, ecc_shared

        while True:
            try:
                recieved = client.recv(1024).decode("utf-8")

                if "//KEY" in recieved and nickname not in recieved:
                        ecc_client_pb = recieved.split("->")[1].split(",")
                        ecc_client_pb = Encryption.force_create_point(int(ecc_client_pb[0]), int(ecc_client_pb[1]))
                        ecc_shared = Encryption.recieve_exchange_keys(client, ecc_client_pb)
                        ex_msg = 0
                elif recieved == "//NICKNAME" or recieved == "//CHATROOM" or "//HAHA" in recieved or ("//KEY" in recieved and nickname in recieved):
                    pass
                else:
                    recieved = Encryption.decrypt(recieved, ecc_shared)

                    if f"{nickname}: " in recieved:
                        print(f"\033[F\033[K{recieved}" + ' '*spaces) #MAYBE \r
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


##############################

class Interface:
    pass

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

    if Encryption.decrypt(client.recv(1024).decode('utf8'), ecc_shared) == "//NICKNAME":
        nickname = input("Enter your nickname -> ")
        client.send(Encryption.encrypt(nickname, ecc_shared).encode('utf-8'))

    if Encryption.decrypt(client.recv(1024).decode('utf-8') , ecc_shared) == "//CHATROOM":
        client.send(Encryption.encrypt("kurwa", ecc_shared).encode('utf-8'))

    print(f"\033[K{client.recv(1024).decode('utf-8')}")

    write_process = threading.Thread(target=Chat.send_message, args=(client,))
    recieve_messages = threading.Thread(target=Chat.recieve_messages, args=(client,))

    write_process.start()
    recieve_messages.start()

    sys.exit(0)
