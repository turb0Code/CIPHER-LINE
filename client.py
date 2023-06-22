"""
pip install ahk
pip install ahk[binary]
pip install tinyec
"""

import threading
import socket
import sys
import secrets
import hashlib
import random
import os
import time

try:
    from ahk import AHK
    from ahk.window import Window
    from tinyec import registry
    from tinyec import ec
except ImportError:
    print("\n" + "-"*20 + "\nLibraries NOT found! \nTry running file like this: 'python3 client.py -setup'" + "\n" + "-"*20 + "\nEXITING...")
    exit(0)

##############################

class SAFE_ZONE:

    @staticmethod
    def __file_hash() -> str:
        with open(__file__, 'rb') as file:
            sha256 = hashlib.sha256()
            while chunk := file.read(4096):
                sha256.update(chunk)
            file_hash = sha256.hexdigest()
        return file_hash

    @staticmethod
    def __random(time: str) -> int:
        element = time.split('.')[1]
        random = sum([int(digit) for digit in element]) % 100
        return random #it's random for sure :)

    @staticmethod
    def __encrypt(data: str, key: int) -> str:
        result = bytes([byte ^ key for byte in bytes.fromhex(data)])
        return result.hex()

    @staticmethod
    def auth(client):
        current_time = str(time.time())
        Chat.send(client, f"{SAFE_ZONE.__encrypt(SAFE_ZONE.__file_hash(), SAFE_ZONE.__random(current_time))}^^{current_time}")
        return


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
    def send_exchange_keys(client, nickname: str):
        ecc_pv = Encryption.create_pv_key()
        ecc_pb = Encryption.create_pub_key(ecc_pv)
        Chat.send(client, f"//KEY[{nickname}]->{ecc_pb.x},{ecc_pb.y}")
        ecc_user_pb = client.recv(1024).decode('utf-8').split("->")[1].split(",")
        ecc_user_pb = Encryption.force_create_point(int(ecc_user_pb[0]), int(ecc_user_pb[1]))
        ecc_shared = ecc_pv * ecc_user_pb
        return ecc_shared

    @staticmethod
    def recieve_exchange_keys(client, ecc_client_pb):
        ecc_pv = Encryption.create_pv_key()
        ecc_pb = Encryption.create_pub_key(ecc_pv)
        Chat.send(client, f"//RES->{ecc_pb.x},{ecc_pb.y}")
        ecc_shared = ecc_client_pb * ecc_pv
        return ecc_shared

    @staticmethod
    def hash_sha(data: str) -> str:
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
    def checksum(root: str, start: int, end: int) -> int:
        output = 0
        for x in root[start:end]:
            output += int(x) * 2
        return output % 10

    @staticmethod
    def create_id(login: str) -> str:

        result = ""

        for i in range(8):
            if i >= len(login) - 1:
                result += (str(random.randint(0, 1000) % 10))
            else:
                if i % 2 == 0:
                    result += (str((ord(login[i] ) + random.randint(0, 1000)) % 10))
                else:
                    result += (str(ord(login[i] ) % 10))

        checksum_1 = Client_side.checksum(result, 0, 4)
        checksum_2 = Client_side.checksum(result, 4, 8)

        return f"{result[0:4]}-{result[4:8]}-{checksum_1}{checksum_2}"

    @staticmethod
    def disconnect(client):
        print("\n" + "-"*20 + "\nEXITING...")
        Chat.send(client, "//EXIT")
        client.close()
        exit(0)

    @staticmethod
    def login(client) -> str:
        Chat.send(client, "//LOGIN")
        print("\n" + "-"*20 + "\nLOGIN")
        login = input(str("LOGIN -> ")).strip()
        password = input(str("PASSWORD -> ")).strip()
        client.send(f"{login}^^{Encryption.hash_sha(password)}".encode('utf-8'))
        return login

    @staticmethod
    def register(client) -> str:
        Chat.send(client, "//REGISTER")
        print("\n" + "-"*20 + "\nSIGN UP")
        login = input(str("LOGIN -> ").strip())
        password = Encryption.hash_sha(input(str("PASS -> ")).strip())
        password_confirm = Encryption.hash_sha(input(str("CONFIRM PASS -> ")).strip())
        user_id = Client_side.create_id(login)
        token = Client_side.create_token()
        if password != password_confirm:
            print("PASSWORD AND CONFIRMATION DOES NOT MATCH!")
            client.send(f"//ERROR".encode('utf-8'))
            return ""
        else:
            Chat.send(client, f"{login}^^{password}^^{password_confirm}^^{user_id}^^{Encryption.hash_sha(token)}")
        print(f"THIS IS YOUR RECOVERY KEY, NEVER FORGET IT:  {token}")
        return login

    @staticmethod
    def recover_password(client) -> bool:
        Chat.send(client, "//FORGOT")
        print("\n" + "-"*20 + "\nPASSWORD RECOVERY")
        token = input(str("TOKEN -> ")).strip()
        Chat.send(client, f"{Encryption.hash_sha(token)}")
        match client.recv(1024).decode("utf-8"):
            case "//OK":
                password = Encryption.hash_sha(input(str("NEW PASSWORD -> ")).strip())
                password_confirm = Encryption.hash_sha(input(str("CONFIRM PASSWORD -> ")).strip())
                if password != password_confirm:
                    print("PASSWORD AND CONFIRMATION DOES NOT MATCH!")
                    return False
                else:
                    Chat.send(client, f"{password}")
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
    def send(client, message, encrypt=False, ecc_shared=""):
        try:
            if encrypt:
                client.send(Encryption.encrypt(message, ecc_shared).encode('utf-8'))
            else:
                client.send(message.encode('utf-8'))
        except Exception as e:
            print("\n" + "-"*20 + f"\nAn ERROR OCCURED - {e}")
            Client_side.disconnect(client)

    @staticmethod
    def receive(client):
        pass

    @staticmethod
    def send_message(client):
        global ex_msg, ecc_shared

        try:
            while True:
                try:
                    message = '{}: {}'.format(nickname, input('Message -> \033[0;11'))

                except EOFError:
                    Chat.send(client, "//EXIT") #NOT ENCRYPTED!!!! (FOR SURE)
                    break

                except KeyboardInterrupt:
                    Chat.send(client, "//EXIT") #NOT ENCRYPTED!!!! (FOR SURE)
                    print("\n\n Please EXIT SAFELY by typing //EXIT")
                    break

                if '\uCBA0\uCBBC\uCC9F\uCD95\uCDB7\uCE8C\uCF97\uCFA1' in message:
                    print('\033[F\r', end='')
                    #print('\033[F\r', end='')
                    print('\033[K', end='')
                elif "//EXIT" in message:
                    Chat.send(client, "//EXIT") #NOT ENCRYPTED!!!! (FOR SURE)
                    break
                else:

                    if ex_msg == 3:
                        ecc_shared = Encryption.send_exchange_keys(client, nickname)
                        ex_msg = 0

                    Chat.send(client, message, True, ecc_shared)
                    print('\033[K\r', end='')
                    ex_msg += 1
            return

        except Exception as e:
            print("\n" + "-"*20 + f"\nAn ERROR occured! - {e}")
            Client_side.disconnect(client)

    @staticmethod
    def recieve_messages(client):
        global nickname, WINDOW, AHK, ex_msg, ecc_shared

        try:
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
                    elif "LEFT CHAT" in recieved:
                        if nickname in recieved:
                            print(recieved)
                        else:
                            spaces = 11-len(recieved)
                            if 11-len(recieved) <= 0:
                                spaces = 0
                            print(f"\r\033[K{recieved}" + ' '*spaces)
                            print("\nType //EXIT to EXIT...")
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

                except KeyboardInterrupt:
                    continue

                except:
                    print("An ERROR occured!")
                    client.close()
                    return
            return
        except Exception as e:
            print("\n" + "-"*20 + f"\nAn ERROR occured! - {e}")
            Client_side.disconnect(client)


