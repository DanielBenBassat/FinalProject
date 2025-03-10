import pickle
import socket
import threading
import protocol
import logging
import os
from music_db import MusicDB
import time
import jwt
import datetime


IP = "127.0.0.1"
PORT = 5555
CLIENTS_SOCKETS = []
THREADS = []
MD5_TARGET = "25f9e794323b453885f5181f1b624d0b"
NUM_PER_CORE = 10000
lock = threading.Lock()
task_start = 0
found = False
ADDRESS_LIST = [("127.0.0.1", 2222)]
SECRET_KEY = "my_secret_key"


def background_task():
    db = MusicDB("my_db.db")
    while True:
        db.verify_songs()
        time.sleep(15)


def generate_token():
    """יוצר טוקן JWT עם user_id וחותם עליו עם המפתח הסודי."""
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=1),  # תוקף לשעה
        "iat": datetime.datetime.utcnow(),  # זמן יצירה
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token):
    """בודק אם טוקן JWT תקף ומחזיר את הנתונים שבו."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "data": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}

def handle_client(client_socket):
    try:
        db = MusicDB("my_db.db")
        dict = db.all_songs()
        dict = pickle.dumps(dict)
        token = generate_token()
        #enter to system
        temp = False
        while not temp:
            msg = protocol.protocol_receive(client_socket)
            if msg is not None:
                cmd = msg[0]
                data = msg[1]
            if cmd == "sig":
                username = data[0]
                password = data[1]
                db.add_user(username, password)
                protocol.protocol_send(client_socket, "sig", ["good", token, dict])
                temp = True
            elif cmd == "log":
                username = data[0]
                password = data[1]
                val, problem = db.verified_user(username, password)
                if not val:
                    if problem == "username":
                        protocol.protocol_send(client_socket, "log", ["False", "username"])
                    elif problem == "password":
                        protocol.protocol_send(client_socket, "log", ["False", "password"])
                elif val:
                    temp = True
                    protocol.protocol_send(client_socket, "log", ["good", token, dict])


        #start working



        while True:
            try:
                msg = protocol.protocol_receive(client_socket)
                if msg is None:
                    logging.debug("[ERROR] Received None, closing connection.")
                    break

                cmd, data = msg
                logging.debug(f"Received command: {cmd}, Data: {data}")

                if cmd == "gad":  # [id]
                    song_id = data[0]
                    result = db.get_address(song_id)
                    if result:
                        ip, port = result
                        protocol.protocol_send(client_socket, "gad", [ip, port])
                    else:
                        protocol.protocol_send(client_socket, "error", ["ID not found"])

                elif cmd == "pad":  # [name, artist]
                    name, artist = data
                    id, ip, port = db.add_song(name, artist, ADDRESS_LIST)
                    id = id[0][0]
                    protocol.protocol_send(client_socket, "pad", [id, ip, port])

            except Exception as e:
                logging.error(f"[ERROR] Exception in client handling: {e}")
                break  # יציאה אם יש שגיאה`

    except socket.error as e:
        logging.error(f"[ERROR] Socket error: {e}")
    finally:
        client_socket.close()
        logging.debug("Client disconnected")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((IP, PORT))
        server.listen()
        while True:
            try:
                client_socket, client_address = server.accept()
                CLIENTS_SOCKETS.append(client_socket)
                thread = threading.Thread(target=handle_client, args=([client_socket]))
                THREADS.append(thread)
                thread.start()
                logging.debug(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            except socket.error:
                logging.debug("socket error")

    except socket.error:
        logging.debug("socket error")
    finally:
        server.close()
        logging.debug("server is closed")


if __name__ == "__main__":
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    main()
