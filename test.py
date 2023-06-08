import pymongo
import random
import hashlib


def connect():
    DB_CLIENT = pymongo.MongoClient("mongodb://localhost:27017/")\

    DB = DB_CLIENT["database"]

    COLLECTION = DB["users"]

    print(DB_CLIENT.list_database_names())

    return COLLECTION


def register(login, password, confirmation, user_id, token, COLLECTION):
    if password != confirmation:
        return

    data = {"user_id" : user_id, "username" : login, "password" : password, "token" : token}
    COLLECTION.insert_one(data)


def sign_in(login, password, COLLECTION):
    result = COLLECTION.find({"username" : login, "password" : password})
    try:
        if result[0]["username"] == login:
            return True
        else:
            return False
    except:
        return False


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

def password_recovery(token, COLLECTION):
    result = COLLECTION.find({"token" : token})
    try:
        result[0]["token"]
    except:
        print("INVALID TOKEN!")
        return
    password = hash_sha(input(str("NEW PASSWORD -> ")))
    password_confirm = hash_sha(input(str("CONFIRM PASSWORD -> ")))
    if password != password_confirm:
        print("PASSWORD AND CONFIRMATION DOES NOT MATCH!")
        return
    if password == result[0]["password"]:
        print("NEW PASSWORD CANNOT BE SAME AS OLD!")
        return
    COLLECTION.update_one({"token" : token}, { "$set" : {"password" : password}})
    print(result[0])
    pass


def hash_sha(data):
    sha256 = hashlib.sha256()
    sha256.update(data.encode("utf-8"))
    return sha256.hexdigest()

COLLECTION = connect()

print("""
   _____         ______ ______        _____ _    _       _______             _____  _____
  / ____|  /\   |  ____|  ____|      / ____| |  | |   /\|__   __|      /\   |  __ \|  __ \ 
 | (___   /  \  | |__  | |__        | |    | |__| |  /  \  | |        /  \  | |__) | |__) |
  \___ \ / /\ \ |  __| |  __|       | |    |  __  | / /\ \ | |       / /\ \ |  ___/|  ___/
  ____) / ____ \| |    | |____      | |____| |  | |/ ____ \| |      / ____ \| |    | |
 |_____/_/    \_\_|    |______|      \_____|_|  |_/_/    \_\_|     /_/    \_\_|    |_|
 """)

while True:
    print("\n" + "-"*20 + "\nCHOOSE OPTION: " + "\n1. Login \n2. Register \n3. Forgotten password")
    option = int(input(str("> ")))

    match option:
        case 1:
            login = input(str("LOGIN -> "))
            password = input(str("PASSWORD -> "))
            if sign_in(login, hash_sha(password), COLLECTION):
                print("LOGGED IN!")
            else:
                print("INCORRECT LOGIN OR PASSWORD!")
                break
            break

        case 2:
            print("\n" + "-"*20 + "\nSIGN UP")
            login = input(str("LOGIN -> "))
            password = input(str("PASS -> "))
            password_confirm = input(str("CONFIRM PASS -> "))
            user_id = create_id(login)
            token = create_token()
            register(login, hash_sha(password), hash_sha(password_confirm), user_id, hash_sha(token), COLLECTION)
            print(f"THIS IS YOUR RECOVERY TOKEN, NEVER FORGET IT:  {token}")
            print(f"Registred as {login} with pass {password}")
            break

        case 3:
            print("\n" + "-"*20 + "\nPASSWORD RECOVERY")
            token = input(str("TOKEN -> "))
            password_recovery(hash_sha(token), COLLECTION)
            break

        case default:
            print("WRONG OPTION!")
            continue

print("\n" + "-"*20 + "\nCHOOSE CHAT: ")

query = COLLECTION.find({})
options = {}
i = 1

for document in query:
    options[i] = document["username"]
    i += 1
options[i] = "NEW USER"

for number in options:
    print(f"{number}. {options[number]}")

option = int(input(str("> ")))

print(f"Chatting on chat room: {options[option]}")
