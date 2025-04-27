import queue
import os


class SongsQueue:
    def __init__(self):
        self.my_queue = queue.Queue() # queue of file's paths
        self.previous_songs_stack = []
        self.recent_song_path = ""
        self.prev_song_path = ""
        self.old_song_path = ""



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
            if os.path.exists(self.old_song_path) and self.old_song_path != self.recent_song_path  :
                os.remove(self.old_song_path)
            self.old_song_path = self.prev_song_path
            self.prev_song_path = self.recent_song_path
        while True:
            try:
                song_path = self.my_queue.get(timeout=1)
                self.recent_song_path = song_path
                print("now: " + self.recent_song_path)
                print("prev: " + self.prev_song_path)
                return song_path
            except queue.Empty:
                continue

    def put_first(self, item):
        temp = []

    # הוצאת כל האיברים מהתור לתוך רשימה זמנית
        while not self.my_queue.empty():
            temp.append(self.my_queue.get())

        # הכנסה של האיבר החדש ראשון
        self.my_queue.put(item)

        # הכנסה מחדש של כל האיברים הקודמים, לפי הסדר
        for elem in temp:
            self.my_queue.put(elem)

    def update_previous(self):
        #מחזיר את השיר הנוכחי לראש התור
        self.put_first(self.recent_song_path)
        #self.put_first(self.prev_song_path)
        self.recent_song_path = self.prev_song_path
        self.prev_song_path = self.old_song_path
        self.old_song_path = ""
        return  self.recent_song_path








