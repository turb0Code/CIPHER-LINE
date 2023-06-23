import pymongo

def connect():
    DB_CLIENT = pymongo.MongoClient("mongodb://localhost:27017/")

    DB = DB_CLIENT["database"]

    COLLECTION = DB["users"]

    print(DB_CLIENT.list_database_names())

    return COLLECTION


COLLECTION = connect()


def add_friend(username, friend_name, friend_id):
    result = COLLECTION.find_one({"username" : friend_name, "user_id" : friend_id})
    try:
        if result["user_id"] == friend_id:
            COLLECTION.update_one({"username" : username}, { "$set" : {"friends" : [[friend_id, friend_name]]}})
            print(f"Successfully added new friend {friend_name}")
        else:
            print("USER NOT FOUND!")
    except:
        print("USER NOT FOUND!")


def get_friends(username):
    result = COLLECTION.find_one({"username" : username})
    friends = []
    for i in range(len(result["friends"])):
        friends.append(f"{result['friends'][i][1]} | {result['friends'][i][0]}")
    return friends


def choose_chat():

    friends = get_friends("admin")

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
            break
        elif choice == i+1:
            print("\n" + "-"*20 +"\nSETTINGS")
            break
        elif choice == i:
            print("\n" + "-"*20 +"ADD NEW USER")
            add_friend("admin", "test", "0177-4073-08")
            break
        elif choice < i and choice >= 1:
            print("\n" + "-"*20 + f"\nChatting with user {friends[choice-1]}")
            break
        else:
            print("\nINVALID OPTION!")