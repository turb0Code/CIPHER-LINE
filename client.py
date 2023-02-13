import threading
import socket

ADDRESS = "127.0.0.1"
PORT = 9999

current_action = ""

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((ADDRESS, PORT))

if client.recv(1024).decode('utf-8') == "//NICKNAME":
    nickname = input("Enter your nickname -> ")
    client.send(nickname.encode('utf-8'))

print(f"{client.recv(1024).decode('utf-8')}")

##############################

def receive():
    while True:
        try:
            recieved = client.recv(1024).decode("utf-8")

            if recieved == "//NICKNAME":
                pass
            else:
                print(f"\033[F\033[F{recieved}\n")
        except:
            print("An ERROR occured!")
            client.close()
            break

##############################

def write():
    while True:
        current_action = "WRITE"
        print("Message -> ")
        message = input()
        client.send(f"{nickname}: {message}".encode('utf-8'))

##############################

receive_thread = threading.Thread(target=receive)
write_thread = threading.Thread(target=write)

receive_thread.start()
write_thread.start()
