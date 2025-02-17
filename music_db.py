import sqlite3
from database import DataBase
import random

class MusicDB(DataBase):
    def __init__(self, name):
        super().__init__(name)
        songs_columns = {"id" : "INTEGER PRIMARY KEY AUTOINCREMENT",
                        "name": "TEXT NOT NULL",
                        "artist" : "TEXT NOT NULL",
                        "address1" :  "TEXT NOT NULL",
                        "setting1": "TEXT NOT NULL",
                        "address2": "TEXT",
                        "setting2": "TEXT"}
        self.create_table("songs", songs_columns)

        users_columns = {"id" : "INTEGER PRIMARY KEY AUTOINCREMENT",
                        "username" : "TEXT NOT NULL",
                        "password": "TEXT NOT NULL",
                        "key" : "TEXT"}
        self.create_table("users", users_columns)

        playlists_columns = {"id" : "INTEGER PRIMARY KEY AUTOINCREMENT",
                            "playlists_name": "TEXT NOT NULL",
                            "user": "TEXT NOT NULL",
                            "songs": "TEXT"}
        foreign_key = ("user","users",id)
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


    def find_address(self, address_dict):
        index = random.randint(0, len(address_dict))
        return address_dict[index]


    #post song
    def add_song(self, song_name, artist, address_list):
        data = {"name": song_name, "artist": artist}
        address = self.find_address(address_list)
        data["address1"] = address
        data["setting1"] = "pending"
        self.insert("users", data)
        return address


    #get
    def get_address(self, song_id):
        song = self.select("songs", '*', {"id": song_id})
        if song is not None:
            add1 = song[3]
            set1 = song [4]
            add2 = song[5]
            set2 = song[6]
            if set1 == "verified":
                return add1
            elif set2 == "verified":
                return add2
            else:
                return None
        else:
            return None



    #def add_playlist
    #turn active
    #def create_key(self, user_id):

