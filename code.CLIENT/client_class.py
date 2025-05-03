import queue
import socket
import logging
from protocol import protocol_send
from protocol import protocol_receive
import threading
import pickle
import os
import time

from songs_queue import SongsQueue
from player import MusicPlayer

LOG_DIR = 'log'
LOG_FILE_CLIENT = os.path.join(LOG_DIR, 'client.log')
LOG_FILE_PLAYER = os.path.join(LOG_DIR, 'player.log')
LOG_FORMAT = '%(levelname)s | %(asctime)s | %(name)s | %(message)s'


class Client:
    def __init__(self):

        self.MAIN_SERVER_ADDR = ("127.0.0.1", 5555)
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.connect(self.MAIN_SERVER_ADDR)

        self.q = SongsQueue()
        self.p = MusicPlayer()
        self.client_to_gui_queue = queue.Queue()
        self.gui_to_client_queue = queue.Queue()

        player_thread = threading.Thread(target=self.player_func, daemon=True)
        player_thread.start()

        self.username = ""
        self.token = ""
        self.song_id_dict = {}
        self.liked_song = []

        if not os.path.isdir(LOG_DIR):
            os.makedirs(LOG_DIR)
        # Initialize loggers (runs at import)
        self.client_log = self.setup_logger("ClientLogger", LOG_FILE_CLIENT)
        self.player_log = self.setup_logger("PlayerLogger", LOG_FILE_PLAYER)




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
            self.client_log.debug(msg)
        except Exception as e:  # תפיסת כל סוגי החריגות
            self.client_log.debug(e)

    def song_and_playlist(self, cmd, playlist_name, song_id):
        try:
            if cmd == "add":
                cmd = "atp"
                data = [self.token, self.username, playlist_name, song_id]
                protocol_send(self.main_socket, cmd, data)
                self.logging_protocol("send", cmd, data)

                cmd, data = protocol_receive(self.main_socket)
                self.logging_protocol("received", cmd, data)
                if data[0] == "Token has expired":
                    return 'Token has expired'
                if data[0] == 'True':
                    self.liked_song.append(song_id)
            elif cmd == "remove":
                cmd = "rfp"
                data = [self.token, self.username, playlist_name, song_id]
                protocol_send(self.main_socket, cmd, data)
                self.logging_protocol("send", cmd, data)

                cmd, data = protocol_receive(self.main_socket)
                self.logging_protocol("received", cmd, data)
                if data[0] == "Token has expired":
                    return 'Token has expired'
                if data[0] == 'True':
                    self.liked_song.remove(song_id)
        except Exception as e:
            print(e)





    def get_address(self, song_id):
        """
        sends the main server a song id and receive an address of the media server that has the song
        :param song_id: int
        :return: address of the media server that has the required song
        """
        cmd = "gad"
        data = [self.token, song_id]
        protocol_send(self.main_socket, cmd, data)
        self.logging_protocol("send", cmd, data)

        cmd, data = protocol_receive(self.main_socket)
        self.logging_protocol("received", cmd, data)
        if data[0] == "Token has expired":
            return 'Token has expired'

        ip = data[0]
        port = int(data[1])
        address = (ip, port)
        return address


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
            self.client_log.debug("Connection with media server successful!")

            cmd = "get"
            data = [self.token, song_id]
            protocol_send(media_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            cmd, data = protocol_receive(media_socket)
            self.logging_protocol("received", cmd, data)
            media_socket.close()
            if data[0] == "Invalid token":
                file_name = "Invalid token"
            else:

                file_name = data[0]
                if file_name != "not found":
                    with open(file_name, 'wb') as file:
                        file.write(data[1])
                    self.client_log.debug(f"File saved as {file_name}")

        except socket.error as e:
            self.client_log.debug(f"Connection failed: {e}")

        finally:
            return file_name


    def listen_song(self, song_id):

        file_path = os.path.join(str(song_id) + '.mp3')

        if os.path.exists(file_path):
            self.q.add_to_queue(file_path)
            self.client_log.debug(file_path + " was added to queue")
            return 'good'

        media_server_address = self.get_address(song_id)
        if media_server_address == 'Token has expired':
            return 'Token has expired'
        else:
            file_name =  self.get_song(song_id, media_server_address)
            if file_name == "error":
                return "error"
            elif file_name == "Invalid token":
                return "Invalid token"
            self.q.add_to_queue(file_name)
            self.client_log.debug(file_name + " was added to queue")
            return 'good'
    def play_playlist(self, playlist):
        self.q.clear_queue()
        self.p.stop_song()
        for song in playlist:
            self.listen_song(song)
    def add_song(self, song_name, artist, file_path):
        if os.path.isfile(file_path):
            data = self.get_address_new_song(song_name, artist)
            if data[0] == "False":
                return data
            else:
                song_id = data[0]
                media_server_address = data[1]
                val = self.post_song(file_path, song_id, media_server_address)
                return val

        else:
            return ["False", "file does not exist"]
    def get_address_new_song(self, song_name, artist):
        """
        gets an id and a server address for adding new song
        :param song_name: str
        :param artist: str
        :return:
        """
        cmd = "pad"
        data = [self.token, song_name, artist]
        protocol_send(self.main_socket, cmd, data)
        self.logging_protocol("send", cmd, data)

        cmd, data = protocol_receive(self.main_socket) # "pad", [id, ip, port]
        self.logging_protocol("received", cmd, data)
        if data[0] == "Invalid token" or data[0] == "Token has expired" or data[0] == "error":
            return data
        else:
            song_id = int(data[1])
            ip = data[2]
            port = int(data[3])
            address = (ip, port)
            return [song_id, address]


    def post_song(self, file_path, id, server_address):
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
            self.client_log.debug("Connection with media server successful!")
            with open(file_path, "rb") as file:
                song_bytes = file.read()
                print(len(song_bytes))

            cmd = "pst"
            data = [self.token, id, song_bytes]
            protocol_send(media_socket, cmd, data)
            self.logging_protocol("send", cmd, data)

            cmd, data = protocol_receive(media_socket)
            self.logging_protocol("received", cmd, data)
            if data[0] == "Invalid token":
                val = data
            else:
                val = data
                media_socket.close()

        except socket.error as e:
            self.client_log.debug(f"Connection failed: {e}")
            val = ["False", "error connection"]
        finally:
            return val

    def start_client(self, cmd, username, password): # cmd =1 sign up cmd =2 login
        if cmd == "1":
            cmd = "sig"
            data = [username, password]
            protocol_send(self.main_socket, cmd, data)
            self.logging_protocol("send", cmd, data)
            cmd, data = protocol_receive(self.main_socket)
            self.logging_protocol("received", cmd, data)
            if data[0] == "True":
                self.username = username
                self.token = data[1]
                self.song_id_dict = pickle.loads(data[2])

        elif cmd == "2":
            cmd = "log"
            data = [username, password]
            protocol_send(self.main_socket, cmd, data)
            self.logging_protocol("send", cmd, data)
            cmd, data = protocol_receive(self.main_socket)
            self.logging_protocol("received", cmd, data)
            if data[0] == "True":
                self.username = username
                self.token = data[1]
                self.song_id_dict = pickle.loads(data[2])
                print(self.song_id_dict)
                self.liked_song = pickle.loads(data[3])

                print("liked song")
                print(self.liked_song)
        return data




    def player_func(self):
        while True:
            cmd = self.gui_to_client_queue.get()
            self.queue_logging()
            self.player_log.debug(cmd)
            play = False
            if cmd == "play":
                play = True

            if cmd == "pause":
                self.p.pause_song()
                self.player_log.debug("pause song: ")
            elif cmd == "resume":
                self.p.resume_song()
                self.player_log.debug("resume song: ")
            elif cmd == "next":
                if not self.q.my_queue.empty():
                    self.p.stop_song()
                    play = True

            elif cmd == "prev":
                if self.q.prev_song_path != "":
                    self.p.stop_song()
                    play = True

            elif cmd == "shutdown":
                self.p.shutdown()

            if play:
                print(cmd)
                self.play_loop(cmd)


            self.player_log.debug("*********************************************************************")

    def play_loop(self, cmd):
        while self.gui_to_client_queue.empty():
            if not self.q.my_queue.empty() or (cmd == "prev" and self.q.prev_song_path != ""):
                song_path = self.q.get_song(cmd)
                self.queue_logging()
                if os.path.exists(song_path):
                    self.p.play_song(song_path, self.gui_to_client_queue) # שהתור ריק השיר מתנגן ושיש בו משהו הפעולה מופסקת
                else:
                    self.player_log.debug("song not found")
                cmd == "play" # after the first time, doing the loop regulary
            else:
                self.player_log.debug("nothing to play")
                self.client_to_gui_queue.put("nothing to play")
                break



    def queue_logging(self):
        msg_queue = list(self.q.my_queue.queue)
        for i in msg_queue:
            i = str(i)
        msg_queue = ', '.join(msg_queue)

        msg = f"paused: {self.p.is_paused}::::: recent: {self.q.recent_song_path}, previous: {self.q.prev_song_path}, old: {self.q.old_song_path}, queue: {msg_queue}"
        self.player_log.debug(msg)