"""
pip install ahk
pip install ahk[binary]
pip install tinyec
"""

import threading
import socket
import sys
import multiprocessing
from ahk import AHK
from ahk.window import Window

##############################

ADDRESS = "127.0.0.1"
PORT = 9999

##############################

PROCESS = multiprocessing.current_process()
AHK = AHK()
#WINDOW = Window.from_pid(AHK, pid=str(PROCESS.pid))
WINDOW = AHK.active_window

##############################

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((ADDRESS, PORT))

##############################

if client.recv(1024).decode('utf-8') == "//NICKNAME":
    nickname = input("Enter your nickname -> ")
    client.send(nickname.encode('utf-8'))

print(f"{client.recv(1024).decode('utf-8')}")

def recieve_messages():
    pass

def write():
    pass

write_process = threading.Thread(target=write)
recieve_messages = threading.Thread(target=recieve_messages)

##############################

def recieve_messages():
    global nickname, WINDOW, AHK

    while True:
        try:
            recieved = client.recv(1024).decode("utf-8")
            spaces = 11-len(recieved)
            if 11-len(recieved) <= 0:
                spaces = 0

            if recieved == "//NICKNAME":
                pass
            else:
                if f"{nickname}: " in recieved:
                    print(f"\033[F\033[K{recieved}" + ' '*spaces)
                else:
                    print(f"\033[F\033[K{recieved}" + ' '*spaces)
                    if not WINDOW.exists:
                        WINDOW.activate()
                        AHK.type("\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1\n")
                        WINDOW.minimize()

                    WINDOW.activate()
                    AHK.type("\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1\n")
        except:
            print("An ERROR occured!")
            client.close()
            return

##############################

def write():
    while True:
        message = '{}: {}'.format(nickname, input('Message -> \033[0;11'))

        if "\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1" not in message:
            client.send(message.encode('utf-8'))

        print('\r ', end='')
        if message == "//QUIT":
            return


##############################

if __name__ == "__main__":

    write_process = threading.Thread(target=write)
    recieve_messages = threading.Thread(target=recieve_messages)

    write_process.start()
    recieve_messages.start()

    sys.exit(0)
