import threading
import socket
import sys

ADDRESS = "127.0.0.1"
PORT = 9999

current_action = ""

def recieve():
    pass

def write():
    pass

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((ADDRESS, PORT))

if client.recv(1024).decode('utf-8') == "//NICKNAME":
    nickname = input("Enter your nickname -> ")
    client.send(nickname.encode('utf-8'))

print(f"{client.recv(1024).decode('utf-8')}")

receive_thread = threading.Thread(target=recieve)
write_thread = threading.Thread(target=write)

##############################

def recieve():
    global write_thread
    while True:
        try:
            recieved = client.recv(1024).decode("utf-8")

            if recieved == "//NICKNAME":
                pass
            else:
                print(f"\033[F{recieved}\n")
                write_thread.run()
        except:
            print("An ERROR occured!")
            client.close()
            return

##############################

def write():
    while True:
        current_action = "WRITE"
        print()
        message = input(str("Message -> "))
        client.send(f"{nickname}: {message}".encode('utf-8'))
        if message == "//QUIT":
            return

##############################

receive_thread = threading.Thread(target=recieve)
write_thread = threading.Thread(target=write)

receive_thread.start()
write_thread.start()

sys.exit(0)
