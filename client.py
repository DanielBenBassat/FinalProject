import socket
import logging
import pygame
from protocol import protocol_send
from protocol import protocol_receive
import threading
import pickle
import os
import time
from songs_queue import SongsQueue
from player import MusicPlayer




# === Logging Configuration ===
LOG_DIR = 'log'

LOG_FILE_CLIENT = os.path.join(LOG_DIR, 'client.log')
LOG_FILE_PLAYER = os.path.join(LOG_DIR, 'player.log')
LOG_FORMAT = '%(levelname)s | %(asctime)s | %(name)s | %(message)s'


def setup_logger(name, log_file):
    """Set up a logger that logs to a specific file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger







MAIN_SERVER_ADDR = ("127.0.0.1", 5555)

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE_CLIENT = LOG_DIR + '/client.log'
LOG_FILE_PLAYER = LOG_DIR + '/player.log'


q = SongsQueue()


def get_address(client_socket, song_id):
    """
    sends the main server a song id and receive an address of the media server that has the song
    :param client_socket: socket
    :param song_id: int
    :return: address of the media server that has the required song
    """
    cmd = "gad"
    data = [song_id]
    protocol_send(client_socket, cmd, data)
    cmd, data = protocol_receive(client_socket)
    ip = data[0]
    port = int(data[1])
    address = (ip, port)
    return address


def get_song(song_id, server_address):
    """

    :param song_id: int
    :param server_address: tuple of ip(str) and port(int)
    :return:
    """
    file_name = "error"
    try:
        media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        media_socket.connect(server_address)
        client_log.debug("Connection with media server successful!")
        protocol_send(media_socket, "get", [song_id])
        cmd, data = protocol_receive(media_socket) # "get" , [file_name, file_bytes]
        media_socket.close()
        file_name = data[0]
        if file_name != "not found":
            with open(file_name, 'wb') as file:
                file.write(data[1])
            client_log.debug(f"File saved as {file_name}")

    except socket.error as e:
        client_log.debug(f"Connection failed: {e}")

    finally:
        return file_name


def listen_song(main_socket, song_id_dict):
    song = input("Enter song's name: ")
    if song in song_id_dict:
        song_id = song_id_dict[song][1]
        media_server_address = get_address(main_socket, song_id)
        file_name = get_song(song_id, media_server_address)
        if file_name != "error":
            q.add_to_queue(file_name)

def get_address_new_song(client_socket, song_name, artist):
    """
    gets an id and a server address for adding new song
    :param client_socket: socket
    :param song_name: str
    :param artist: str
    :return:
    """
    protocol_send(client_socket, "pad", [song_name, artist])
    cmd, data = protocol_receive(client_socket) # "pad", [id, ip, port]
    song_id = int(data[0])
    ip = data[1]
    port = int(data[2])
    address = (ip, port)
    return song_id, address


def post_song(file_path, id, server_address):
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
        client_log.debug("Connection with media server successful!")
        with open(file_path, "rb") as file:
            song_bytes = file.read()
        data = [id, song_bytes]
        protocol_send(media_socket, "pst", data)
        cmd, data = protocol_receive(media_socket)
        val = data[0]
        media_socket.close()

    except socket.error as e:
        client_log.debug(f"Connection failed: {e}")
    finally:
        return val


def start_client(main_socket):
    cmd = 0
    while cmd != "1" and cmd != "2":
        cmd = input("enter 1 to sign up or 2 to log in: ")

    if cmd == "1":
        username = input("choose your username: ")
        password = input("enter password")
        password2 = input("verify password")
        if password == password2 and password is not None:
            protocol_send(main_socket, "sig", [username, password])
            cmd, data = protocol_receive(main_socket)
            if data[0] == "good":
                return True
    elif cmd == "2":
        username = input("choose your username: ")
        password = input("enter password")
        protocol_send(main_socket, "log", [username, password])
        cmd, data = protocol_receive(main_socket)
        print(data)
        if data[0] == "True":
            return True
        elif data[1] == "username" or data[1] == "password":
            return False

def main():
    try:
        main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        main_socket.connect(MAIN_SERVER_ADDR)
        temp = False
        while not temp:
            temp = start_client(main_socket)
            print(temp)

        cmd, data = protocol_receive(main_socket)
        if cmd == "str":
            song_id_dict = pickle.loads(data[0])
            print(song_id_dict)
            try:
                while True:
                    cmd = input("Enter command: listen, add, or exit: ")
                    if cmd == "exit":
                        break
                    elif cmd == "listen":
                        media_type = input("song or playlist: ")
                        if media_type == "song":
                            listen_song(main_socket, song_id_dict)

                    elif cmd == "add":
                        song_name = input("Enter song's name: ")
                        artist = input("Enter artist's name: ")
                        file_path = input("Enter file path: ")
                        if os.path.isfile(file_path):
                            song_id, media_server_address = get_address_new_song(main_socket, song_name, artist)
                            val = post_song(file_path, song_id, media_server_address)
                            if val == "good":
                                client_log.debug("post song succeeded")
                            elif val == "error":
                                client_log.debug("post song failed")

                    else:
                        print("Try again")

            except socket.error as err:
                client_log.debug(f"Received socket error: {err}")

            finally:
                client_log.debug("Client finish")
                main_socket.close()

    except socket.error as err:
        client_log.debug(f"Received socket error: {err}")


def player():
    p = MusicPlayer()
    while True:
        song_path = q.get_song()  # ממתין להודעה מה-thread הראשי
        if os.path.exists(song_path):
            player_log.debug("play song: " + song_path)
            p.play_song(song_path)


if __name__ == "__main__":
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    # Initialize loggers (runs at import)
    client_log = setup_logger("ClientLogger", LOG_FILE_CLIENT)
    player_log = setup_logger("PlayerLogger", LOG_FILE_PLAYER)

    player_thread = threading.Thread(target=player, daemon=True)
    player_thread.start()
    main()
