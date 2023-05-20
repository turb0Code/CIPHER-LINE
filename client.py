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
import secrets

##############################

class Encryption:

    curve = registry.get_curve('brainpoolP256r1')

    @staticmethod
    def create_pv_key():
        return secrets.randbelow(Encryption.curve.field.n)

    @staticmethod
    def create_pub_key(pv_key):
        return pv_key * Encryption.curve.g

##############################

class Background:
    pass

##############################

class Chat:
    AHK = AHK()
    WINDOW = AHK.active_window

    @staticmethod
    def send_message(client):
        while True:
            message = '{}: {}'.format(nickname, input('Message -> \033[0;11'))

            if "\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1\n" not in message:
                client.send(message.encode('utf-8'))

            print('\r ', end='')
            if message == "//QUIT":
                return

    @staticmethod
    def recieve_messages(client):
        global nickname, WINDOW, AHK

        while True:
            try:
                recieved = client.recv(1024).decode("utf-8")
                spaces = 11-len(recieved)
                if 11-len(recieved) <= 0:
                    spaces = 0

                if recieved == "//NICKNAME" or recieved == "//CHATROOM":
                    pass
                else:
                    if f"{nickname}: " in recieved:
                        print(f"\033[F\033[K{recieved}" + ' '*spaces)
                    else:
                        print(f"\033[F\033[K{recieved}" + ' '*spaces)
                        if not Chat.WINDOW.exists:
                            Chat.WINDOW.activate()
                            Chat.AHK.type("\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1\n")
                            Chat.WINDOW.minimize()

                        Chat.WINDOW.activate()
                        Chat.AHK.type('\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1\n')
            except:
                print("An ERROR occured!")
                client.close()
                return


##############################

if __name__ == "__main__":

    ADDRESS = "127.0.0.1"
    PORT = 9999

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ADDRESS, PORT))

    if client.recv(1024).decode('utf-8') == "//NICKNAME":
        nickname = input("Enter your nickname -> ")
        client.send(nickname.encode('utf-8'))

    if client.recv(1024).decode('utf-8') == "//CHATROOM":
        print("TĘPA DZIDA")
        client.send("kurwa".encode('utf-8'))

    print(f"{client.recv(1024).decode('utf-8')}")

    write_process = threading.Thread(target=Chat.send_message, args=(client,))
    recieve_messages = threading.Thread(target=Chat.recieve_messages, args=(client,))

    write_process.start()
    recieve_messages.start()

    sys.exit(0)
