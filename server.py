import socket
import os
from protocol import receive_protocol

FOLDER = r"C:\musicCyber"
IP = '127.0.0.1'
PORT = 2222
QUEUE_LEN = 1


def send_song(client_socket, song_name):
    song_name += ".mp3"
    song_path = os.path.join(FOLDER, song_name)
    print("path: " + song_path)
    if os.path.exists(song_path) and os.path.isfile(song_path):
        with open(song_path, "rb") as file:
            song_bytes = file.read()
        client_socket.send(song_bytes)
        print("File sent successfully!")
    else:
        error_msg = "not found"
        client_socket.send(error_msg.encode())
        print("File not found: " + song_name)


def add_song(song_byte, song_name):
    file_name = song_name + ".mp3"
    file_path = os.path.join(FOLDER, file_name)
    with open(file_path, 'wb') as file:
        file.write(song_byte.encode())


def main():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.bind((IP, PORT))
        my_socket.listen(QUEUE_LEN)

        while True:
            client_socket, client_address = my_socket.accept()
            print(f"Client connected: {client_address}")
            try:
                while True:
                    msg = receive_protocol(client_socket)
                    cmd = msg[0]
                    data = msg[1]
                    if cmd == "get": # [name]
                        song_name = data[0]
                        send_song(client_socket, song_name)
                    elif cmd == "pst": # [name ,file]
                        name = data[0]
                        file = data[1]
                        add_song(file, name)

            except socket.error as err:
                print('Socket error on client connection: ' + str(err))

            finally:
                print("Client disconnected")
                client_socket.close()

    except socket.error as err:
        print('Socket error on server socket: ' + str(err))

    finally:
        my_socket.close()


if __name__ == "__main__":
    main()