##############################

class Interface:

    @staticmethod
    def display_logo():
        print(r"""
   _____         ______ ______        _____ _    _       _______             _____  _____
  / ____|  /\   |  ____|  ____|      / ____| |  | |   /\|__   __|      /\   |  __ \|  __ \
 | (___   /  \  | |__  | |__        | |    | |__| |  /  \  | |        /  \  | |__) | |__) |
  \___ \ / /\ \ |  __| |  __|       | |    |  __  | / /\ \ | |       / /\ \ |  ___/|  ___/
  ____) / ____ \| |    | |____      | |____| |  | |/ ____ \| |      / ____ \| |    | |
 |_____/_/    \_\_|    |______|      \_____|_|  |_/_/    \_\_|     /_/    \_\_|    |_|
 """)
        return

    @staticmethod
    def clear_console():
        os.system("cls")

    @staticmethod
    def welcome(client):
        global ecc_shared

        while True:
            try:
                print("\n" + "-"*20 + "\nCHOOSE OPTION: " + "\n1. Login \n2. Register \n3. Forgotten password \n4. EXIT")
                option = int(input(str("> ")).strip())

            except KeyboardInterrupt:
                print("\n\nPlease next time EXIT SAFELY")
                option = 4

            except Exception as e:
                print("\n" + "-"*20 + f"\nAn ERROR occured! - {e}")
                Client_side.disconnect(client)

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
                    Client_side.disconnect(client)

                case default:
                    print("WRONG OPTION!")
                    continue
        return login

    @staticmethod
    def choose_chat(client, nickname: str) -> str:

        friends = eval(client.recv(1024).decode('utf-8'))

        while True:
            Interface.clear_console()
            Interface.display_logo()
            print("-"*20 + f"\nLOGGED IN AS: {nickname}" + "\nPICK CHAT:")
            i = 1
            for _ in range(len(friends)):
                print(f"{i}. {friends[_]}")
                i += 1

            try:
                print(f"{i}. NEW USER \n{i+1}. SETTINGS \n{i+2}. EXIT")
                choice = int(input(str("> ")).strip())

            except KeyboardInterrupt:
                print("\n\nPlease next time EXIT SAFELY")
                choice = i+2

            except Exception as e:
                print("\n" + "-"*20 + f"An ERROR occured! - {e}")
                Client_side.disconnect(client)

            if choice == i+2:
                print("\n" + "-"*20 +"\nEXITING...")
                Chat.send(client, "//EXIT")
                exit(0)
            elif choice == i+1:
                print("\n" + "-"*20 +"\nSETTINGS")
                break
            elif choice == i:
                print("\n" + "-"*20 +"\nADD NEW USER")
                Chat.send(client, "///NEW[USER]")
                friend_name = input(str("FRIEND LOGIN -> ")).strip()
                friend_id = input(str("FRIEND ID -> ")).strip()
                if Client_side.checksum(friend_id, 0, 4) == int(friend_id[10]) and Client_side.checksum(friend_id, 5, 9) == int(friend_id[11]) and len(friend_id) == 12:
                    Chat.send(client, f"{friend_id}^^{friend_name}")
                    friends = eval(client.recv(1024).decode('utf-8'))
                else:
                    print("\n" + "-"*20 + "\nInvalid friend ID!")
                continue
            elif choice < i and choice >= 1:
                print("\n" + "-"*20 + f"\nChatting with user {friends[choice-1]}")
                Chat.send(client, "//PICK")
                chat = friends[choice-1]  # TODO: send it to server
                break
            else:
                print("\nINVALID OPTION!")
        return chat

