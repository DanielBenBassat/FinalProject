import queue
import os


class SongsQueue:
    def __init__(self):
        """
        Initializes the song queue and tracks recent, previous, and old songs.
        """
        self.my_queue = queue.Queue()  # queue of file paths
        self.previous_songs_stack = []
        self.recent_song_path = ""
        self.prev_song_path = ""
        self.old_song_path = ""

    def add_to_queue(self, file_path):
        """
        Adds a song file path to the queue.

        :param file_path: Path to the song file to add.
        """
        try:
            self.my_queue.put(file_path)
        except Exception as e:
            print(f"Error adding song to queue: {e}")

    def get_song(self, cmd):
        """
        Gets the next song path from the queue, or returns previous song if cmd == "prev".

        :param cmd: Command to determine whether to get previous song ("prev") or next song.
        :return: Path to the song file.
        """
        try:
            if self.recent_song_path != "":
                if cmd == "prev":
                    print("hello from prev")
                    self.put_first(self.recent_song_path)
                    self.recent_song_path = self.prev_song_path
                    self.prev_song_path = self.old_song_path
                    self.old_song_path = ""
                    return self.recent_song_path
                else:
                    if os.path.exists(self.old_song_path) and self.old_song_path != self.recent_song_path:
                        try:
                            os.remove(self.old_song_path)
                        except Exception as e:
                            print(f"Error removing old song file '{self.old_song_path}': {e}")
                    self.old_song_path = self.prev_song_path
                    self.prev_song_path = self.recent_song_path

            while True:
                try:
                    song_path = self.my_queue.get(timeout=1)
                    self.recent_song_path = song_path
                    return song_path
                except queue.Empty:
                    continue
        except Exception as e:
            print(f"Error getting song from queue: {e}")
            return None

    def put_first(self, item):
        """
        Puts the specified item at the front of the queue, preserving the order of existing items.

        :param item: The item (song path) to place first in the queue.
        """
        try:
            temp = []

            # Remove all items from queue into a temp list
            while not self.my_queue.empty():
                temp.append(self.my_queue.get())

            # Put the new item first
            self.my_queue.put(item)

            # Reinsert the previous items back in order
            for elem in temp:
                self.my_queue.put(elem)
        except Exception as e:
            print(f"Error putting item first in queue: {e}")

    def update_previous(self):
        """
        Updates previous song pointers and reorders the queue accordingly.
        """
        try:
            self.put_first(self.recent_song_path)
            self.put_first(self.prev_song_path)
            self.prev_song_path = self.old_song_path
            self.old_song_path = ""
        except Exception as e:
            print(f"Error updating previous songs: {e}")

    def clear_queue(self):
        """
        Clears the song queue and resets all tracking variables.
        """
        try:
            self.recent_song_path = ""
            self.prev_song_path = ""
            self.old_song_path = ""
            while not self.my_queue.empty():
                self.my_queue.get()
        except Exception as e:
            print(f"Error clearing queue: {e}")
