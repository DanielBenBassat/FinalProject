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


MAIN_SERVER_ADDR = ("127.0.0.1", 5555)

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = LOG_DIR + '/client.log'

q = SongsQueue()



def play_song(song_name):
    """

    :param song_name: name.mp3
    :return:
    """
    pygame.mixer.init()
    pygame.mixer.music.load(song_name)
    pygame.mixer.music.play()
    print(f"Playing {song_name}... Type 'stop' to stop the music.")

    while pygame.mixer.music.get_busy():
        cmd = input("Type 'stop' to stop the music: ")
        if cmd.lower() == "stop":
            pygame.mixer.music.stop()
            print("Music stopped.")
            break


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
        print("Connection with media server successful!")
        protocol_send(media_socket, "get", [song_id])
        cmd, data = protocol_receive(media_socket) # "get" , [file_name, file_bytes]
        media_socket.close()
        file_name = data[0]
        if file_name != "not found":
            with open(file_name, 'wb') as file:
                file.write(data[1])
            print(f"File saved as {file_name}")

    except socket.error as e:
        print(f"Connection failed: {e}")

    finally:
        return file_name


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

    try:
        media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        media_socket.connect(server_address)
        print("Connection successful!")
        with open(file_path, "rb") as file:
            song_bytes = file.read()
        data = [id, song_bytes]
        protocol_send(media_socket, "pst", data)
        media_socket.close()

    except socket.error as e:
        print(f"Connection failed: {e}")


def main():
    try:
        main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        main_socket.connect(MAIN_SERVER_ADDR)
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
                        song = input("Enter song's name: ")
                        if song in song_id_dict:
                            song_id = song_id_dict[song][1]
                            media_server_address = get_address(main_socket, song_id)
                            file_name = get_song(song_id, media_server_address)
                            if file_name != "error":
                                q.add_to_queue(file_name)
                                #play_song(file_name)

                    elif cmd == "add":
                        song_name = input("Enter song's name: ")
                        artist = input("Enter artist's name: ")
                        file_path = input("Enter file path: ")
                        if os.path.isfile(file_path):
                            song_id, media_server_address = get_address_new_song(main_socket, song_name, artist)
                            post_song(file_path, song_id, media_server_address)
                    else:
                        print("Try again")

            except socket.error as err:
                print(f"Received socket error: {err}")

            finally:
                print("Client left the server")
                main_socket.close()

    except socket.error as err:
        print(f"Received socket error: {err}")


def player():
    p = MusicPlayer()
    while True:
        song_path = q.next_song()  # ממתין להודעה מה-thread הראשי
        if os.path.exists(song_path):
            p.play_song(song_path)



if __name__ == "__main__":
    player_thread = threading.Thread(target=player, daemon=True)
    player_thread.start()
    main()
