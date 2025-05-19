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

LOG_DIR = 'log'
LOG_FILE_CLIENT = os.path.join(LOG_DIR, 'client.log')
LOG_FILE_PLAYER = os.path.join(LOG_DIR, 'player.log')
LOG_FORMAT = '%(levelname)s | %(asctime)s | %(name)s | %(message)s'


class Client:
    def __init__(self, ip, port):
        """
        Initialize the Client object.

        :param ip: str, the IP address of the main server
        :param port: int, the port number of the main server
        """
        try:
            if not os.path.isdir(LOG_DIR):
                os.makedirs(LOG_DIR)

            self.client_log = self.setup_logger("ClientLogger", LOG_FILE_CLIENT)
            self.player_log = self.setup_logger("PlayerLogger", LOG_FILE_PLAYER)

            self.MAIN_SERVER_ADDR = (ip, port)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.main_socket = context.wrap_socket(temp_socket, server_hostname=ip)
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

    def setup_logger(self, name, log_file):
        """
        Set up a logger that logs to a specific file.

        :param name: str, logger name
        :param log_file: str, path to the log file
        :return: logger object
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
        Starts the client login or signup process with the main server.

        Depending on the command, this method sends a signup or login request
        to the main server using the provided username and password. If the
        response from the server is successful (indicated by "T"), the client's
        session is initialized with the username, authentication token, and
        song data.

        Additionally, the method ensures that the player thread is running
        (starts it if not already alive) so that the client can handle music playback.

        Parameters:
            cmd (str): Command indicating the action. "1" for signup, "2" for login.
            username (str): The username to sign up or log in with.
            password (str): The corresponding password.

        Returns:
            list: The response data from the server (e.g., ["T", token, ...] or ["F", reason]).
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
        Sends the main server a song ID and receives the address of the media server that hosts the song.

        :param song_id: int - The ID of the requested song.
        :return: tuple - Response from the server, e.g. ("T", ip, port) on success, or ("F", error_message) on failure.
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
            # מחזיר תגובה שמדגימה כישלון כדי שהקריאה בפונקציה שמעבירה את התוצאה תוכל לטפל בזה
            return ["F", f"Exception occurred: {str(e)}"]

    def get_song(self, song_id, server_address):
        """
        Requests the song file from the given media server address and saves it locally.

        :param song_id: int - The ID of the requested song.
        :param server_address: tuple(str, int) - The IP address and port of the media server.
        :return: str - The filename if the song was successfully downloaded and saved,
                       or "error" if there was a failure.
        """
        file_name = "error"
        try:
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_socket.connect(server_address)
            self.client_log.debug(f"Connection with media server {server_address} successful!")

            cmd = "get"
            data = [self.token, song_id]
            protocol_send(media_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            cmd, data = protocol_receive(media_socket)
            self.logging_protocol("received", cmd, data)
            media_socket.close()

            if data[0] == "F":
                if data[1] in ("Token has expired", "Invalid token"):
                    self.is_expired = True
                self.client_log.warning(f"Failed to get song: {data[1]}")
            else:
                file_name = data[1]
                if file_name != "not found":
                    with open(file_name, 'wb') as file:
                        file.write(data[2])
                    self.client_log.debug(f"File saved as {file_name}")
                else:
                    self.client_log.warning(f"Song with ID {song_id} not found on media server.")

        except socket.error as e:
            self.client_log.error(f"Socket error while connecting to media server {server_address}: {e}")

        except Exception as e:
            self.client_log.error(f"Unexpected error in get_song: {e}")

        finally:
            return file_name

    def upload_song(self, song_name, artist, file_path):
        """
        Upload a song to the appropriate media server.

        This function checks if the provided file exists, requests a media server address
        from the main server to upload the song, and sends the song file to that media server.

        :param song_name: str - the name of the song
        :param artist: str - the artist of the song
        :param file_path: str - path to the local song file
        :return: list - response indicating success or failure, e.g. ["T"] or ["F", "reason"]
        """
        try:
            if not os.path.isfile(file_path):
                return ["F", "file does not exist"]

            # Get media server address for the new song
            data = self.get_address_new_song(song_name, artist)
            if data[0] == "T":
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

            if data[0] == "F":
                if data[1] in ("Token has expired", "Invalid token"):
                    self.is_expired = True
                self.client_log.debug(f"Failed to get upload address: {data}")
            return data

        except Exception as e:
            self.client_log.error(f"Exception in get_address_new_song: {e}")
            return ["F", "exception occurred"]

    def post_song(self, file_path, id, server_address):
        """
        Uploads a song file to the specified media server.

        :param file_path: str - full path to the song file
        :param id: int - unique song ID assigned by the main server
        :param server_address: tuple(str, int) - (IP, port) of the target media server
        :return: list - server response, e.g. ["T"] for success or ["F", reason] on failure
        """
        result = ["F", "error"]
        try:
            # Try connecting to media server
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_socket.connect(server_address)
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
            data = [self.token, id, song_bytes]
            protocol_send(media_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            # Receive response
            cmd, data = protocol_receive(media_socket)
            self.logging_protocol("received", cmd, data)
            result = data

            # Check for token-related errors
            if data[0] == "F" and data[1] in ("Token has expired", "Invalid token"):
                self.is_expired = True

            media_socket.close()

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
        Refresh the local song dictionary by requesting updated song data from the main server.

        This function sends a "rfs" (refresh songs) command along with the user's token to the main server,
        and attempts to receive an updated song dictionary. If the response is successful ("T"),
        the dictionary is deserialized using pickle and stored in self.song_id_dict.

        Returns:
            bool: True if the song dictionary was successfully updated, False otherwise.

        Handles:
            - ConnectionError, OSError: Network-related issues during communication.
            - pickle.PickleError: Issues decoding the received song dictionary.
            - Any other unexpected exception is logged and results in a False return value.
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
        Add or remove a song from a user's playlist on the server.

        This function communicates with the main server to add or remove a song from a specified playlist.
        It uses the token and username for authentication and handles token expiration.

        Parameters:
            func (str): Operation to perform - "add" to add song, "remove" to remove song.
            playlist_name (str): Name of the playlist.
            song_id (str): ID of the song to add/remove.

        Returns:
            list: A response list from the server. ["T", ...] on success, ["F", reason] on failure.

        Handles:
            - Network errors
            - Protocol errors
            - Unexpected exceptions
            - Token expiration
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
        Resets the client state after logout or token expiration.

        - Sends a logout request to the main server if the session is still valid.
        - Clears the local playback queue and user-related data.
        - Marks the client as expired to prevent further actions.

        This method also handles and logs any exceptions that occur during cleanup.
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
        Gracefully shuts down the client.

        - Sends an 'exit' command (`ext`) to the main server to notify of disconnection.
        - Closes the main socket connection safely.
        - Resets the music queue, music player, and internal queues.
        - Clears all user-related state including token, username, liked songs, etc.
        - Marks the client as expired.

        Any exceptions during the shutdown process are caught and logged.
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

    def play_playlist(self, playlist):
        """
        Clears the current song queue and starts playing the given playlist.

        Parameters:
        playlist (list): A list of song metadata (e.g., song paths or song objects) to enqueue and play.

        Behavior:
        - Clears the existing queue to avoid mixing with previous songs.
        - Stops any currently playing song.
        - Enqueues and processes each song in the playlist using `listen_song`.

        Exceptions:
        - Any error during queue manipulation or song playback is caught and logged.
        """
        try:
            self.client_log.debug("Starting playlist playback.")
            self.q.clear_queue()
            self.client_log.debug("Cleared current queue.")

            self.p.stop_song()
            self.client_log.debug("Stopped any currently playing song.")

            for song in playlist:
                self.listen_song(song)
                self.client_log.debug(f"Added song to queue: {song}")

            self.client_log.debug("Playlist setup completed.")

        except Exception as e:
            self.client_log.debug(f"Error in play_playlist: {e}")
            print(f"Failed to play playlist: {e}")



















































    def player_func(self):
        print("player_thread")
        while True: # and not self.is_expired:
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
                    temp = self.client_to_gui_queue.get()
                while not self.gui_to_client_queue.empty():
                    temp = self.gui_to_client_queue.get()
                self.player_log.debug("clear queues")

            elif cmd == "shutdown":
                self.p.shutdown()
                self.player_log.debug("shut down: ")
                break

            if play:
                print(cmd)
                self.play_loop(cmd)

            self.player_log.debug("*********************************************************************")
        self.player_log.debug("finish player thread")

    def play_loop(self, cmd):
        while self.gui_to_client_queue.empty():
            if not self.q.my_queue.empty() or (cmd == "prev" and self.q.prev_song_path != ""):
                song_path = self.q.get_song(cmd)
                self.queue_logging()
                if os.path.exists(song_path):
                    self.p.play_song(song_path, self.gui_to_client_queue) # שהתור ריק השיר מתנגן ושיש בו משהו הפעולה מופסקת
                else:
                    self.player_log.debug("song not found")
                cmd == "play" # after the first time, doing the loop regulary
            else:
                self.player_log.debug("nothing to play")
                self.client_to_gui_queue.put("nothing to play")
                break
        self.player_log.debug("play loop has finished")

    def queue_logging(self):
        msg_queue = list(self.q.my_queue.queue)
        for i in msg_queue:
            i = str(i)
        msg_queue = ', '.join(msg_queue)

        msg = f"paused: {self.p.is_paused}::::: recent: {self.q.recent_song_path}, previous: {self.q.prev_song_path}, old: {self.q.old_song_path}, queue: {msg_queue}"
        self.player_log.debug(msg)