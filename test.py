import select
import socket
import sys

# ustawienia serwera
HOST = ''
PORT = 9999

# tworzenie gniazda serwera
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(10)

# lista gniazd klientów
client_sockets = []
nickname_dict = {}

while True:
    # lista gniazd do odczytu
    read_sockets = client_sockets.copy()
    read_sockets.append(server_socket)

    # lista gniazd do zapisu
    write_sockets = []

    # lista błędów
    error_sockets = []

    # wywołanie metody select - czekamy na dane do odczytu lub zapisu
    readable, writable, exceptional = select.select(read_sockets, write_sockets, error_sockets)

    # obsługa zdarzeń
    for sock in readable:
        # nowe połączenie - gniazdo serwera
        if sock == server_socket:
            client_socket, client = 

            _address = server_socket.accept()
            client_sockets.append(client_socket)
            print('New client connected')
            # nowe dane do odczytu
        else:

            try:
                data = sock.recv(1024).decode('utf-8').strip()
                # klient wysyła wiadomość
                if data:
                    # jeśli to pierwsza wiadomość od klienta, to ustawiamy mu nickname
                    if sock not in nickname_dict:
                        nickname_dict[sock] = data
                        print(f'New client registered with nickname: {data}')
                    # w przeciwnym wypadku przesyłamy wiadomość do pozostałych klientów
                    else:
                        sender_nickname = nickname_dict[sock]
                        print(f'{sender_nickname}: {data}')

                for client in client_sockets:
                    if client != sock:
                        client.send(f'{sender_nickname}: {data}'.encode('utf-8'))
                    # brak danych - klient rozłączony
                    else:
                        client_sockets.remove(sock)
                    print(f'Client disconnected')

            except:
                client_sockets.remove(sock)
                print(f'Client disconnected')