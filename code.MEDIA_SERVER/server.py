import socket
import os
import threading
import jwt
import logging
from protocol import protocol_receive, protocol_send


class MediaServer:
    def __init__(self, ip, port, folder, secret_key, queue_len=1, log_dir='logs', log_file='server.log'):
        self.ip = ip
        self.port = port
        self.folder = folder
        self.secret_key = secret_key
        self.queue_len = queue_len
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, log_file)

        self._setup_environment()
        self._setup_logging()

    def _setup_environment(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _setup_logging(self):
        logging.basicConfig(
            format='%(levelname)s | %(asctime)s | %(message)s',
            filename=self.log_file,
            level=logging.DEBUG
        )

    def logging_protocol(self, func, cmd, data):
        try:
            msg = func + " : " + cmd
            for i in data:
                if not isinstance(i, bytes):
                    msg += ", " + str(i)
            logging.debug(msg)
        except Exception as e:
            logging.debug(e)

    def verify_token(self, token):
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
            protocol_send(client_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

    def add_song(self, song_byte, song_name):
        try:
            path = os.path.join(self.folder, f"{song_name}.mp3")
            with open(path, 'wb') as file:
                file.write(song_byte)
            return True
        except Exception as e:
            logging.debug(f"Error saving file: {e}")
            return False

    def handle_client(self, client_socket, client_address):
        logging.debug(f"Client connected: {client_address}")
        try:
            cmd, data = protocol_receive(client_socket)
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
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((ip, port))
                        self.send_song("bkp", s, song_name, token)
                except Exception as e:
                    logging.debug(f"Failed to connect to secondary server: {e}")

            elif cmd == "bkp":
                result = self.add_song(data[2], str(data[1]))
                if result:
                    logging.debug("Song uploaded")

        except socket.error as e:
            logging.debug("Socket error: " + str(e))
        finally:
            client_socket.close()
            logging.debug("Client disconnected")

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.ip, self.port))
                s.listen(self.queue_len)
                logging.debug(f"Media server started at {self.ip}:{self.port}")
                while True:
                    client_socket, client_addr = s.accept()
                    threading.Thread(target=self.handle_client, args=(client_socket, client_addr)).start()
            except socket.error as e:
                logging.debug(f"Socket error on main socket: {e}")

if __name__ == "__main__":
    server = MediaServer(
        ip="127.0.0.1",
        port=2222,
        folder=r"C:\musicCyber",
        secret_key="my_secret_key",
        queue_len=1,
        log_dir="log3",
        log_file="server.log"
    )
    server.start()