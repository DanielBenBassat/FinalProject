import queue
import socket
import logging
import ssl
from protocol import protocol_send
from protocol import protocol_receive
import threading
import pickle
import os
from songs_queue import SongsQueue
from player import MusicPlayer


CACHE_FOLDER = r"C:\work\cyber\FinalProject\code.CLIENT\cache"
LOG_DIR = 'log'
LOG_FILE_CLIENT = os.path.join(LOG_DIR, 'client.log')
LOG_FILE_PLAYER = os.path.join(LOG_DIR, 'player.log')
LOG_FORMAT = '%(levelname)s | %(asctime)s | %(name)s | %(message)s'


class Client:
    def __init__(self, ip, port):
        """
        Initializes the Client object, connects to the main server and sets up necessary components.
        :param ip: str, the IP address of the main server
        :param port: int, the port number of the main server
        :return: None
        """
        try:
            if not os.path.isdir(LOG_DIR):
                os.makedirs(LOG_DIR)
            if not os.path.exists(CACHE_FOLDER):
                os.mkdir(CACHE_FOLDER)

            self.client_log = self.setup_logger("ClientLogger", LOG_FILE_CLIENT)
            self.player_log = self.setup_logger("PlayerLogger", LOG_FILE_PLAYER)

            self.MAIN_SERVER_ADDR = (ip, port)

            self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.main_socket = self.create_ssl_socket(temp_socket, ip)
            self.main_socket.connect(self.MAIN_SERVER_ADDR)

            self.q = SongsQueue()
            self.p = MusicPlayer()
            self.client_to_gui_queue = queue.Queue()
            self.gui_to_client_queue = queue.Queue()

            self.username = ""
            self.token = ""
            self.song_id_dict = {}
            self.liked_song = []
            self.is_expired = True

            self.player_thread = threading.Thread(target=self.player_func, daemon=True)

        except socket.error as e:
            # If logging is not yet set, fallback to print
            if hasattr(self, 'client_log'):
                self.client_log.error(f"Socket error: {e}")
            else:
                print(f"Socket error: {e}")
        except Exception as e:
            if hasattr(self, 'client_log'):
                self.client_log.error(f"Error in client initialization: {e}")
            else:
                print(f"Error in client initialization: {e}")

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
            ssl_socket = self.context.wrap_socket(client_socket, server_hostname=ip)
            ssl_socket.settimeout(5)
            return ssl_socket
        except ssl.SSLError as ssl_err:
            self.client_log.error(f"SSL error while wrapping socket: {ssl_err}")
            raise  # אפשר להעביר את השגיאה הלאה או לטפל כאן בהתאם
        except socket.error as sock_err:
            self.client_log.error(f"Socket error while setting up SSL socket: {sock_err}")
            raise
        except Exception as e:
            self.client_log.error(f"Unexpected error in create_ssl_socket: {e}")
            raise

    @staticmethod
    def setup_logger(name, log_file):
        """
        Sets up a logger that writes to a specified log file.
        :param name: str, the logger name
        :param log_file: str, the log file path
        :return: logging.Logger object
        """
        try:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(LOG_FORMAT)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            return logger

        except Exception as e:
            print(f"Failed to setup logger {name}: {e}")
            return None

    def logging_protocol(self, func, cmd, data):
        """
        Log the protocol messages with the command and data.

        :param func: str, action type ("send" or "receive")
        :param cmd: str, command sent or received
        :param data: list, data associated with the command
        """
        try:
            msg = f"{func} : {cmd}"
            for i in data:
                if not isinstance(i, bytes):
                    msg += ", " + str(i)
            if self.client_log:
                self.client_log.debug(msg)
            else:
                print(msg)

        except Exception as e:
            if self.client_log:
                self.client_log.debug(f"Logging protocol error: {e}")
            else:
                print(f"Logging protocol error: {e}")

    def start_client(self, cmd, username, password):
        """
        Starts the client login or signup process with the main server, handles authentication and initializes session data.
        :param cmd: str, "1" for signup, "2" for login
        :param username: str, the username for authentication
        :param password: str, the password for authentication
        :return: list, response data from server (e.g., ["T", token, ...] or ["F", reason])
        """
        data = ["N"]
        try:
            if cmd == "1":
                cmd = "sig"
                data = [username, password]
                protocol_send(self.main_socket, cmd, data)
                self.logging_protocol("send", cmd, data)
                cmd, data = protocol_receive(self.main_socket)
                self.logging_protocol("received", cmd, data)
                if data[0] == "T":
                    self.username = username
                    self.token = data[1]
                    self.is_expired = False
                    self.song_id_dict = pickle.loads(data[2])

            elif cmd == "2":
                cmd = "log"
                data = [username, password]
                protocol_send(self.main_socket, cmd, data)
                self.logging_protocol("send", cmd, data)
                cmd, data = protocol_receive(self.main_socket)
                self.logging_protocol("received", cmd, data)
                if data[0] == "T":
                    self.username = username
                    self.token = data[1]
                    self.is_expired = False
                    self.song_id_dict = pickle.loads(data[2])
                    print(self.song_id_dict)
                    self.liked_song = pickle.loads(data[3])
                    print("liked song")
                    print(self.liked_song)

            if cmd in ("log", "sig") and data[0] == "T":
                print("pt1")
                if not self.player_thread.is_alive():
                    print("pt2")
                    self.player_thread.start()

        except (ConnectionError, OSError) as net_err:
            self.client_log.debug(f"[ERROR] Network error: {net_err}")
            data = ["F", "Network error"]
        except pickle.PickleError as pickle_err:
            self.client_log.debug(f"[ERROR] Data decoding error: {pickle_err}")
            data = ["F", "Data decoding error"]

        except Exception as e:
            self.client_log.debug(f"[ERROR] Unexpected error: {e}")
            data = ["F", "Unexpected error"]
        finally:
            return data

    def listen_song(self, song_id):
        """
        Attempts to play a song by ID. If the song exists locally, it is added to the playback queue.
        Otherwise, it fetches the media server address, downloads the song, and adds it to the queue.
        :param song_id: The ID of the song to listen to.
        """
        try:
            file_path = os.path.join(f"{song_id}.mp3")
            if os.path.exists(file_path):
                self.q.add_to_queue(file_path)
                self.client_log.debug(f"{file_path} was added to queue (local file)")
                return

            # Request address of the media server hosting the song
            data = self.get_address(song_id)
            if data[0] == "T":
                ip = data[1]
                port = int(data[2])
                media_server_address = (ip, port)

                # Attempt to get the song from the media server
                file_name = self.get_song(song_id, media_server_address)
                if file_name != "error":
                    self.q.add_to_queue(file_name)
                    self.client_log.debug(f"{file_name} was added to queue (downloaded)")
                else:
                    self.client_log.error(f"Failed to download song {song_id} from {media_server_address}")
            else:
                self.client_log.error(f"Could not get address for song {song_id}: {data}")
        except Exception as e:
            self.client_log.error(f"Unexpected error in listen_song: {e}")

    def get_address(self, song_id):
        """
        Requests the media server address hosting the specified song from the main server.
        :param song_id: int, the ID of the requested song
        :return: tuple, server response like ("T", ip, port) on success or ("F", error_message) on failure
        """
        try:
            cmd = "gad"
            data = [self.token, song_id]
            protocol_send(self.main_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            cmd, data = protocol_receive(self.main_socket)
            self.logging_protocol("received", cmd, data)

            if data[0] == "F":
                if data[1] in ("Token has expired", "Invalid token"):
                    self.is_expired = True
            return data

        except Exception as e:
            self.client_log.error(f"Error in get_address for song_id {song_id}: {e}")
            return ["F", f"Exception occurred: {str(e)}"]

    def get_song(self, song_id, server_address):
        """
        Downloads the song file from the media server and saves it locally.
        :param song_id: int, the ID of the requested song
        :param server_address: tuple(str, int), IP and port of the media server
        :return: str, filename if downloaded successfully or "error" if failed
        """
        file_path = "error"
        try:
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_server_ip = server_address[0]
            ssl_media_socket = self.create_ssl_socket(media_socket, media_server_ip)
            ssl_media_socket.connect(server_address)
            self.client_log.debug(f"Connection with media server {server_address} successful!")

            cmd = "get"
            data = [self.token, song_id]
            protocol_send(ssl_media_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            cmd, data = protocol_receive(ssl_media_socket)
            self.logging_protocol("received", cmd, data)
            ssl_media_socket.close()

            if data[0] == "F":
                if data[1] in ("Token has expired", "Invalid token"):
                    self.is_expired = True
                self.client_log.warning(f"Failed to get song: {data[1]}")
            else:
                file_name = data[1]
                if file_name != "file not found":
                    file_path = os.path.join(CACHE_FOLDER, file_name)
                    with open(file_path, 'wb') as file:
                        file.write(data[2])
                    self.client_log.debug(f"File saved as {file_name}")
                else:
                    self.client_log.warning(f"Song with ID {song_id} not found on media server.")

        except socket.error as e:
            self.client_log.error(f"Socket error while connecting to media server {server_address}: {e}")

        except Exception as e:
            self.client_log.error(f"Unexpected error in get_song: {e}")

        finally:
            return file_path

    def upload_song(self, song_name, artist, file_path):
        """
        Uploads a new song to the appropriate media server.

        :param song_name: str - name of the song to upload
        :param artist: str - artist name
        :param file_path: str - full path to the song file on local machine
        :return: list - ["T"] on success, or ["F", reason] on failure
        """
        try:
            if not os.path.isfile(file_path):
                return ["F", "file does not exist"]

            # Get media server address for the new song
            data = self.get_address_new_song(song_name, artist)
            print(data)
            if data[0] == "F":
                if data[1] in ("Token has expired", "Invalid token"):
                    self.is_expired = True
                self.client_log.debug(f"Failed to get upload address: {data}")
            elif data[0] == "T":
                song_id = int(data[1])
                ip = data[2]
                port = int(data[3])
                media_server_address = (ip, port)

                post_song_result = self.post_song(file_path, song_id, media_server_address)
                return post_song_result
            else:
                self.client_log.debug(f"Failed to get media server address: {data}")
                return data

        except Exception as e:
            self.client_log.error(f"Exception during upload_song: {e}")
            return ["F", "exception occurred"]

    def get_address_new_song(self, song_name, artist):
        """
        Requests a unique song ID and the address of a media server
        for uploading a new song to the system.

        :param song_name: str - name of the new song
        :param artist: str - name of the artist
        :return: list - server response, e.g. ["T", id, ip, port] or ["F", reason]
        """
        try:
            cmd = "pad"
            data = [self.token, song_name, artist]

            protocol_send(self.main_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            cmd, data = protocol_receive(self.main_socket)  # e.g., "pad", ["T", id, ip, port]
            self.logging_protocol("received", cmd, data)
            return data

        except Exception as e:
            self.client_log.error(f"Exception in get_address_new_song: {e}")
            return ["F", "exception occurred"]

    def post_song(self, file_path, song_id, server_address):
        """
        Uploads a song file to the specified media server.

        :param file_path: str - full path to the song file
        :param song_id: int - unique song ID assigned by the main server
        :param server_address: tuple(str, int) - (IP, port) of the target media server
        :return: list - server response, e.g. ["T"] for success or ["F", reason] on failure
        """
        result = ["F", "error"]
        try:
            # Try connecting to media server
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_server_ip = server_address[0]
            ssl_media_socket = self.create_ssl_socket(media_socket, media_server_ip)
            ssl_media_socket.connect(server_address)
            self.client_log.debug("Connection with media server successful!")

            # Try reading the song file
            try:
                with open(file_path, "rb") as file:
                    song_bytes = file.read()
                    self.client_log.debug(f"Read {len(song_bytes)} bytes from song file.")
            except Exception as file_err:
                self.client_log.error(f"Failed to read song file: {file_err}")
                return ["F", "file read error"]

            # Send upload command
            cmd = "pst"
            data = [self.token, song_id, song_bytes]
            protocol_send(ssl_media_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            # Receive response
            cmd, data = protocol_receive(ssl_media_socket)
            self.logging_protocol("received", cmd, data)
            result = data

            # Check for token-related errors
            if data[0] == "F" and data[1] in ("Token has expired", "Invalid token"):
                self.is_expired = True

            ssl_media_socket.close()

        except socket.error as e:
            self.client_log.error(f"Connection to media server failed: {e}")
            result = ["F", "error connection"]

        except Exception as e:
            self.client_log.error(f"Unexpected error during post_song: {e}")
            result = ["F", "unexpected error"]

        finally:
            return result

    def refresh_song_dict(self):
        """
        Refreshes the local song dictionary by requesting updated data from the main server.

        :return: bool - True if the song dictionary was successfully updated, False otherwise
        """
        try:
            cmd = "rfs"
            data = [self.token]
            protocol_send(self.main_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            cmd, data = protocol_receive(self.main_socket)
            self.logging_protocol("received", cmd, data)

            if data[0] == "T":
                song_dict = pickle.loads(data[1])
                self.song_id_dict = song_dict
                return True
            else:
                return False

        except (ConnectionError, OSError) as net_err:
            self.client_log.error(f"[ERROR] Network error during refresh: {net_err}")
            return False

        except pickle.PickleError as pickle_err:
            self.client_log.error(f"[ERROR] Failed to deserialize song data: {pickle_err}")
            return False

        except Exception as e:
            if self.client_log:
                self.client_log.error(f"[ERROR] Unexpected error in refresh_song_dict: {e}")
            return False

    def song_and_playlist(self, func, playlist_name, song_id):
        """
        Adds or removes a song from a user's playlist on the main server.

        :param func: str - "add" to add song, "remove" to remove song
        :param playlist_name: str - name of the playlist
        :param song_id: str - ID of the song to add or remove
        :return: list - ["T", ...] on success, or ["F", reason] on failure
        """
        try:
            if func == "add":
                cmd = "atp"
                data = [self.token, self.username, playlist_name, song_id]
            elif func == "remove":
                cmd = "rfp"
                data = [self.token, self.username, playlist_name, song_id]
            else:
                raise ValueError("Invalid function type. Expected 'add' or 'remove'.")

            protocol_send(self.main_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            cmd, data = protocol_receive(self.main_socket)
            self.logging_protocol("received", cmd, data)

            if data[0] == "F":
                if data[1] in ("Token has expired", "Invalid token"):
                    self.is_expired = True
                return data

            if data[0] == "T":
                if func == "add" and song_id not in self.liked_song:
                    self.liked_song.append(song_id)
                elif func == "remove" and song_id in self.liked_song:
                    self.liked_song.remove(song_id)
                return data

            return ["F", "Unexpected response format"]

        except (ConnectionError, OSError) as net_err:
            error_msg = f"[ERROR] Network error during song_and_playlist: {net_err}"
            self.client_log.error(error_msg)
            return ["F", error_msg]

        except ValueError as ve:
            self.client_log.error(f"[ERROR] Value error: {ve}")
            return ["F", str(ve)]

        except Exception as e:
            error_msg = f"[ERROR] Unexpected exception in song_and_playlist: {e}"
            self.client_log.error(error_msg)
            return ["F", str(e)]

    def reset(self):
        """
        Resets client state after logout or token expiration.

        :return: None
        """
        self.client_log.debug("reset() called - logging out user")
        try:
            if not self.is_expired:
                cmd = "lgu"
                data = [self.token]
                protocol_send(self.main_socket, cmd, data)
                self.logging_protocol("send", cmd, data)
                self.client_log.debug("Logout request sent to main server.")

            self.q.clear_queue()
            self.username = ""
            self.token = ""
            self.song_id_dict = {}
            self.liked_song = []
            self.is_expired = True
            self.client_log.debug("Client state has been reset.")

        except Exception as e:
            self.client_log.debug(f"Exception occurred during reset: {e}")

    def exit(self):
        """
        Gracefully shuts down the client by notifying the server, closing sockets, and clearing state.

        :return: None
        """
        self.client_log.debug("exit() called - shutting down client")
        try:
            # Attempt to send exit command to server
            cmd = "ext"
            data = [self.token]
            protocol_send(self.main_socket, cmd, data)
            self.logging_protocol("send", cmd, data)
            self.client_log.debug("Exit command sent to main server.")

            # Close main socket safely
            if self.main_socket:
                try:
                    self.main_socket.close()
                    self.client_log.debug("Main socket closed.")
                except Exception as e:
                    self.client_log.debug(f"Error closing socket: {e}")

            # Reset components and state
            self.q = SongsQueue()
            self.p = MusicPlayer()
            self.client_to_gui_queue = queue.Queue()
            self.gui_to_client_queue = queue.Queue()

            self.username = ""
            self.token = ""
            self.song_id_dict = {}
            self.liked_song = []
            self.is_expired = True

            self.client_log.debug("Client state fully reset.")
            print("end of exit")

        except Exception as e:
            self.client_log.debug(f"Exception during exit: {e}")
            print(f"Error during client exit: {e}")

    def setup_playlist(self, playlist):
        """
        Clears the current queue and starts playing the given playlist.

        :param playlist: list - list of songs (paths or objects) to play
        :return: None
        """
        try:
            self.client_log.debug("Starting playlist playback.")
            self.q.clear_queue()
            self.client_log.debug("Cleared current queue.")

            for song in playlist:
                self.listen_song(song)
                self.client_log.debug(f"Added song to queue: {song}")

            self.client_log.debug("Playlist setup completed.")

        except Exception as e:
            self.client_log.debug(f"Error in play_playlist: {e}")
            print(f"Failed to play playlist: {e}")

    def player_func(self):
        """
        Main player thread loop that processes commands from the GUI queue.

        - Handles playback commands: play, pause, resume, next, prev.
        - Clears queues on logout.
        - Shuts down player and deletes files on shutdown.
        - Logs detailed debug information for each action.

        :return: None
        """
        self.player_log.debug("player_thread")
        while True:
            cmd = self.gui_to_client_queue.get()
            self.queue_logging()
            self.player_log.debug(cmd)
            play = False
            if cmd == "play":
                play = True
            if cmd == "pause":
                self.p.pause_song()
                self.player_log.debug("pause song: ")
            elif cmd == "resume":
                self.p.resume_song()
                self.player_log.debug("resume song: ")
            elif cmd == "next":
                if not self.q.my_queue.empty():
                    self.p.stop_song()
                    play = True
            elif cmd == "prev":
                if self.q.prev_song_path != "":
                    self.p.stop_song()
                    play = True
            elif cmd == "logout":
                self.p.stop_song()
                self.player_log.debug("stop song: ")
                while not self.client_to_gui_queue.empty():
                    self.client_to_gui_queue.get()
                while not self.gui_to_client_queue.empty():
                    self.gui_to_client_queue.get()
                self.player_log.debug("clear queues")

            elif cmd == "shutdown":
                self.p.shutdown()
                self.delete_files()
                self.player_log.debug("shut down: ")
                break

            if play:
                print(cmd)
                self.play_loop(cmd)

            self.player_log.debug("*********************************************************************")
        self.player_log.debug("finish player thread")

    def play_loop(self, cmd):
        """
        Plays songs from the queue based on the command until the GUI queue receives new input.

        - Checks for song existence before playing.
        - Sends notification if no songs are available.
        - Logs playback and queue status.

        :param cmd: str - playback command such as 'play' or 'prev'
        :return: None
        """
        while self.gui_to_client_queue.empty():
            if not self.q.my_queue.empty() or (cmd == "prev" and self.q.prev_song_path != ""):
                song_path = self.q.get_song(cmd)
                self.queue_logging()
                if os.path.exists(song_path):
                    self.p.play_song(song_path, self.gui_to_client_queue)  # ניגון השיר מופסק במידה שהגיע פקודה חדשה בתור
                else:
                    self.player_log.debug("song not found")
                cmd = "play"
            else:
                self.player_log.debug("nothing to play")
                self.client_to_gui_queue.put("nothing to play")
                break
        self.player_log.debug(self.q.my_queue.empty())
        self.player_log.debug("play loop has finished")

    def queue_logging(self):
        """
        Logs the current state of the song queue and player pause status.
        :return: None
        """
        msg_queue = list(self.q.my_queue.queue)
        for i in msg_queue:
            i = str(i)
        msg_queue = ', '.join(msg_queue)

        msg = f"paused: {self.p.is_paused}::::: recent: {self.q.recent_song_path}, previous: {self.q.prev_song_path}, old: {self.q.old_song_path}, queue: {msg_queue}"
        self.player_log.debug(msg)

    def delete_files(self):
        """
        Deletes temporary or old song files stored in the queue and other tracked paths.
        Checks if each file exists before attempting removal.
        """
        try:
            self.player_log.debug("deleting files")
            while not self.q.my_queue.empty():
                file_path = self.q.my_queue.get()
                if os.path.exists(file_path):
                    os.remove(file_path)

            if os.path.exists(self.q.old_song_path):
                os.remove(self.q.old_song_path)
            if os.path.exists(self.q.prev_song_path):
                os.remove(self.q.prev_song_path)
            if os.path.exists(self.q.recent_song_path):
                print(self.q.recent_song_path)
                os.remove(self.q.recent_song_path)
        except Exception as e:
            self.player_log.error(f"Error deleting files: {e}")