##############################

if __name__ == "__main__":

    Interface.display_logo()

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "-setup":
            os.system("pip3 install ahk")
            os.system("pip3 install ahk[binary]")
            os.system("pip3 install tinyec")
            print("\n" +"-"*20 + "\nDONE...")
            exit(0)

    except Exception as e:
        print("\n" + "-"*20 + f"\nAn ERROR OCCURED! - {e}")
        print("TRY INSTALLING LIBRARIES MANUALLY!")
        exit(0)

    try:
        ADDRESS = "127.0.0.1"
        PORT = 9999
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ADDRESS, PORT))

    except ConnectionRefusedError:
        print("\n" + "-"*20 + "\nAn connection ERROR OCCURED!")
        print("EXITING...")
        exit(0)
    except Exception as e:
        print("\n" + "-"*20 + f"\nAn ERROR OCCURED! - {e}")
        Client_side.disconnect(client)

    request = client.recv(1024).decode('utf-8')

    if "//AUTH" in request:
        SAFE_ZONE.auth(client)

    ecc_pv = Encryption.create_pv_key()
    ecc_pb = Encryption.create_pub_key(ecc_pv)

    request = client.recv(1024).decode('utf8')

    if "//KEY" in request:
        ecc_server_pb = request.split("->")[1].split(",")
        ecc_server_pb = Encryption.force_create_point(int(ecc_server_pb[0]), int(ecc_server_pb[1]))
        Chat.send(client, f"{ecc_pb.x},{ecc_pb.y}")

        ecc_shared = ecc_server_pb * ecc_pv

    nickname = Interface.welcome(client)

    if Encryption.decrypt(client.recv(1024).decode('utf8'), ecc_shared) == "//NICKNAME":
        Chat.send(client, nickname, True, ecc_shared)

    ecc_shared_server = ecc_shared

    try:
        while True:

            ex_msg = 2 # ex_msg -> exchanged messages

            recieved = Encryption.decrypt(client.recv(1024).decode('utf-8') , ecc_shared_server)

            if "//CHATROOM" in recieved:
                print("CHOOSE CHATTT")
                Interface.clear_console()
                chat_room = Interface.choose_chat(client, nickname)
                Chat.send(client, chat_room, True, ecc_shared_server)

            print(f"\033[K{client.recv(1024).decode('utf-8')}")

            write_process = threading.Thread(target=Chat.send_message, args=(client,))
            recieve_messages = threading.Thread(target=Chat.recieve_messages, args=(client,))

            write_process.start()
            recieve_messages.start()

            try:
                write_process.join()
                recieve_messages.join()
            except KeyboardInterrupt:
                write_process.join()
                recieve_messages.join()

            chat_room = ""

        exit(0)

    except KeyboardInterrupt:
        print("\n" + "-"*20 + "\nPlease next time EXIT SAFELY")
        Client_side.disconnect(client)

    except Exception as e:
        print("\n" + "-"*20 + f"\nAn ERROR OCCURED! - {e}")
        Client_side.disconnect(client)
