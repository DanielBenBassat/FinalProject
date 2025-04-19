import queue
import os


class SongsQueue:
    def __init__(self):
        self.my_queue = queue.Queue() # queue of file's paths
        self.previous_songs_stack = []
        self.recent_song_path = ""


    def add_to_queue(self, file_path): # main thread
        """
        מוסיף שיר לתור
        """
        self.my_queue.put(file_path)

    def get_song(self):
        """
        מנגן את השיר הבא מהתור
        """
        if self.recent_song_path != "":
            self.update_previous(self.recent_song_path)
        while True:
            try:
                song_path = self.my_queue.get(timeout=1)
                self.recent_song_path = song_path
                return song_path
            except queue.Empty:
                continue

    def update_previous(self, file_path):
        if not self.previous_songs_stack:
            self.previous_songs_stack.append(file_path)
        elif len(self.previous_songs_stack) == 1:
            self.previous_songs_stack.append(file_path)
        else:
            old_file_path = self.previous_songs_stack.pop()
            very_old_file_path = self.previous_songs_stack.pop()
            if os.path.exists(very_old_file_path):
                os.remove(very_old_file_path)
            self.previous_songs_stack.append(old_file_path)
            self.previous_songs_stack.append(file_path)




