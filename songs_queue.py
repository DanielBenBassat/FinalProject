import queue


class SongsQueue:
    def __init__(self):
        self.my_queue = queue.Queue() # queue of file's paths

    def add_to_queue(self, file_path): # main thread
        """
        מוסיף שיר לתור
        """
        self.my_queue.put(file_path)

    def get_song(self):
        """
        מנגן את השיר הבא מהתור
        """
        while True:
            try:
                song_path = self.my_queue.get(timeout=1)
                return song_path
            except queue.Empty:
                continue

    def queue_to_list(self):

        l = list(self.my_queue.queue)
        return " -> ".join(l)





    #def add_to_queue_front(self):
