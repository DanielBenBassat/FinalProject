import socket
import os
from protocol import protocol_receive
from protocol import protocol_send
import threading

FOLDER = r"C:\musicCyber"
IP = '127.0.0.1'
PORT = 2222
QUEUE_LEN = 1

#token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def send_song(client_socket, song_name):
    song_name += ".mp3"
    song_path = os.path.join(FOLDER, song_name)
    print("path: " + song_path)
    if os.path.exists(song_path) and os.path.isfile(song_path):
        with open(song_path, "rb") as file:
            song_bytes = file.read()
        data = [song_name, song_bytes]
        protocol_send(client_socket, "get", data)
        print("File sent successfully!")
    else:
        error_msg = "not found"
        protocol_send(client_socket, "get", [error_msg])
        print("File not found: " + song_name)


def add_song(song_byte, song_name):
    temp = False
    try:
        file_name = song_name + ".mp3"
        file_path = os.path.join(FOLDER, file_name)
        with open(file_path, 'wb') as file:
            file.write(song_byte)
        temp = True
    except Exception as e:  # תפיסת כל סוגי החריגות
        print(f"Error saving file {file_name}: {e}")
    finally:
        return temp


def handle_client(client_socket, client_address):
    print(f"Client connected: {client_address}")
    try:
        #while True:
        msg = protocol_receive(client_socket)
        if msg is not None:
            cmd = msg[0]
            data = msg[1]
            if cmd == "get": # [name]
                song_name = data[0]
                send_song(client_socket, song_name)
            elif cmd == "pst": # [name ,file]
                name = data[0]
                file = data[1]
                is_worked = add_song(file, name)
                if is_worked:
                    val = "good"
                else:
                    val = "error"
                protocol_send(client_socket, "pst", [val])

    except socket.error as err:
        print('Socket error on client connection: ' + str(err))

    finally:
        print("Client disconnected")
        client_socket.close()


def main():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.bind((IP, PORT))
        my_socket.listen(QUEUE_LEN)

        while True:
            client_socket, client_address = my_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()

    except socket.error as err:
        print(f'Socket error on server socket: {err}')

    finally:
        my_socket.close()



if __name__ == "__main__":
    main()
