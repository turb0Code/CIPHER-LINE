<img src="https://raw.githubusercontent.com/turb0Code/CIPHER-LINE/main/ExtraResources/cipher-line.png"/>

## INTRODUCTION
> *CPIHER-LINE* IS STILL IN DEVELOPMENT

*CIPHER-LINE* is a console chat app that allows you to have private conversations with your friends. Enjoy the freedom of chatting without worrying about privacy. Your messages are encrypted, ensuring your safety and security.


## USAGE

### SERVER SIDE

1. Download python `3.10` or newer.
2. It's recommended to download MongoDBCompass.
3. Download lastest *CIPHER-LINE* release.
4. Bring `server.py` and `version.env` into one directory.
5. Run server setup with command:
```
python3 server.py -setup
```

6. Now you can just run server!
```
python3 server.py
```

### CLIENT SIDE

1. Download python `3.10` or newer.
2. Download lastest *CIPHER-LINE* release.
3. Run client setup with
```
python3 client.py -setup
```

4. Now you can run client, register and chat with friends safely!
```
python3 client.py
```

## ENCRYPTION

*CIPHER-LINE* ensures your privacy by utilizing ECC (Elliptic-Curve Cryptography) encryption. This state-of-the-art encryption technique guarantees that your messages remain secure and confidential. *CIPHER-LINE* offers full end-to-end encryption for your peace of mind.


## PRIVACY

*CIPHER-LINE* does not store your IP address or any other sensitive data in the database. It only saves essential information such as login credentials, hashed passwords, and hashed recovery tokens to provide the best user experience while prioritizing your privacy.

## GOALS

> - ~~.env files support~~
> - simplified process of adding new friends using special files
