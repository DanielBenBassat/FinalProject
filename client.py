import socket
import logging
import pygame
import protocol
from protocol import protocol_send
from protocol import protocol_receive
import threading

MAIN_SERVER_ADDR = ("127.0.0.1", 5555)

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = LOG_DIR + '/client.log'

SONGS_ID_DICT = {"bad": 1, "help": 2}

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


def get_address(client_socket, song_id):
    protocol_send(client_socket, "gad", [song_id])
    cmd, data = protocol_receive(client_socket)
    server_address = data[0]
    return server_address

def get_song(song_id, server_address):
    try:
        media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        media_socket.connect(server_address)
        print("✅ Connection successful!")
    except socket.error as e:
        print(f"❌ Connection failed: {e}")

    data = [song_id]
    protocol_send(media_socket, "get", data)
    cmd, data = protocol_receive(media_socket)
    media_socket.close()
    file_name = data[0]
    with open(file_name, 'wb') as file:
        file.write(data[1])
    print(f"File saved as {file_name}")
    play_song(file_name)

def get_address_new_song(client_socket, song_name, artist):
    protocol_send(client_socket, "pad", [song_name, artist])
    cmd,data= protocol_receive(client_socket)
    id = int(data[0])
    ip = data[1]
    port = int(data[2])
    address = (ip, port)
    return id, address


def post_song(file_path, id, address):
    media_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    media_socket.connect(address)

    with open(file_path, "rb") as file:
        song_bytes = file.read()
    data = [id, song_bytes]
    protocol_send(media_socket, "pst", data)


def main():
    try:
        main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        main_socket.connect(MAIN_SERVER_ADDR)
        try:
            while True:
                cmd = input("Enter command: get, post, or exit: ")
                if cmd == "exit":
                    break
                elif cmd == "get":
                    song = input("Enter song's name: ")
                    song_id= SONGS_ID_DICT[song]
                    media_server_address = get_address(main_socket, song_id)
                    get_song(song_id, media_server_address)
                elif cmd == "post":
                    #song_name = input("Enter song's name: ")
                    #artist = input("Enter artist's name: ")
                    #file_path = input("Enter file path: ")
                    song_name = "shape"
                    artist = "ed"
                    file_path = r"C:\newSongs\shape.mp3"

                    song_id, media_server_address = get_address_new_song(main_socket, song_name, artist)
                    #second_thread = threading.Thread(target=post_song(), args=())  # יצירת הטרד השני
                    #second_thread.start()  # הפעלת הטרד השני
                    #second_thread.join()
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

def start_client():
    print("🔌 Starting the client...")
    client_thread = threading.Thread(target=main(), args=())
    client_thread.start()  # הפעלת הטרד הראשון (החיבור לשרת הראשון)

    # ניתן להוסיף פעולות נוספות בלקוח בזמן שהטרד הראשון פועל
    # לדוג' הפסקה לחיבור שני, פעולות UI או עוד טרדים

    client_thread.join()

if __name__ == "__main__":
    main()
