import pickle
import socket
import threading
from protocol import protocol_receive
from protocol import protocol_send
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
ADDRESS_LIST = [("127.0.0.1", 2222), ("127.0.0.1", 3333)]
SECRET_KEY = "my_secret_key"

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log2'
LOG_FILE = LOG_DIR + '/main_server.log'


def logging_protocol(func, cmd, data):
    try:
        msg = func + " : " + cmd
        for i in data:
            if type(i) is not bytes:
                msg += ", " + str(i)
        logging.debug(msg)
    except Exception as e:  # תפיסת כל סוגי החריגות
        logging.debug(e)


def background_task():
    db = MusicDB("my_db.db", ADDRESS_LIST)
    token = generate_infinity_token()
    while True:
        db.verify_and_backup_songs(token, ADDRESS_LIST)
        time.sleep(15)


def generate_token():
    """יוצר טוקן JWT עם user_id וחותם עליו עם המפתח הסודי."""
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # תוקף לשעה
        "iat": datetime.datetime.utcnow(),  # זמן יצירה
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def generate_infinity_token():
    """
    יוצר טוקן JWT ללא תפוגה, המכיל את זמן היצירה.

    :return: מחרוזת טוקן JWT חתום עם HS256.
    """
    payload = {
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


def handle_client(client_socket, client_address):
    try:
        db = MusicDB("my_db.db", ADDRESS_LIST)
        songs_dict = db.all_songs()
        songs_dict = pickle.dumps(songs_dict)
        token = generate_token()
        temp = False
        while not temp:
            msg = protocol_receive(client_socket)
            if msg is not None:
                cmd = msg[0]
                data = msg[1]
                logging_protocol("receive", cmd, data)
                if cmd == "sig":
                    username = data[0]
                    password = data[1]
                    db.add_user(username, password)

                    cmd = "sig"
                    data = ["True", token, songs_dict]
                    protocol_send(client_socket, cmd, data)
                    logging_protocol("send", cmd, data)
                    temp = True

                elif cmd == "log":
                    username = data[0]
                    password = data[1]
                    val, problem = db.verified_user(username, password)
                    cmd = "log"
                    if not val:
                        if problem == "username":
                            data = ["False", "username"]
                            protocol_send(client_socket, cmd, data)
                        elif problem == "password":
                            data = ["False", "password"]
                            protocol_send(client_socket, cmd, data)
                    elif val:
                        temp = True
                        data = ["True", token, songs_dict]
                        protocol_send(client_socket, cmd, data)
                    logging_protocol("send", cmd, data)

        while True:
            try:
                cmd, data = protocol_receive(client_socket)
                logging_protocol("receive", cmd, data)
                token = data[0]
                valid = verify_token(token)
                if not valid.get("valid"):
                    error = valid.get("error")
                    #print(error)
                    data = [error]
                    protocol_send(client_socket, cmd, data)
                    logging_protocol("send", cmd, data)
                    break
                elif valid.get("valid"):
                    if cmd == "gad":  # [id]
                        song_id = data[1]
                        result = db.get_address(song_id)
                        if result:
                            ip, port = result
                            data= [ip, port]
                            protocol_send(client_socket, cmd, data)
                        else:
                            data = ["ID not found"]
                            protocol_send(client_socket, cmd, data)
                        logging_protocol("send", cmd, data)

                    elif cmd == "pad":  # [name, artist]
                        name = data[1]
                        artist = data[2]
                        id, ip, port = db.add_song(name, artist)
                        id = id[0][0]
                        cmd = "pad"
                        data = [str(id), ip, port]
                        protocol_send(client_socket, cmd, data)
                        logging_protocol("send", cmd, data)

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
                thread = threading.Thread(target=handle_client, args=([client_socket, client_address]))
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
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)

    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    main()
