from database import DataBase
import socket
from protocol import protocol_receive
from protocol import protocol_send
import os
import logging

LOG_DIR = 'log2'
LOG_FILE_TASK = os.path.join(LOG_DIR, 'background_task.log')
LOG_FILE_DB = os.path.join(LOG_DIR, 'music_db.log')
LOG_FORMAT = '%(levelname)s | %(asctime)s | %(name)s | %(message)s'


class MusicDB(DataBase):
    def __init__(self, name, address_list):
        super().__init__(name)
        self.address_list = address_list
        songs_columns = {"id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                         "name": "TEXT NOT NULL",
                         "artist": "TEXT NOT NULL",
                         "IP1":  "TEXT NOT NULL",
                         "port1": "INTEGER NOT NULL",
                         "setting1": "TEXT NOT NULL",
                         "IP2": "TEXT ",
                         "port2": "INTEGER",
                         "setting2": "TEXT"}
        self.create_table("songs", songs_columns)

        users_columns = {"id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                         "username": "TEXT NOT NULL",
                         "password": "TEXT NOT NULL",
                         "key": "TEXT"}
        self.create_table("users", users_columns)

        playlists_columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "username": "TEXT NOT NULL",
            "playlists_name": "TEXT NOT NULL",
            "song_id": "INTEGER"
        }
        foreign_key = [
            ("username", "users", "username"),
            ("song_id", "songs", "id")
        ]
        server_columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "IP":   "TEXT NOT NULL",
            "port": "INTEGER NOT NULL",
            "setting": "TEXT NOT NULL"
        }
        self.create_table("servers", server_columns)
        existing_servers = self.select("servers")
        if not existing_servers:
            self.insert_server_columns()

        self.create_table("playlists", playlists_columns, foreign_key)
        self.task_log = self.setup_logger("TaskLogger", LOG_FILE_TASK)
        self.music_db_log = self.setup_logger("dbLogger", LOG_FILE_DB)

    def insert_server_columns(self):
        for server in self.address_list:
            data = {"IP": server[0], "port": server[1], "setting": "pending"}
            self.insert("servers", data)

    @staticmethod
    def setup_logger(name, log_file):
        """Set up a logger that logs to a specific file"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

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
# **********************************************************************************************88

    def add_user(self, username, password):
        """
        Adds a new user to the "users" table if the username does not already exist.

        :param username: The username string to add.
        :param password: The password string for the user.
        :return: True if the user was added successfully, False if the username already exists or on error.
        """
        try:
            existing = self.select("users", where_condition={"username": username})
            if existing:
                self.music_db_log.debug("Username already exists")
                return False

            # Insert new user if username not found
            self.insert("users", {"username": username, "password": password})
            return True
        except Exception as e:
            self.music_db_log.debug(f"Error adding user: {e}")
            return False

    def verified_user(self, username, password):
        """
        Verifies if a user exists with the given username and password.

        :param username: The username to verify.
        :param password: The password to verify.
        :return: Tuple (bool, str)
            - True and "all" if username and password match.
            - False and "password" if username exists but password is incorrect.
            - False and "username" if username does not exist.
        """
        try:
            details = self.select("users", '*', {"username": username})
            self.music_db_log.debug(details)
            if details:
                if password == details[0][2]:
                    return True, "all"
                else:
                    return False, "password"
            else:
                return False, "username"
        except Exception as e:
            self.music_db_log.debug(f"Error verifying user: {e}")
            return False, "error"

    def all_songs(self):
        """
        Retrieves all songs from the 'songs' table where either 'setting1' or 'setting2' is 'verified'.

        Returns: dict: A dictionary where each key is a song name and the value is a tuple (artist, id).
        """
        song_dict = {}
        try:
            songs = self.select("songs", 'id,name,artist', {"setting1": "verified", "setting2": "verified"}, "OR")
            for i in songs:
                name = i[1]
                artist = i[2]
                song_id = i[0]
                song_dict[name] = (artist, song_id)
        except Exception as e:
            self.music_db_log.debug(f"Error in all_songs: {e}")
        return song_dict

# ******************************************************************************
    def find_address(self):
        """
        Randomly selects an active server address from the address list.

        This method continuously picks a random address (IP, port) from self.address_list,
        queries the 'servers' table to check if the server at that address has a setting
        of "active". It loops until it finds an active server.

        Returns:
            tuple: (IP, port) of an active server if found.
            None: If an exception occurs during the process.
        """
        import random
        check = False
        address = ()

        while not check:
            try:
                index = random.randint(0, len(self.address_list)-1)
                address = self.address_list[index]
                server = self.select("servers", "*", {"IP": address[0], "port": address[1]})
                setting = server[0][3]  # Index 3 corresponds to the 'setting' column
                if setting == "active":
                    check = True
            except Exception as e:
                self.music_db_log.debug(f"Error in find_address: {e}")
                return None

        return address

    def add_song(self, song_name, artist):
        """
        Adds a new song entry to the database if it does not already exist.

        :param song_name: Name of the song to add.
        :param artist: Artist name of the song.
        :return:
            - ["F", "existing"] if the song already exists.
            - ["T", song_id, ip, port] on successful insertion, with the new song's ID and server address.
        """
        try:
            existing = self.select("songs", "*", {"name": song_name, "artist": artist})
            if existing:
                self.music_db_log.debug(f"add_song: Song already exists: {existing}")
                print("שיר כבר קיים:", existing)
                return ["F", "existing"]

            data = {"name": song_name, "artist": artist}
            address = self.find_address()
            if not address:
                self.music_db_log.debug("add_song: No active server address found.")
                return ["F", "no_server"]

            ip = address[0]
            port = address[1]
            data["IP1"] = ip
            data["port1"] = port
            data["setting1"] = "pending"
            self.insert("songs", data)

            song_id = self.select("songs", "id", {"name": song_name, "artist": artist})
            if not song_id:
                self.music_db_log.debug(f"add_song: Failed to retrieve song ID after insertion for {song_name} - {artist}")
                return ["F", "insert_failed"]

            song_id = str(song_id[0][0])
            self.music_db_log.debug(f"add_song: Added song '{song_name}' by '{artist}' with ID {song_id} at {ip}:{port}")
            print(song_id)
            return ["T", song_id, ip, port]

        except Exception as e:
            self.music_db_log.debug(f"add_song: Exception occurred adding song '{song_name}' by '{artist}' - {e}")
            return ["F", "error"]

    def get_address(self, song_id):
        """
        Retrieves an active server address (IP, port) that hosts the song with the given song_id.

        Checks two possible server addresses associated with the song and returns the first one
        where both the song's setting is "verified" and the server's setting is "active".

        :param song_id: The ID of the song to find the server address for.
        :return: Tuple (IP, port) of the active server hosting the song, or None if none found or song doesn't exist.
        """
        try:
            song = self.select("songs", '*', {"id": song_id})
            if not song:
                self.music_db_log.debug(f"get_address: No song found with id {song_id}")
                return None

            song = song[0]
            self.music_db_log.debug(f"get_address: Retrieved song record: {song}")

            address1 = (song[3], int(song[4]))
            song_set1 = song[5]
            server1 = self.select("servers", "*", {"IP": address1[0], "port": address1[1]})
            server_set1 = server1[0][3]  # setting column index

            address2 = (song[6], int(song[7]))
            song_set2 = song[8]
            server2 = self.select("servers", "*", {"IP": address2[0], "port": address2[1]})
            server_set2 = server2[0][3]

            if song_set1 == "verified" and server_set1 == "active":
                self.music_db_log.debug(f"get_address: Returning address1 {address1}")
                return address1
            elif song_set2 == "verified" and server_set2 == "active":
                self.music_db_log.debug(f"get_address: Returning address2 {address2}")
                return address2
            else:
                self.music_db_log.debug(f"get_address: No active server found for song_id {song_id}")
                return None

        except Exception as e:
            self.music_db_log.debug(f"get_address: Exception occurred for song_id {song_id} - {e}")
            return None

    # ******************************************************************************
    def add_to_playlist(self, username, playlist_name, song_id):
        """
        Add a song to a user's playlist if the song exists and is not already in the playlist.

        :param username: The username owning the playlist.
        :param playlist_name: The name of the playlist.
        :param song_id: The ID of the song to add.
        :return: ["T"] on success, ["F", error_message] on failure.
        """
        try:
            # Check if song exists
            song_exists = self.select("songs", where_condition={"id": song_id})
            if not song_exists:
                msg = f"Error: Song with ID {song_id} does not exist."
                self.music_db_log.debug(msg)
                print(msg)
                return ["F", "Song with ID does not exist"]

            # Check if song is already in playlist
            song_in_playlist = self.select("playlists", where_condition={
                "username": username,
                "playlists_name": playlist_name,
                "song_id": song_id
            })
            if song_in_playlist:
                msg = f"Song already exists in playlist '{playlist_name}' for user '{username}'."
                self.music_db_log.debug(msg)
                print(msg)
                return ["F", "Song is already in playlist"]

            # Add song to playlist
            data = {
                "username": username,
                "playlists_name": playlist_name,
                "song_id": song_id
            }
            self.insert("playlists", data)
            msg = f"✅ Song {song_id} added to playlist '{playlist_name}' for user '{username}'."
            self.music_db_log.debug(msg)
            print(msg)
            return ["T"]
        except Exception as e:
            self.music_db_log.debug(f"add_to_playlist exception: {e}")
            return ["F", "error"]

    def remove_from_playlist(self, username, playlist_name, song_id):
        """
        Remove a song from a user's playlist if the song exists and is in the playlist.

        :param username: The username owning the playlist.
        :param playlist_name: The name of the playlist.
        :param song_id: The ID of the song to remove.
        :return: ["T"] on success, ["F", error_message] on failure.
        """
        try:
            # Check if song exists
            song_exists = self.select("songs", where_condition={"id": song_id})
            if not song_exists:
                msg = f"Error: Song with ID {song_id} does not exist."
                self.music_db_log.debug(msg)
                print(msg)
                return ["F", "Song with ID does not exist"]

            # Check if song is in playlist
            song_in_playlist = self.select("playlists", where_condition={
                "username": username,
                "playlists_name": playlist_name,
                "song_id": song_id
            })
            if not song_in_playlist:
                msg = f"Error: Song {song_id} not found in playlist '{playlist_name}' for user '{username}'."
                self.music_db_log.debug(msg)
                print(msg)
                return ["F", "Song is not in playlist"]

            # Remove song from playlist
            self.delete("playlists", where={
                "username": username,
                "playlists_name": playlist_name,
                "song_id": song_id
            })
            msg = f"✅ Song {song_id} removed from playlist '{playlist_name}' for user '{username}'."
            self.music_db_log.debug(msg)
            print(msg)
            return ["T"]
        except Exception as e:
            self.music_db_log.debug(f"remove_from_playlist exception: {e}")
            return ["F", "error"]

    def get_user_playlists(self, username, playlist_name):
        """
       Retrieve all song IDs in a user's specified playlist.

       :param username: The username owning the playlist.
       :param playlist_name: The name of the playlist.
       :return: List of song IDs in the playlist, or empty list if none or on error.
       """
        try:
            # Retrieve song IDs from playlist
            playlist_entries = self.select(
                "playlists",
                fields="song_id",
                where_condition={
                    "username": username,
                    "playlists_name": playlist_name
                }
            )
            if not playlist_entries:
                return []
            return playlist_entries
        except Exception as e:
            self.music_db_log.debug(f"get_user_playlists exception: {e}")
            return []

# ****************************************************************
    def check_server(self, token):
        """
        Checks each server in self.address_list by sending a 'hlo' command with the given token.
        Updates the server's setting to 'active' if response data[0] == "T", otherwise 'fallen'.

        :param token: Token string sent to servers for verification.
        """
        setting = None
        address = None
        try:
            cmd = "hlo"
            for address in self.address_list:
                data = [token]
                server = self.select("servers", "*", {"IP": address[0], "port": address[1]})
                setting = server[0][3]  # setting column index

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.settimeout(2)  # Max wait time 2 seconds
                        s.connect(address)  # address is (host, port) tuple

                        protocol_send(s, cmd, data)
                        cmd_resp, data_resp = protocol_receive(s)

                        if data_resp[0] == "T":
                            if setting != "active":
                                self.task_log.debug(f"Server {address} responded with 'T'. Marking as active.")
                                self.update("servers", {"setting": "active"}, {"IP": address[0], "port": address[1]},)
                        else:
                            self.task_log.debug(
                                f"Server {address} responded with unexpected message: {data_resp}"
                            )
                            if setting != "fallen":
                                self.update("servers", {"setting": "fallen"}, {"IP": address[0], "port": address[1]},)

                    except socket.timeout:
                        self.task_log.debug(f"Server {address} timed out.")
                        if setting != "fallen":
                            self.update("servers", {"setting": "fallen"}, {"IP": address[0], "port": address[1]},)

        except socket.error as e:
            self.task_log.debug(f"Socket error with server address: {e}")
            if setting is not None and setting != "fallen" and address is not None:
                self.update("servers", {"setting": "fallen"}, {"IP": address[0], "port": address[1]},)

        finally:
            fallen_servers = self.select("servers", "*", {"setting": "fallen"})
            self.task_log.debug(f"Current servers state: {fallen_servers}")

    def verify_songs(self, token):
        """
        Verify songs that are in 'pending' status and update their status if available.
        """
        try:
            # Fetch songs pending verification
            songs_pending = self.select("songs", '*', {"setting1": "pending", "setting2": "pending"}, "OR")
            self.task_log.debug(f"Found {len(songs_pending)} pending songs to verify.")
            for song in songs_pending:
                try:
                    song_id = str(song[0])
                    setting = ""
                    if song[5] == "pending":
                        ip1 = song[3]
                        port1 = song[4]
                        setting = "setting1"
                    elif song[8] == "pending":
                        ip1 = song[6]
                        port1 = song[7]
                        setting = "setting2"

                    if setting != "":
                        self.task_log.debug(f"Verifying song_id {song_id} at {ip1}:{port1} ({setting})")
                        result = self.verify_songs_func(token, song_id, (ip1, int(port1)))
                        self.task_log.debug(f"Verification result for song_id {song_id}: {result}")

                        if result[1] == "found":
                            self.update("songs", {setting: "verified"}, {"id": song_id})
                            self.task_log.info(f"Song ID {song_id} verified successfully on {setting}.")
                        elif result[1] == "lost":
                            self.task_log.warning(f"Song ID {song_id} lost on {setting}, clearing data.")
                            if setting == "setting2":
                                self.update("songs", {"ip2": "", "port2": "", "setting2": ""}, {"id": song_id})
                            elif setting == "setting1":
                                self.update("songs", {"ip1": "", "port1": "", "setting1": ""}, {"id": song_id})

                except ValueError as e:
                    err_msg = f"Error converting port to integer for song ID {e}"
                    self.task_log.error(err_msg)
                    print(err_msg)
                except Exception as e:
                    err_msg = f"Unexpected error processing song ID {e}"
                    self.task_log.error(err_msg)
                    print(err_msg)

        except Exception as e:
            err_msg = f"Database or connection error in verify_songs: {e}"
            self.task_log.error(err_msg)
            print(err_msg)

    def verify_songs_func(self, token, song_id, server_address):
        """
        Verify availability of a song file on a media server.

        :param token: Authentication token
        :param song_id: int - ID of the song to verify
        :param server_address: tuple (ip:str, port:int) of media server
        :return: response data from server, or None on failure
        """
        try:
            self.task_log.debug(f"Connecting to media server at {server_address} for song ID {song_id}")
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_socket.connect(server_address)
            self.task_log.info("Connection with media server successful!")
            cmd = "vrf"
            data = [token, song_id]
            protocol_send(media_socket, cmd, data)
            self.logging_protocol("send", cmd, data)
            cmd, data = protocol_receive(media_socket)  # "get", [file_name, file_bytes]
            self.logging_protocol("recv", cmd, data)
            media_socket.close()
            return data

        except socket.error as e:
            err_msg = f"Connection failed to media server {server_address}: {e}"
            self.task_log.error(err_msg)
            print(err_msg)

    def backup_songs(self, token, token2):
        """
        Backup songs that are verified but exist on only one server.

        - Checks for songs in 'verified' status.
        - If the song exists only on one server, finds a new backup address and starts the backup process.
        """
        try:
            songs_verified = self.select("songs", '*', {"setting1": "verified", "setting2": "verified"}, "OR")
            self.task_log.debug(f"Found {len(songs_verified)} verified songs to consider for backup.")
            for song in songs_verified:
                try:
                    song_id = str(song[0])
                    setting = ""
                    if song[5] == "verified" and (song[8] is None or song[8] == ""):
                        ip1 = song[3]
                        port1 = song[4]
                        setting = "setting2"
                    elif song[8] == "verified" and (song[5] is None or song[5] == ""):
                        ip1 = song[6]
                        port1 = song[7]
                        setting = "setting1"

                    if setting != "":
                        address = (ip1, int(port1))  # current address of the song
                        temp = False
                        while not temp:
                            address2 = self.find_address()  # new address for backup
                            if address2 != address:
                                temp = True
                        self.task_log.debug(f"Backing up song {song_id} from {address} to {address2}")
                        val = self.backup_func(token, token2, song_id, address, address2)
                        if val:
                            data = {"ip2": address2[0], "port2": address2[1]}
                            data[setting] = "pending"
                            self.update("songs", data, {"id": int(song_id)})
                except Exception as e:
                    self.task_log.error(f"Error backing up song {e}")
                    print(f"Error backing up song {e}")
        except Exception as e:
            err_msg = f"Error during backup_songs process: {e}"
            self.task_log.error(err_msg)
            print(err_msg)

    def backup_func(self, token, token2, song_id, server1, server2):
        """
        Sends a backup command to a media server to copy a song from one server to another.

        :param token: Authentication token for the source server
        :param token2: Authentication token for the destination server
        :param song_id: ID of the song to be backed up
        :param server1: Tuple (IP, port) of the source media server where the song currently exists
        :param server2: Tuple (IP, port) of the target media server for backup
        :return: True if the backup command was successfully sent, False otherwise
        """
        val = False
        try:
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_socket.connect(server1)

            cmd = "bkg"
            data = [token, token2, song_id, server2[0], server2[1]]
            protocol_send(media_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            media_socket.close()
            val = True
            self.task_log.info(f"Backup command sent for song ID {song_id} from {server1} to {server2}")
        except socket.error as e:
            err_msg = f"Connection failed during backup for song ID {song_id}: {e}"
            self.task_log.error(err_msg)
            print(err_msg)
        finally:
            return val
