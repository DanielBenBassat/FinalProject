import pickle
import socket
import threading
from protocol import protocol_receive, protocol_send
import logging
import os
from music_db import MusicDB
import time
import jwt
import datetime
import ssl


class MainServer:
    def __init__(self, ip, port, cert_file, key_file, address_list, secret_key):
        """
        Initializes the main server.

        :param ip: The IP address the server should bind to.
        :param port: The TCP port number the server will listen on.
        :param cert_file: Path to the server's SSL certificate file (in PEM format).
        :param key_file: Path to the server's private key file (in PEM format).
        :param address_list: A list of addresses (e.g. media servers or other nodes).
        :param secret_key: A shared secret key used for authentication or encryption between nodes.
        """
        self.IP = ip
        self.PORT = port
        self.CERT_FILE = cert_file
        self.KEY_FILE = key_file
        self.ADDRESS_LIST = address_list
        self.SECRET_KEY = secret_key

        self.CLIENTS_SOCKETS = []
        self.THREADS = []
        self.LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
        self.LOG_LEVEL = logging.DEBUG
        self.LOG_DIR = 'log2'
        self.LOG_FILE = os.path.join(self.LOG_DIR, 'main_server.log')

        self._setup_logging()
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(certfile=self.CERT_FILE, keyfile=self.KEY_FILE)



    def _setup_logging(self):
        try:
            if not os.path.isdir(self.LOG_DIR):
                os.makedirs(self.LOG_DIR)
            logging.basicConfig(format=self.LOG_FORMAT, filename=self.LOG_FILE, level=self.LOG_LEVEL)
        except Exception as e:
            print(f"Failed to setup logging: {e}")


    @staticmethod
    def logging_protocol(func, cmd, data):
        """
        Logs a debug message composed of the function name, command, and data items.

        The message format is: "<func> : <cmd>, <data_item1>, <data_item2>, ...".
        Bytes-type items in `data` are skipped and not included in the message.

        :param func: Name of the function or operation (string).
        :param cmd: Command or action description (string).
        :param data: Iterable containing data items to log.
        """
        try:
            msg = func + " : " + cmd
            for i in data:
                if not isinstance(i, bytes):
                    msg += ", " + str(i)
            logging.debug(msg)
        except Exception as e:
            logging.debug(e)

    def generate_token(self, username):
        """
        Generates a JWT token for the given username with 1 hour expiry.

        :param username: User identifier for the token.
        :return: Encoded JWT token string.
        """
        payload = {
            "sub": username,  # Subject: מי המשתמש
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            "iat": datetime.datetime.utcnow()
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm="HS256")

    def verify_token(self, token):
        """
        Verifies a JWT token's validity and expiration.

        :param token: JWT token string.
        :return: Dict with 'valid' boolean and data or error message.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=["HS256"])
            return {"valid": True, "data": payload}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}

    def background_task(self):
        """
        Runs periodic background tasks: server checks, song verification, and backups.
        """
        db = MusicDB("my_db.db", self.ADDRESS_LIST)
        token = self.generate_token("main_server")
        token2 = self.generate_token("media_server")
        while True:
            db.check_server(token)
            db.verify_songs(token)
            db.backup_songs(token, token2)
            time.sleep(15)

    def login_signup(self, db, client_socket):
        """
        Handles user login and signup interactions with the client.

        :param db: MusicDB instance.
        :param client_socket: Socket connected to the client.
        :return: True if login/signup successful, False otherwise.
        """
        logging.debug("Waiting for login or signup")
        songs_dict = pickle.dumps(db.all_songs())

        while True:
            msg = protocol_receive(client_socket)
            if msg is not None:
                cmd, data = msg
                self.logging_protocol("receive", cmd, data)

                if cmd == "sig":
                    username, password = data
                    success = db.add_user(username, password)
                    token = self.generate_token(username)
                    response_data = ["T", token, songs_dict] if success else ["F", "existing"]
                    protocol_send(client_socket, cmd, response_data)
                    self.logging_protocol("send", cmd, response_data)
                    if success:
                        return True

                elif cmd == "log":
                    username, password = data
                    is_verified, reason = db.verified_user(username, password)
                    token = self.generate_token(username)

                    if not is_verified:
                        response_data = ["F", reason]
                    else:
                        liked = pickle.dumps(db.get_user_playlists(username, "liked_song"))
                        response_data = ["T", token, songs_dict, liked]
                    protocol_send(client_socket, cmd, response_data)
                    self.logging_protocol("send", cmd, response_data)
                    if is_verified:
                        return True

                elif cmd in ("ext", "error"):
                    logging.debug("EXT command received")
                    return False

    def handle_client(self, client_socket):
        """
        Manages communication with a connected client, handling commands and authentication.

        :param client_socket: SSL wrapped client socket.
        """
        try:
            db = MusicDB("my_db.db", self.ADDRESS_LIST)
            if not self.login_signup(db, client_socket):
                return

            while True:
                cmd, data = protocol_receive(client_socket)
                self.logging_protocol("receive", cmd, data)

                token = data[0]
                verification = self.verify_token(token)

                if not verification["valid"]:
                    protocol_send(client_socket, cmd, ["F", verification["error"]])
                    self.logging_protocol("send", cmd, ["F", verification["error"]])
                    if not self.login_signup(db, client_socket):
                        break
                    continue

                if cmd == "gad":
                    address = db.get_address(data[1])
                    response_data = ["T", *address] if address else ["F", "ID not found"]

                elif cmd == "pad":
                    response_data = db.add_song(data[1], data[2])

                elif cmd == "rfs":
                    response_data = ["T", pickle.dumps(db.all_songs())]

                elif cmd == "atp":
                    response_data = db.add_to_playlist(data[1], data[2], data[3])

                elif cmd == "rfp":
                    response_data = db.remove_from_playlist(data[1], data[2], data[3])

                elif cmd == "lgu":
                    if not self.login_signup(db, client_socket):
                        break
                    continue

                elif cmd in ("ext", "error"):
                    break
                else:
                    response_data = ["F"]

                protocol_send(client_socket, cmd, response_data)
                self.logging_protocol("send", cmd, response_data)

        except Exception as e:
            logging.error(f"[ERROR] Exception in client handling: {e}")
        finally:
            client_socket.close()
            logging.debug("Client disconnected")

    def start(self):
        """
        Starts the server: binds socket, listens for clients, and spawns handler threads.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.IP, self.PORT))
        server_socket.listen()
        logging.debug("Server started and listening...")

        background = threading.Thread(target=self.background_task, daemon=True)
        background.start()

        try:
            while True:
                client_socket, _ = server_socket.accept()
                ssl_socket = self.context.wrap_socket(client_socket, server_side=True)
                self.CLIENTS_SOCKETS.append(ssl_socket)

                thread = threading.Thread(target=self.handle_client, args=(ssl_socket,))
                self.THREADS.append(thread)
                thread.start()
                logging.debug(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            server_socket.close()
            logging.debug("Server closed")


if __name__ == "__main__":
    server = MainServer(
        ip="127.0.0.1",
        port=5555,
        cert_file="C:/work/cyber/FinalProject/code.MAIN_SERVER/certificate_main.crt",
        key_file="C:/work/cyber/FinalProject/code.MAIN_SERVER/privatekey_main.key",
        address_list=[("127.0.0.1", 2222), ("127.0.0.1", 3333)],
        secret_key="my_secret_key"
    )
    server.start()
