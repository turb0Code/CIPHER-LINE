import threading
import socket
import time

ADDRESS = "127.0.0.1"
PORT = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((ADDRESS, PORT))

server.listen()

clients = []
nicknames = []

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    indexx = clients.index(client)
    nickname = nicknames[indexx]
    while True:
        try:
            recieved = client.recv(1024)
            if recieved == "//QUIT".encode('utf-8'):
                clients.remove(client)
                client.close()
                nicknames.remove(nickname)
                broadcast(f"{nickname} LEFT CHAT".encode('utf-8'))
                break
            else:
                broadcast(recieved)
        except:
            clients.remove(client)
            client.close()
            nicknames.remove(nickname)
            broadcast(f"{nickname} LEFT CHAT".encode('utf-8'))
            break

def connect():
    while True:
        client, addr = server.accept()
        client.send(f"//NICKNAME".encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)

        print(f"Connected with {str(addr)} as {nickname}.")

        broadcast(f"{nickname} JOINED CHAT".encode('utf-8'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()
        time.sleep(0.5)

print("-"*20)
print("Running server...")
connect()
