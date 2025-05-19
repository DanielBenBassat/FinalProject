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
import ssl

CERT_FILE = "C:/work/cyber/FinalProject/code.MAIN_SERVER/certificate_main.crt"
KEY_FILE = "C:/work/cyber/FinalProject/code.MAIN_SERVER/privatekey_main.key"
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
    """
    Logs a protocol-level action for debugging.

    :param func: The type of operation ("send" or "recv").
    :param cmd: The command used .
    :param data: Data sent or received in the protocol.
    """
    try:
        msg = func + " : " + cmd
        for i in data:
            if type(i) is not bytes:
                msg += ", " + str(i)
        logging.debug(msg)
    except Exception as e:
        logging.debug(e)


def background_task():
    db = MusicDB("my_db.db", ADDRESS_LIST)
    token = generate_token()
    token2 = generate_token()
    while True:
        db.check_server(token)
        db.verify(token)
        db.backup_songs(token, token2)
        time.sleep(15)


def generate_token():
    """
    Generates a new JWT token with a short expiration time.

    :return: A JWT token string encoded using the HS256 algorithm, containing:
             - 'exp': Token expiration time (5 minutes from creation)
             - 'iat': Token creation time (current UTC time)
    """
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # תוקף לשעה
        "iat": datetime.datetime.utcnow(),  # זמן יצירה
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token):
    """
    Verifies a JWT token.

    :param token: The token string to verify.
    :return: A dict with 'valid': True/False. if True return איק פשטךםשג and if false return the type of error
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "data": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}


def login_signup(db, client_socket):
    logging.debug("back to waiting for log")
    songs_dict = db.all_songs()
    songs_dict = pickle.dumps(songs_dict)
    token = generate_token()
    temp = True
    val = True
    while temp:
        msg = protocol_receive(client_socket)
        if msg is not None:
            cmd = msg[0]
            data = msg[1]
            logging_protocol("receive", cmd, data)
            if cmd == "sig":
                username = data[0]
                password = data[1]
                check = db.add_user(username, password)

                cmd = "sig"
                if check:
                    data = ["T", token, songs_dict]
                    temp = False
                else:
                    data = ["F", "existing"]
                protocol_send(client_socket, cmd, data)
                logging_protocol("send", cmd, data)

            elif cmd == "log":
                username = data[0]
                password = data[1]
                val, problem = db.verified_user(username, password)
                cmd = "log"
                if not val:
                    if problem == "username":
                        data = ["F", "username"]
                        protocol_send(client_socket, cmd, data)
                    elif problem == "password":
                        data = ["", "password"]
                        protocol_send(client_socket, cmd, data)
                elif val:
                    temp = False
                    liked_song = db.get_user_playlists(username, "liked_song")
                    liked_song = pickle.dumps(liked_song)
                    data = ["T", token, songs_dict, liked_song]
                    protocol_send(client_socket, cmd, data)
                logging_protocol("send", cmd, data)

            elif cmd == "ext" or cmd == "error":
                print("EXT command received, breaking loop.")
                temp = False
                val = False
    logging.debug("finish loign")
    return val


def handle_client(client_socket):
    try:
        db = MusicDB("my_db.db", ADDRESS_LIST)
        temp = login_signup(db, client_socket)

        while temp:
            try:
                print("waiting for cmd")
                cmd, data = protocol_receive(client_socket)
                logging_protocol("receive", cmd, data)

                token = data[0]
                valid = verify_token(token)
                if not valid.get("valid"):
                    error = valid.get("error")
                    data = ["F", error]
                    protocol_send(client_socket, cmd, data)
                    logging_protocol("send", cmd, data)
                    login_signup(db, client_socket)

                elif valid.get("valid"):
                    if cmd == "gad":  # [id]
                        song_id = data[1]
                        address = db.get_address(song_id)
                        if address:
                            data = ["T", address[0], address[1]]
                            protocol_send(client_socket, cmd, data)
                        else:
                            data = ["F", "ID not found"]
                            protocol_send(client_socket, cmd, data)
                        logging_protocol("send", cmd, data)

                    elif cmd == "pad":  # [name, artist]
                        name = data[1]
                        artist = data[2]
                        data = db.add_song(name, artist)
                        protocol_send(client_socket, cmd, data)
                        logging_protocol("send", cmd, data)

                    elif cmd == "rfs":  # [token]
                        song_list = db.all_songs()
                        song_list = pickle.dumps(song_list)
                        data = ["T", song_list]
                        protocol_send(client_socket, cmd, data)
                        logging_protocol("send", cmd, data)

                    elif cmd == "atp":  # add to playlist
                        username = data[1]
                        playlist_name = data[2]
                        song_id = data[3]
                        data = db.add_to_playlist(username, playlist_name, song_id)
                        protocol_send(client_socket, cmd, data)
                        logging_protocol("send", cmd, data)

                    elif cmd == "rfp":  # remove from playlist
                        username = data[1]
                        playlist_name = data[2]
                        song_id = data[3]
                        data = db.remove_from_playlist(username, playlist_name, song_id)
                        protocol_send(client_socket, cmd, data)
                        logging_protocol("send", cmd, data)

                    elif cmd == "lgu":
                        login_signup(db, client_socket)

                    elif cmd == "ext" or cmd == "error":
                        print("EXT command received, breaking loop.")
                        break

            except Exception as e:
                logging.error(f"[ERROR] Exception in client handling: {e}")
                break  # יציאה אם יש שגיאה`

    except socket.error as e:
        logging.error(f"[ERROR] Socket error: {e}")
    finally:
        client_socket.close()
        logging.debug("Client disconnected")
        logging.debug(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")


def main():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((IP, PORT))
        server.listen()
        while True:
            try:
                client_socket, client_address = server.accept()
                ssl_client_socket = context.wrap_socket(client_socket, server_side=True)

                CLIENTS_SOCKETS.append(ssl_client_socket)
                thread = threading.Thread(target=handle_client, args=(ssl_client_socket,))
                THREADS.append(thread)
                thread.start()
                logging.debug(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")
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

    background_thread = threading.Thread(target=background_task, daemon=True)
    background_thread.start()
    main()
