from database import DataBase
import random
import socket
from protocol import protocol_receive
from protocol import protocol_send
import os
import jwt
import datetime

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
        self.create_table("playlists", playlists_columns, foreign_key)

#signup
    def add_user(self, username, password):
        data = {"username": username, "password": password}
        self.insert("users", data)

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
        index = random.randint(0, len(self.address_list)-1)
        return self.address_list[index]

    #post song
    def add_song(self, song_name, artist):
        data = {"name": song_name, "artist": artist}
        address = self.find_address()
        ip = address[0]
        port = address[1]
        data["IP1"] = address[0]
        data["port1"] = address[1]
        data["setting1"] = "pending"
        self.insert("songs", data)
        song_id = self.select("songs", "id", {"name": song_name, "artist": artist})
        print(song_id)
        return song_id, ip, port


    #get
    def get_address(self, song_id):
        song = self.select("songs", '*', {"id": song_id})
        song = song[0]
        print(song)
        if song is not None:
            ip1 = song[3]
            port1 = song[4]
            set1 = song[5]
            ip2 = song[6]
            port2 = song[7]
            set2 = song[8]
            if set1 == "verified":
                return ip1, port1
            elif set2 == "verified":
                return ip2, port2
            else:
                return None
        else:
            return None




    def get_song(self, token, song_id, server_address):
        """

        :param song_id: int
        :param server_address: tuple of ip(str) and port(int)
        :return:
        """
        file_name = "error"
        try:
            print(server_address)
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_socket.connect(server_address)
            print("Connection with media server successful!")
            protocol_send(media_socket, "get", [token, song_id])
            cmd, data = protocol_receive(media_socket) # "get" , [file_name, file_bytes]
            media_socket.close()
            file_name = data[0]
            if file_name != "error":
                with open(file_name, 'wb') as file:
                    file.write(data[1])
                print(f"File saved as {file_name}")

        except socket.error as e:
            print(f"Connection failed: {e}")

        finally:
            print("file_name" + file_name)
            return file_name

    def post_song(self, file_path, id, server_address, token):
        """

        :param file_path: str
        :param id: int
        :param server_address: tuple of ip(str) and port(int)
        :return:
        """
        val = "error"
        try:
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_socket.connect(server_address)
            with open(file_path, "rb") as file:
                song_bytes = file.read()
            print("reading the file after getting it from server 1")
            print(len(song_bytes))

            cmd = "pst"
            data = [token, id, song_bytes]
            protocol_send(media_socket, cmd, data)

            cmd, data = protocol_receive(media_socket)
            if data[0] == "error":
                val = False
            else:
                val = data[0]
                media_socket.close()

        except socket.error as e:
            print(f"Connection failed: {e}")
        finally:
            return val


    def verify_and_backup_songs(self, token, ADDRESS_LIST):
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
                    ip1 = song[3]
                    port1 = song[4]

                    # ניסיון לקבל את השיר מהשרת
                    file_name = self.get_song(token, song_id, (ip1, int(port1)))
                    if file_name != "error":
                        self.update("songs", {"setting1": "verified"}, {"id": song_id})

                        # אם השיר נמצא רק בשרת אחד, מבצעים גיבוי
                        #if song in songs_in_one_server:
                        address = (ip1, port1)
                        temp = False
                        print(temp)
                        while not temp:
                            address2 = self.find_address()
                            if address2 != address:
                                temp = True
                        print(address2)
                        self.post_song(file_name, song_id, address2, token)

                except ValueError as e:
                    print(f"Error converting port to integer for song ID {song_id}: {e}")
                except Exception as e:
                    print(f"Unexpected error processing song ID {song_id}: {e}")

        except Exception as e:
            print(f"Database or connection error in verify_songs: {e}")


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


