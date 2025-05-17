from database import DataBase
import random
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
                            "artist" : "TEXT NOT NULL",
                            "IP1" :  "TEXT NOT NULL",
                            "port1": "INTEGER NOT NULL",
                            "setting1": "TEXT NOT NULL",
                            "IP2" : "TEXT ",
                            "port2": "INTEGER",
                            "setting2": "TEXT"}
        self.create_table("songs", songs_columns)

        users_columns = {"id" : "INTEGER PRIMARY KEY AUTOINCREMENT",
                         "username" : "TEXT NOT NULL",
                         "password": "TEXT NOT NULL",
                         "key": "TEXT"}
        self.create_table("users", users_columns)

        playlists_columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",  # מזהה ייחודי לשורת פלייליסט
            "username": "TEXT NOT NULL",                # מקושר לשם המשתמש
            "playlists_name": "TEXT NOT NULL",
            "song_id": "INTEGER"                        # מקושר לשיר
        }
        foreign_key = [
            ("username", "users", "username"),
            ("song_id", "songs", "id")
        ]
        server_columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "IP":   "TEXT NOT NULL",
            "port": "INTEGER NOT NULL",
            "setting": "TEXT NOT NULL" # active or fallen
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
            data = {"IP": server[0], "port": server[1], "setting": "pending" }
            self.insert("servers", data)

    def setup_logger(self, name, log_file):
        """Set up a logger that logs to a specific file"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        return logger

    def logging_protocol(self, func, cmd, data):
        try:
            msg = func + " : " + cmd
            for i in data:
                if type(i) is not bytes:
                    msg += ", " + str(i)
            self.task_log.debug(msg)
        except Exception as e:  # תפיסת כל סוגי החריגות
            self.task_log.debug(e)
#signup
    def add_user(self, username, password):
    # בדיקה אם המשתמש כבר קיים לפי השם
        existing = self.select("users", where_condition={"username": username})
        if existing:
            print("שם המשתמש כבר קיים")
            return False

        # אם לא קיים, מוסיפים
        self.insert("users", {"username": username, "password": password})
        return True


    #login
    def verified_user(self, username, password):
        """
        :param username:
        :param password:
        :return: true if verified and false if not
        """
        details = self.select("users", '*', {"username": username})
        print(details)
        if details:
            if password == details[0][2]:
                return True, "all"
            else:
                return False, "password"
        else:
            return False, "username"

    def all_songs(self):
        dict = {}
        songs = self.select("songs", 'id,name,artist', {"setting1": "verified"})
        for i in songs:
            name = i[1]
            artist = i[2]
            id = i[0]
            dict[name] = (artist, id)
        return dict

    def find_address(self):
        check = False
        address = ()
        while not check:
            index = random.randint(0, len(self.address_list)-1)
            address = self.address_list[index]
            server = self.select("servers", "*", {"IP": address[0], "port": address[1]})
            setting = server[0][3]  # עמודת setting (index 3)
            if setting == "active":
                check = True
        return address

    #post song
    def add_song(self, song_name, artist):
    # בדיקה אם השיר כבר קיים במסד הנתונים
        existing = self.select("songs", "*", {"name": song_name, "artist": artist})
        if existing:
            print("שיר כבר קיים:", existing)
            return ["False", "existing"]  # או שתחזיר את ה-ID הקיים אם אתה רוצה להשתמש בו

        # המשך רגיל אם השיר לא קיים
        data = {"name": song_name, "artist": artist}
        address = self.find_address()
        ip = address[0]
        port = address[1]
        data["IP1"] = ip
        data["port1"] = port
        data["setting1"] = "pending"
        self.insert("songs", data)

        song_id = self.select("songs", "id", {"name": song_name, "artist": artist})
        print(song_id)
        song_id = str(song_id[0][0])
        return ["True", song_id, ip, port]



    #get
    def get_address(self, song_id):
        song = self.select("songs", '*', {"id": song_id})
        song = song[0]
        print(song)
        if song is not None:
            address1 = (song[3], int(song[4]))
            song_set1 = song[5]
            server1 = self.select("servers", "*", {"IP": address1[0], "port": address1[1]})
            server_set1 = server1[0][3]  # עמודת setting (index 3)

            address2 = (song[6], int(song[7]))
            song_set2 = song[8]

            server2 = self.select("servers", "*", {"IP": address2[0], "port": address2[1]})
            server_set2 = server2[0][3]  # עמודת setting (index 3)

            if song_set1 == "verified" and server_set1 == "active":
                print(address1)
                return address1
            elif song_set2 == "verified" and server_set2 == "active":
                return address2
            else:
                return None
        else:
            return None

    def check_server(self, token):
        try:
            cmd = "hlo"

            for address in self.address_list:
                print(type(address[0]))
                print(type(address[1]))
                data = [token]
                server = self.select("servers", "*", {"IP": address[0], "port": address[1]})
                setting = server[0][3]  # עמודת setting (index 3)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.settimeout(2)  # נניח שאתה רוצה לחכות מקסימום 2 שניות לתגובה
                        s.connect(address)  # address זה tuple של (host, port)

                        protocol_send(s, cmd, data)
                        self.logging_protocol("send", cmd, data)
                        cmd, data = protocol_receive(s)
                        self.logging_protocol("receive", cmd, data)

                        if data[0] == "True":
                            if setting != "active":
                                # עדכון בבסיס הנתונים
                                self.update("servers", {"setting": "active"}, {"IP": address[0], "port": address[1]})
                        else:
                            self.task_log.debug(f"Server {address} responded with unexpected message")

                            if setting != "fallen":
                                self.update("servers", {"setting": "fallen"}, {"IP": address[0], "port": address[1]})

                    except socket.timeout:
                        self.task_log.debug(f"Server {address} timed out.")
                        if setting != "fallen":
                            self.update("servers", {"setting": "fallen"}, {"IP": address[0], "port": address[1]})
        except socket.error as e:
            self.task_log.debug(f"Socket error with server {address}: {e}")
            if setting != "fallen":
                self.update("servers", {"setting": "fallen"}, {"IP": address[0], "port": address[1]})

        finally:
            fallen_servers = self.select("servers", "*", {})
            self.task_log.debug(fallen_servers)



    def verify(self, token):
        """
        מאמת שירים שנמצאים במצב 'pending' ומעדכן את הסטטוס שלהם אם הם זמינים.

        - בודק אילו שירים מסומנים כ-pending במסד הנתונים.
        - מנסה להביא את הקובץ מהשרת שצוין.
        - אם הקובץ נמצא, מעדכן את הסטטוס ל-'verified'.
        - אם השיר נמצא רק בשרת אחד, מבצע גיבוי.

        :raises Exception: במקרה של שגיאה כללית.
        """
        try:
            # שליפת שירים בהמתנה לאימות
            songs_pending = self.select("songs", '*', {"setting1": "pending", "setting2": "pending"}, "OR")
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
                        self.task_log.debug(f"song_id {song_id}, pending")
                        result = self.verify_func(token, song_id, (ip1, int(port1)))
                        self.task_log.debug(result)
                        if result == "found":
                            self.update("songs", {setting: "verified"}, {"id": song_id})
                        elif result == "lost":
                            if setting == "setting2":
                                self.update("songs", {"ip2" : "" , "port2": "", "setting2": ""}, {"id": song_id})
                            elif setting == "setting1":
                                self.update("songs", {"ip1" : "" , "port1": "", "setting1": ""}, {"id": song_id})


                except ValueError as e:
                    print(f"Error converting port to integer for song ID {song_id}: {e}")
                except Exception as e:
                    print(f"Unexpected error processing song ID {song_id}: {e}")

        except Exception as e:
            print(f"Database or connection error in verify_songs: {e}")
    def verify_func(self, token, song_id, server_address):
        """

        :param song_id: int
        :param server_address: tuple of ip(str) and port(int)
        :return:
        """
        try:
            print(server_address)
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_socket.connect(server_address)
            print("Connection with media server successful!")
            cmd = "vrf"
            data = [token, song_id]
            protocol_send(media_socket, cmd, data)
            self.logging_protocol("send", cmd, data )
            cmd, data = protocol_receive(media_socket) # "get" , [file_name, file_bytes]
            self.logging_protocol("recv", cmd, data)
            media_socket.close()
            return data[0]


        except socket.error as e:
            print(f"Connection failed: {e}")

        #finally:
        #   print("file_name" + file_name)
    def backup_songs(self, token, token2):
        songs_verified = self.select("songs", '*', {"setting1": "verified", "setting2": "verified"}, "OR")
        # אם השיר נמצא רק בשרת אחד, מבצעים גיבוי
        for song in songs_verified:
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
                address = (ip1, int(port1)) #הכתובת שהשיר נמצא כרגע
                temp = False
                while not temp:
                    address2 = self.find_address() # כתובת חדשה לגיבוי השיר
                    if address2 != address:
                        temp = True
                self.task_log.debug(song)
                val = self.backup_func(token, token2, song_id, address, address2)
                if val:
                    data = {"ip2": address2[0], "port2": address2[1]}
                    data[setting] = "pending"
                    self.update("songs", data, {"id": int(song_id)})

    def backup_func(self, token, token2, id, server1, server2):
        val = False
        try:
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_socket.connect(server1)

            cmd = "bkg"
            data = [token, token2, id, server2[0], server2[1]]
            protocol_send(media_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            media_socket.close()
            val = True
        except socket.error as e:
            print(f"Connection failed: {e}")
        finally:
            return val
    def add_to_playlist(self, username, playlist_name, song_id):
        # בדיקה אם המשתמש קיים
        user_exists = self.select("users", where_condition={"username": username})
        if not user_exists:
            print(f"שגיאה: המשתמש '{username}' לא קיים.")
            return f"Error: User '{username}' does not exist."

        # בדיקה אם השיר קיים
        song_exists = self.select("songs", where_condition={"id": song_id})
        if not song_exists:
            print(f"שגיאה: שיר עם מזהה {song_id} לא קיים.")
            return f"Error: Song with ID {song_id} does not exist."

        # בדיקה אם השיר כבר בפלייליסט
        song_in_playlist = self.select("playlists", where_condition={
            "username": username,
            "playlists_name": playlist_name,
            "song_id": song_id
        })
        if song_in_playlist:
            print(f"השיר כבר קיים בפלייליסט '{playlist_name}' של המשתמש '{username}'.")
            return f"Error: Song {song_id} is already in playlist '{playlist_name}' for user '{username}'."

        # הוספת השיר לפלייליסט
        data = {
            "username": username,
            "playlists_name": playlist_name,
            "song_id": song_id
        }
        self.insert("playlists", data)

        print(f"✅ השיר {song_id} נוסף לפלייליסט '{playlist_name}' של המשתמש '{username}'.")
        return True

    def remove_from_playlist(self, username, playlist_name, song_id):
        # בדיקה אם המשתמש קיים
        user_exists = self.select("users", where_condition={"username": username})
        if not user_exists:
            print(f"שגיאה: המשתמש '{username}' לא קיים.")
            return f"Error: User '{username}' does not exist."

        # בדיקה אם השיר קיים
        song_exists = self.select("songs", where_condition={"id": song_id})
        if not song_exists:
            print(f"שגיאה: שיר עם מזהה {song_id} לא קיים.")
            return f"Error: Song with ID {song_id} does not exist."

        # בדיקה אם השיר לא קיים בפלייליסט
        song_in_playlist = self.select("playlists", where_condition={
            "username": username,
            "playlists_name": playlist_name,
            "song_id": song_id
        })
        if not song_in_playlist:
            print(f"שגיאה: השיר {song_id} לא נמצא בפלייליסט '{playlist_name}' של המשתמש '{username}'.")
            return f"Error: Song {song_id} is not in playlist '{playlist_name}' for user '{username}'."

        # הסרת השיר מהפלייליסט
        self.delete("playlists", where={
            "username": username,
            "playlists_name": playlist_name,
            "song_id": song_id})

        print(f"✅ השיר {song_id} הוסר מפלייליסט '{playlist_name}' של המשתמש '{username}'.")
        return True



    def get_user_playlists(self, username, playlist_name):
        # שליפת מזהי שירים מהפלייליסט
        playlist_entries = self.select(
            "playlists",
            fields="song_id",
            where_condition={
                "username": username,
                "playlists_name": playlist_name
            }
        )

        # שליפה כושלת או ריק
        if not playlist_entries:
            return []

        # הפקת מזהים מתוך התוצאה
        song_ids = []
        for entry in playlist_entries:
            song_ids.append(entry[0])
        return song_ids


