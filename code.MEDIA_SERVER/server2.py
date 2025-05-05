import socket
import os
from protocol import protocol_receive
from protocol import protocol_send
import threading
import jwt
import datetime
import logging
SECRET_KEY= "my_secret_key"
FOLDER = r"C:\server2_musicCyber"
IP = '127.0.0.1'
PORT = 3333
QUEUE_LEN = 1

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log3'
LOG_FILE = LOG_DIR + '/server2.log'



def logging_protocol(func, cmd, data):
    try:
        msg = func + " : " + cmd
        for i in data:
            if type(i) is not bytes:
                msg += ", " + str(i)
        logging.debug(msg)
    except Exception as e:  # תפיסת כל סוגי החריגות
        logging.debug(e)

def verify_token(token):
    """Checks if a JWT token is valid and returns its payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "data": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}

def generate_infinity_token():
    """
    יוצר טוקן JWT ללא תפוגה, המכיל את זמן היצירה.

    :return: מחרוזת טוקן JWT חתום עם HS256.
    """
    payload = {
        "iat": datetime.datetime.utcnow(),  # זמן יצירה
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def send_song(cmd, client_socket, song_name, token = ""):
    """
    שולח קובץ שיר ללקוח דרך הסוקט.

    :param client_socket: סוקט המחובר ללקוח.
    :param song_name: שם השיר ללא סיומת.
    :param token
    :return: אין ערך מוחזר. שולח נתונים דרך הסוקט.
    """
    try:
        logging.debug("in sendsong")
        song_name2 = song_name + ".mp3"
        song_path = os.path.join(FOLDER, song_name2)
        print("Path:", song_path)

        with open(song_path, "rb") as file:
            song_bytes = file.read()

        data = [song_name, song_bytes]
        if cmd == "bkp": #"sending the song to server
            data = [token, song_name, song_bytes]
        elif cmd == "get":
            data = [song_name2, song_bytes]
        protocol_send(client_socket, cmd, data)
        logging_protocol("send", cmd, data)
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
        logging_protocol("recv", cmd, data)
        token = data[0]
        valid = verify_token(token)
        if not valid.get("valid"):
            print("token is not valid")
            protocol_send(client_socket, cmd, ["False", "token is not valid"])
            logging_protocol("send", cmd, data)
        elif valid.get("valid"):
            print("token is valid")
            if cmd == "get": # [token, name]
                song_name = str(data[1])
                send_song("get", client_socket, song_name)
            elif cmd == "pst": # [token, name ,file]
                name = str(data[1])
                file = data[2]
                is_worked = add_song(file, name)
                if is_worked:
                    val = ["True", "post song succeeded"]
                else:
                    val = ["False", "post song failed"]
                protocol_send(client_socket, "pst", val)
                logging_protocol("send", cmd, data)
            elif cmd == "bkg": #[token, id, ip, port]
                token = generate_infinity_token()
                song = str(data[1])
                ip = data[2]
                port = int(data[3])
                server2_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server2_socket.connect((ip, port))
                logging.debug("connecting to server2")
                cmd = "bkp"
                send_song(cmd, server2_socket, song, token)
            elif cmd == "vrf": #[song_id]
                song_name = data[1]
                song_name += ".mp3"
                song_path = os.path.join(FOLDER, song_name)
                if os.path.exists(song_path):
                    data = ["found"]
                else:
                    data = ["lost"]
                protocol_send(client_socket, cmd, data)
                logging_protocol("send", cmd, data)
            elif cmd == "bkp":
                print("reciving song")
                name = str(data[1])
                file = data[2]
                is_worked = add_song(file, name)
                if is_worked:
                    logging.debug("song uploaded")



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
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)
    main()
