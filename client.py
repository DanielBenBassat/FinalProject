import socket
import logging
import pygame

IP = '127.0.0.1'
PORT = 2222

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = LOG_DIR + '/client.log'


def play_song(song_name):
    pygame.mixer.init()
    pygame.mixer.music.load(song_name)
    pygame.mixer.music.play()
    print(f"Playing {song_name}.mp3... Type 'stop' to stop the music.")
    cmd = input("stop?")
    if cmd == "stop":
        stop_song()


def stop_song():
    pygame.mixer.music.stop()
    print("Music stopped.")


def get_song(client_socket, song):
    client_socket.send(song.encode())
    data = client_socket.recv(500000)
    file_name = song + ".mp3"
    with open(file_name, 'wb') as file:
        file.write(data)
    print(f"file saved as {file_name}")
    play_song(file_name)


def post_song(client_socket):
    print("hey")


def main():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((IP, PORT))

        try:
            while True:
                cmd = input("enter cmd: get or post or exit ")
                if cmd == "exit":
                    break
                elif cmd == "get":
                    song = input("enter song's name: ")
                    get_song(client_socket, song)
                elif cmd == "post":
                    post_song(client_socket)
                else:
                    print("try again")

        except socket.error as err:
            print('received socket error ' + str(err))

        finally:
            print("client left the server")
            client_socket.close()

    except socket.error as err:
        print('received socket error ' + str(err))


if __name__ == "__main__":
    main()