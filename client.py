import socket
import logging
import pygame
from protocol import protocol_send

IP = '127.0.0.1'
PORT = 2222

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = LOG_DIR + '/client.log'


def stop_song():
    pygame.mixer.music.stop()
    print("Music stopped.")


def play_song(song_name):
    pygame.mixer.init()
    pygame.mixer.music.load(song_name)
    pygame.mixer.music.play()
    print(f"Playing {song_name}... Type 'stop' to stop the music.")

    while pygame.mixer.music.get_busy():
        cmd = input("Type 'stop' to stop the music: ")
        if cmd.lower() == "stop":
            stop_song()
            break


def get_song(client_socket, song):
    data = [song]
    protocol_send(client_socket, "get", data)
    data = client_socket.recv(500000)
    file_name = song + ".mp3"
    with open(file_name, 'wb') as file:
        file.write(data)
    print(f"File saved as {file_name}")
    play_song(file_name)


def post_song(client_socket):
    song_name = input("Enter song's name: ")
    file_path = input("Enter file path: ")
    with open(file_path, "rb") as file:
        song_bytes = file.read()
    data = [song_name, song_bytes]
    protocol_send(client_socket, "pst", data)


def main():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((IP, PORT))
        try:
            while True:
                cmd = input("Enter command: get, post, or exit: ")
                if cmd == "exit":
                    break
                elif cmd == "get":
                    song = input("Enter song's name: ")
                    get_song(client_socket, song)
                elif cmd == "post":
                    post_song(client_socket)
                else:
                    print("Try again")

        except socket.error as err:
            print(f"Received socket error: {err}")

        finally:
            print("Client left the server")
            client_socket.close()

    except socket.error as err:
        print(f"Received socket error: {err}")


if __name__ == "__main__":
    main()
