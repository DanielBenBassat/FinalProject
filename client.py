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



def setup_logger(name, log_file):
    """Set up a logger that logs to a specific file"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


MAIN_SERVER_ADDR = ("127.0.0.1", 5555)
q = SongsQueue()


def logging_protocol(func, cmd, data):
    try:
        msg = func + " : " + cmd
        for i in data:
            if type(i) is not bytes:
                msg += ", " + str(i)
        client_log.debug(msg)
    except Exception as e:  # תפיסת כל סוגי החריגות
        client_log.debug(e)


def get_address(client_socket, song_id, token):
    """
    sends the main server a song id and receive an address of the media server that has the song
    :param client_socket: socket
    :param song_id: int
    :return: address of the media server that has the required song
    """
    cmd = "gad"
    data = [token, song_id]
    protocol_send(client_socket, cmd, data)
    logging_protocol("send", cmd, data)

    cmd, data = protocol_receive(client_socket)
    logging_protocol("received", cmd, data)
    if data[0] == "Token has expired":
        return 'Token has expired'

    ip = data[0]
    port = int(data[1])
    address = (ip, port)
    return address


def get_song(song_id, server_address, token):
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

        cmd = "get"
        data = [token, song_id]
        protocol_send(media_socket, cmd, data)
        logging_protocol("send", cmd, data)

        cmd, data = protocol_receive(media_socket)
        logging_protocol("received", cmd, data)
        media_socket.close()
        if data[0] == "Invalid token":
            file_name = "Invalid token"
        else:

            file_name = data[0]
            if file_name != "not found":
                with open(file_name, 'wb') as file:
                    file.write(data[1])
                client_log.debug(f"File saved as {file_name}")

    except socket.error as e:
        client_log.debug(f"Connection failed: {e}")

    finally:
        return file_name


def listen_song(main_socket, song_id_dict, token):
    song = input("Enter song's name: ")
    if song in song_id_dict:
        song_id = song_id_dict[song][1]
        media_server_address = get_address(main_socket, song_id, token)
        if media_server_address == 'Token has expired':
            return 'Token has expired'
        else:
            file_name = get_song(song_id, media_server_address, token)
            if file_name == "error":
                return "error"
            elif file_name == "Invalid token":
                return "Invalid token"
            q.add_to_queue(file_name)
            client_log.debug(file_name + " was added to queue")
            return 'good'

def add_song(main_socket, token):
    song_name = input("Enter song's name: ")
    artist = input("Enter artist's name: ")
    #file_path = input("Enter file path: ")
    song = input("Enter file path: ")
    file_path = fr"C:\newSongs\{song}.mp3"
    if os.path.isfile(file_path):
        data = get_address_new_song(main_socket, song_name, artist, token)
        if data[0] == "Invalid token" or data[0] == "Token has expired" or data[0] == "error":
            return data[0]
        else:
            song_id = data[0]
            media_server_address = data[1]
            val = post_song(file_path, song_id, media_server_address, token)
            if val == "good":
                return "post song succeeded"
            elif val == "Invalid token":
                return "Invalid token"
            else:
                "post song has failed"


def get_address_new_song(client_socket, song_name, artist, token):
    """
    gets an id and a server address for adding new song
    :param client_socket: socket
    :param song_name: str
    :param artist: str
    :return:
    """
    cmd = "pad"
    data = [token, song_name, artist]
    protocol_send(client_socket, cmd, data)
    logging_protocol("send", cmd, data)

    cmd, data = protocol_receive(client_socket) # "pad", [id, ip, port]
    logging_protocol("received", cmd, data)
    if data[0] == "Invalid token" or data[0] == "Token has expired" or data[0] == "error":
        return data
    else:
        song_id = int(data[0])
        ip = data[1]
        port = int(data[2])
        address = (ip, port)
        return [song_id, address]


def post_song(file_path, id, server_address, token):
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

        cmd = "pst"
        data = [token, id, song_bytes]
        protocol_send(media_socket, cmd, data)
        logging_protocol("send", cmd, data)

        cmd, data = protocol_receive(media_socket)
        logging_protocol("received", cmd, data)
        if data[0] == "Invalid token":
            val = "Invalid token"
        else:
            val = data[0]
            media_socket.close()
            val == "good"

    except socket.error as e:
        client_log.debug(f"Connection failed: {e}")
    finally:
        return val


def start_client(main_socket):
    temp = False
    while not temp:
        cmd = 0
        while cmd != "1" and cmd != "2":
            cmd = input("enter 1 to sign up or 2 to log in: ")

        if cmd == "1":
            username = input("choose your username: ")
            password = input("enter password")
            password2 = input("verify password")
            if password == password2 and password is not None:
                cmd = "sig"
                data = [username, password]
                protocol_send(main_socket, cmd, data)
                logging_protocol("send", cmd, data)

                cmd, data = protocol_receive(main_socket)
                logging_protocol("received", cmd, data)

        elif cmd == "2":
            username = input("choose your username: ")
            password = input("enter password")
            cmd = "log"
            data = [username, password]
            protocol_send(main_socket, cmd, data)
            logging_protocol("send", cmd, data)

            cmd, data = protocol_receive(main_socket)
            logging_protocol("received", cmd, data)
        if data[0] == "True":
            temp = True
        else:
            temp = False

    return data

def main():
    try:
        temp = True
        while temp:
            main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            main_socket.connect(MAIN_SERVER_ADDR)

            data = start_client(main_socket)
            token = data[1]
            song_id_dict = pickle.loads(data[2])
            print(song_id_dict)

            try:
                while True:
                    cmd = input("Enter command: listen, add, or exit: ")
                    if cmd == "exit":
                        temp = False
                        break
                    elif cmd == "listen":
                        msg = listen_song(main_socket, song_id_dict, token)
                        if msg == 'Token has expired':
                            break
                    elif cmd == "add":
                        msg = add_song(main_socket, token)
                        client_log.debug(msg)
                        if msg == 'Token has expired' or msg == "Invalid token":
                            break




                    else:
                        print("Try again")

            except socket.error as err:
                client_log.debug(f"Received socket error: {err}")

            finally:
                if temp:
                    client_log.debug("Token has expired, log in again")
                else:
                    client_log.debug("Client finish")
                main_socket.close()

    except socket.error as err:
        client_log.debug(f"Received socket error: {err}")
    finally:
        client_log.debug("Client finish")


def player():
    p = MusicPlayer()
    while True:
        song_path = q.get_song()
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
