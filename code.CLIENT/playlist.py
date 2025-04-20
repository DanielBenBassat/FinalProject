

class Playlist:
    def __init__(self, name):
        self.name = name
        self.song_list = [] # only songs_id

    def add_song(self, song_id):
        self.song_list.append(song_id)

    def remove_song(self, song_id):
        self.song_list.remove(song_id)

