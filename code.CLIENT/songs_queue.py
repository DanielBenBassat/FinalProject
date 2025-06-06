import queue
import os


class SongsQueue:
    def __init__(self):
        """
        Initializes the song queue and tracks recent, previous, and old songs.
        """
        #self.tests()
        self.my_queue = queue.Queue()  # queue of file paths
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


    def tests(self):
        sq = SongsQueue()

        # Test add_to_queue and get_song
        sq.add_to_queue("song1.mp3")
        sq.add_to_queue("song2.mp3")

        # First get_song call should return "song1.mp3"
        song = sq.get_song(cmd="next")
        assert song == "song1.mp3", "First song should be 'song1.mp3'"

        # Second get_song call should return "song2.mp3"
        song = sq.get_song(cmd="next")
        assert song == "song2.mp3", "Second song should be 'song2.mp3'"

        # Test previous song functionality
        sq.prev_song_path = "prev_song.mp3"
        sq.old_song_path = "old_song.mp3"
        sq.recent_song_path = "song2.mp3"

        prev_song = sq.get_song(cmd="prev")
        assert prev_song == "prev_song.mp3", "Previous song should be returned"

        # After calling prev, recent_song_path should update correctly
        assert sq.recent_song_path == "prev_song.mp3", "recent_song_path should update to prev_song_path"
        assert sq.prev_song_path == "old_song.mp3", "prev_song_path should update to old_song_path"
        assert sq.old_song_path == "", "old_song_path should be cleared"

        # Test put_first - add some songs then put one at front
        sq.clear_queue()
        sq.add_to_queue("songA.mp3")
        sq.add_to_queue("songB.mp3")
        sq.put_first("songFront.mp3")

        # Get songs one by one, first should be "songFront.mp3"
        first_song = sq.get_song("next")
        second_song = sq.get_song("next")
        third_song = sq.get_song("next")  # Should block but we won't wait infinitely here

        assert first_song == "songFront.mp3", "put_first did not put song at the front"
        assert second_song == "songA.mp3", "Second song should be 'songA.mp3'"
        assert third_song == "songB.mp3", "Third song should be 'songB.mp3'"

        # Test update_previous resets pointers and queue
        sq.recent_song_path = "recent.mp3"
        sq.prev_song_path = "prev.mp3"
        sq.old_song_path = "old.mp3"
        sq.update_previous()

        assert sq.prev_song_path == "old.mp3", "prev_song_path not updated correctly"
        assert sq.old_song_path == "", "old_song_path should be cleared"

        # Clear queue and check variables
        sq.clear_queue()
        assert sq.recent_song_path == "", "recent_song_path not cleared"
        assert sq.prev_song_path == "", "prev_song_path not cleared"
        assert sq.old_song_path == "", "old_song_path not cleared"
        assert sq.my_queue.empty(), "Queue should be empty after clear"

        print("All SongsQueue tests passed successfully.")