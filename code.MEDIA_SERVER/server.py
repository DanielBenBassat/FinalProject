import socket
import os
import threading
import jwt
import logging
from protocol import protocol_receive, protocol_send
import ssl


class MediaServer:
    def __init__(self, ip, port, folder, secret_key, cert_file, key_file, queue_len=1, log_dir='log3', log_file='server.log'):
        """
       Initializes the MediaServer with networking configuration,
       folder for storing songs, SSL settings, and logging.

       :param ip: str - The IP address the server binds to.
       :param port: int - The port number the server listens on.
       :param folder: str - Path to the directory where songs are stored.
       :param secret_key: str - Secret key used to verify JWT tokens for client authentication.
       :param cert_file: str - Path to the SSL certificate file (used for secure server connections).
       :param key_file: str - Path to the SSL private key file.
       :param queue_len: int, optional - Maximum number of queued client connections (default is 1).
       :param log_dir: str, optional - Directory where log files are stored (default is 'logs').
       :param log_file: str, optional - Name of the log file (default is 'server.log').

       :return: None
       """
        self.ip = ip
        self.port = port
        self.folder = folder
        self.secret_key = secret_key
        self.queue_len = queue_len
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, log_file)
        self._setup_folders()

        self.CERT_FILE = cert_file
        self.KEY_FILE = key_file
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(certfile=self.CERT_FILE, keyfile=self.KEY_FILE)

        # contex2 for the action that the mian server connecting to other server
        self.context2 = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.context2.check_hostname = False
        self.context2.verify_mode = ssl.CERT_NONE

    def create_ssl_socket(self, client_socket, ip):
        """
        Wraps a plain TCP socket with SSL/TLS encryption using the client's SSL context.

        :param client_socket: A plain (non-encrypted) socket.socket object.
        :param ip: The server's IP address or hostname used for SSL hostname verification.
        :return: An SSL-wrapped socket with a timeout of 5 seconds set.
        :raises ssl.SSLError: If an SSL-related error occurs during wrapping.
        :raises socket.error: If a socket-related error occurs.
        """
        try:
            ssl_socket = self.context2.wrap_socket(client_socket, server_hostname=ip)
            ssl_socket.settimeout(5)
            return ssl_socket
        except ssl.SSLError as ssl_err:
            logging.error(f"SSL error while wrapping socket: {ssl_err}")
            raise  # אפשר להעביר את השגיאה הלאה או לטפל כאן בהתאם
        except socket.error as sock_err:
            logging.error(f"Socket error while setting up SSL socket: {sock_err}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in create_ssl_socket: {e}")
            raise

    def _setup_folders(self):
        """
        Creates the media and log directories if they do not exist.

        :return: None
        """
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        logging.basicConfig(
            format='%(levelname)s | %(asctime)s | %(message)s',
            filename=self.log_file,
            level=logging.DEBUG)

    @staticmethod
    def logging_protocol(func, cmd, data):
        """"
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

    def verify_token(self, token):
        """
        Verifies the validity of a JWT token.

        :param token: The JWT token to be verified.
        :return: A dictionary indicating validity and payload or error message.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            logging.debug("Token is valid")
            return {"valid": True, "data": payload}
        except jwt.ExpiredSignatureError:
            logging.debug("Token has expired")
            return {"valid": False, "error": "Token has expired"}
        except jwt.InvalidTokenError:
            logging.debug("Invalid token")
            return {"valid": False, "error": "Invalid token"}

    def send_song(self, cmd, client_socket, song_name, token=""):
        """
        Sends a song file to the client based on the command type.

        :param cmd: Command type ('get' or 'bkp').
        :param client_socket: The socket connected to the client.
        :param song_name: Name of the song (without file extension).
        :param token: JWT token (optional, used for backup command).

        :return: None
        """
        data = []
        try:
            song_path = os.path.join(self.folder, f"{song_name}.mp3")
            with open(song_path, "rb") as file:
                song_bytes = file.read()

            if cmd == "bkp":
                data = [token, song_name, song_bytes]
            elif cmd == "get":
                data = ["T", song_name + ".mp3", song_bytes]

        except FileNotFoundError:
            logging.debug("File not found: " + song_name)
            data = ["F", "file not found"]
        except OSError as e:
            logging.debug(f"OS error while sending {song_name}: {e}")
            data = ["F", "OS error"]
        except Exception as e:
            logging.debug(f"Unexpected error while sending {song_name}: {e}")
            data = ["F", "Unexpected error"]
        finally:
            try:
                protocol_send(client_socket, cmd, data)
                self.logging_protocol("send", cmd, data)
            except Exception as e:
                logging.debug(f"Unexpected error while sending {song_name}: {e}")
            finally:
                if client_socket and cmd == "get":
                    logging.debug("close socket with client")
                    client_socket.close()

    def add_song(self, song_byte, song_name):
        """
        Saves a song's bytes as an MP3 file in the media folder.

        :param song_byte: Byte content of the song.
        :param song_name: Name to save the file as (without extension).

        :return: True if save succeeded, False otherwise.
        """
        try:
            path = os.path.join(self.folder, f"{song_name}.mp3")
            with open(path, 'wb') as file:
                file.write(song_byte)
            return True
        except Exception as e:
            logging.debug(f"Error saving file: {e}")
            return False

    def handle_client(self, client_socket, client_address):
        """
        Handles an individual client connection, processing commands and
        sending appropriate responses.

        :param client_socket: The socket connected to the client.
        :param client_address: Client's address info.

        :return: None
        """
        logging.debug(f"Client connected: {client_address}")
        try:
            cmd, data = protocol_receive(client_socket)
            if cmd != "hlo":
                self.logging_protocol("recv", cmd, data)

            token = data[0]
            valid = self.verify_token(token)

            if not valid["valid"]:
                protocol_send(client_socket, cmd, ["False", "token is not valid"])
                self.logging_protocol("send", cmd, data)
                return

            if cmd == "get":
                self.send_song("get", client_socket, str(data[1]))

            elif cmd == "pst":
                is_ok = self.add_song(data[2], str(data[1]))
                if is_ok:
                    res = ["T", "post song succeeded"]
                else:
                    res = ["F", "post song failed"]
                protocol_send(client_socket, cmd, res)
                self.logging_protocol("send", cmd, res)

            elif cmd == "hlo":
                res = ["T"]
                protocol_send(client_socket, cmd, res)
                self.logging_protocol("send", cmd, res)

            elif cmd == "vrf":
                song_path = os.path.join(self.folder, f"{data[1]}.mp3")
                if os.path.exists(song_path):
                    res = ["T", "found"]
                else:
                    res = ["F", "lost"]
                protocol_send(client_socket, cmd, res)
                self.logging_protocol("send", cmd, res)

            elif cmd == "bkg":
                try:
                    token, song_name, ip, port = data[1], str(data[2]), data[3], int(data[4])
                    protocol_send(client_socket, cmd, ["T"])
                    self.logging_protocol("send", cmd, ["T"])

                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    ssl_s = self.create_ssl_socket(s, ip)
                    ssl_s.connect((ip, port))
                    self.send_song("bkp", ssl_s, song_name, token)
                    cmd, data = protocol_receive(ssl_s)
                    self.logging_protocol("recv", cmd, data)
                    ssl_s.close()
                except Exception as e:
                    logging.debug(f"Failed to connect to secondary server: {e}")

            elif cmd == "bkp":
                result = self.add_song(data[2], str(data[1]))
                if result:
                    logging.debug("Song uploaded")
                protocol_send(client_socket, cmd, ["T"])
                self.logging_protocol("send", cmd, ["T"])

        except socket.error as e:
            logging.debug("Socket error: " + str(e))
        finally:
            client_socket.close()
            logging.debug("Client disconnected")

    def start(self):
        """
        Starts the media server, listens for incoming connections,
        and spawns a new thread to handle each client.

        :return: None
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.ip, self.port))
                s.listen(self.queue_len)
                logging.debug(f"Media server started at {self.ip}:{self.port}")
                while True:
                    try:
                        client_socket, client_addr = s.accept()
                        ssl_socket = self.context.wrap_socket(client_socket, server_side=True)
                        threading.Thread(target=self.handle_client, args=(ssl_socket, client_addr)).start()
                    except Exception as e:
                        logging.debug(f"Error accepting or handling connection: {e}")
                        break
            except socket.error as e:
                logging.debug(f"Socket error on main socket: {e}")


if __name__ == "__main__":
    server = MediaServer(
        ip="127.0.0.1",
        port=2222,
        folder=r"C:\musicCyber",
        secret_key="my_secret_key",
        cert_file="certificate.crt",
        key_file="privateKey.key",
        queue_len=1,
        log_dir="log3",
        log_file="server.log"
    )
    server.start()