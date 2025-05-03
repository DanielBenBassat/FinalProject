import socket
import os
from protocol import protocol_receive
from protocol import protocol_send
import threading
import jwt
import datetime
SECRET_KEY= "my_secret_key"
FOLDER = r"C:\server2_musicCyber"
IP = '127.0.0.1'
PORT = 3333
QUEUE_LEN = 1


def verify_token(token):
    """Checks if a JWT token is valid and returns its payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "data": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}


def send_song(client_socket, song_name):
    """
    שולח קובץ שיר ללקוח דרך הסוקט.

    :param client_socket: סוקט המחובר ללקוח.
    :param song_name: שם השיר ללא סיומת.
    :return: אין ערך מוחזר. שולח נתונים דרך הסוקט.
    """
    try:
        song_name += ".mp3"
        song_path = os.path.join(FOLDER, song_name)
        print("Path:", song_path)

        with open(song_path, "rb") as file:
            song_bytes = file.read()

        data = [song_name, song_bytes]
        protocol_send(client_socket, "get", data)
        print("File sent successfully:", song_name)

    except FileNotFoundError:
        print("File not found (unexpected error):", song_name)
        protocol_send(client_socket, "get", ["error", "file not found"])
    except OSError as e:
        print(f"OS error while sending {song_name}: {e}")
        protocol_send(client_socket, "get", ["error", f"{str(e)}"])
    except Exception as e:
        print(f"Unexpected error while sending {song_name}: {e}")
        protocol_send(client_socket, "get", ["error", f": {str(e)}"])


def add_song(song_byte, song_name):
    temp = False
    try:
        file_name = song_name + ".mp3"
        file_path = os.path.join(FOLDER, file_name)
        print("adding song")
        print(len(song_byte))
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
        cmd, data = protocol_receive(client_socket)
        token = data[0]
        valid = verify_token(token)
        if not valid.get("valid"):
            print("token is not valid")
            protocol_send(client_socket, cmd, ["False", "token is not valid"])

        elif valid.get("valid"):
            print("token is valid")
            if cmd == "get": # [name]
                song_name = str(data[1])
                send_song(client_socket, song_name)
            elif cmd == "pst": # [name ,file]
                name = str(data[1])
                file = data[2]
                is_worked = add_song(file, name)
                if is_worked:
                    val = ["True", "post song succeeded"]
                else:
                    val = ["False", "post song failed"]
                protocol_send(client_socket, "pst", val)

    except socket.error as err:
        print('Socket error on client connection: ' + str(err))
    finally:
        print("Client disconnected")


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
