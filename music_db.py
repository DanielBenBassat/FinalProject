import sqlite3
from database import DataBase
import random
import socket
from protocol import protocol_receive
from protocol import protocol_send

class MusicDB(DataBase):
    def __init__(self, name):
        super().__init__(name)
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

        playlists_columns = {"id" : "INTEGER PRIMARY KEY AUTOINCREMENT",
                             "playlists_name": "TEXT NOT NULL",
                             "user": "TEXT NOT NULL",
                             "songs": "TEXT"}
        foreign_key = [("user","users","id")]
        self.create_table("playlists", playlists_columns, foreign_key)

#signup
    def add_user(self, username, password):
        data = {"username" : username, "password": password}
        self.insert("users", data)

    #login
    def verified_user(self, user_id, username, password):
        """
        :param user_id:
        :param username:
        :param password:
        :return: true if verified and false if not
        """
        details = self.select("users", '*', {"id": user_id})
        if username == details[1]:
            if password == details[2]   :
                return True, "all"
            else:
                return False, "password"
        else:
            return False, "username"

    def all_songs(self):
        dict = {}
        songs = self.select("songs", 'id,name,artist')
        for i in songs:
            name = i[1]
            artist = i[2]
            id = i[0]
            dict[name] = (artist, id)
        return dict
    def find_address(self, address_dict):
        index = random.randint(0, len(address_dict))
        return address_dict[0]


    #post song
    def add_song(self, song_name, artist, address_list):
        data = {"name": song_name, "artist": artist}
        address = self.find_address(address_list)
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
            if set1 == "verified" or set1 == "pending":
                return ip1, port1
            elif set2 == "verified":
                return ip2, port2
            else:
                return None
        else:
            return None

    def verify_songs_pending(self):
        songs_pending = self.select("songs", '*', {"setting1": "pending"})
        for song in songs_pending:
            song_id = song[0]
            ip1 = song[3]
            port1 = song[4]
            check = self.get_song(song_id, (ip1, int(port1)))
            if check != "error":
                self.insert("songs", {"setting1": "verified"})

    def get_song(self, song_id, server_address):
        """

        :param song_id: int
        :param server_address: tuple of ip(str) and port(int)
        :return:
        """
        file_name = "error"
        try:
            media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            media_socket.connect(server_address)
            print("Connection with media server successful!")
            protocol_send(media_socket, "get", [song_id])
            cmd, data = protocol_receive(media_socket) # "get" , [file_name, file_bytes]
            media_socket.close()
            file_name = data[0]
            if file_name != "not found":
                with open(file_name, 'wb') as file:
                    file.write(data[1])
                print(f"File saved as {file_name}")

        except socket.error as e:
            print(f"Connection failed: {e}")

        finally:
            return file_name


    #def add_playlist
    #turn active
    #def create_key(self, user_id):

