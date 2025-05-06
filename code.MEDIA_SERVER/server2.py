import socket
import os
from protocol import protocol_receive
from protocol import protocol_send
import threading
import jwt
import logging

SECRET_KEY = "my_secret_key"
FOLDER = r"C:\server2_musicCyber"
IP = '127.0.0.1'
PORT = 3333
QUEUE_LEN = 1

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log3'
LOG_FILE = LOG_DIR + '/server2.log'


def logging_protocol(func, cmd, data):
    """
    Logs a protocol-level action for debugging.

    :param func: The type of operation ("send" or "recv").
    :param cmd: The command used .
    :param data: Data sent or received in the protocol.
    """
    try:
        msg = func + " : " + cmd
        for i in data:
            if type(i) is not bytes:
                msg += ", " + str(i)
        logging.debug(msg)
    except Exception as e:  # תפיסת כל סוגי החריגות
        logging.debug(e)


def verify_token(token):
    """
    Verifies a JWT token.

    :param token: The token string to verify.
    :return: A dict with 'valid': True/False. if True return איק פשטךםשג and if false return the type of error
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        logging.debug("toke is valid")
        return {"valid": True, "data": payload}
    except jwt.ExpiredSignatureError:
        logging.debug("Token has expired")
        return {"valid": False, "error": "Token has expired"}
    except jwt.InvalidTokenError:
        logging.debug("Invalid token")
        return {"valid": False, "error": "Invalid token"}


def send_song(cmd, client_socket, song_name, token=""):
    """
    Sends an MP3 song file over a socket connection to a server or client.

    :param cmd: The command indicating the type of transfer.
                Options:
                - "bkp": send the song to a backup server (includes token).
                - "get": send the song to a client (no token needed).
    :param client_socket: The socket through which the song data is sent.
    :param song_name: The name of the song (without the .mp3 extension).
    :param token: Authentication token used when backing up to a server (optional, default is empty).

    :return: None. The function sends the data using `protocol_send`.
             In case of error, sends a response like ["error", "message"].
    """
    data = []
    try:
        song_name2 = song_name + ".mp3"
        song_path = os.path.join(FOLDER, f"{song_name}.mp3")
        print("Path:", song_path)
        with open(song_path, "rb") as file:
            song_bytes = file.read()

        if cmd == "bkp":
            # sending the song to server
            data = [token, song_name, song_bytes]
        elif cmd == "get":
            # sending the song to client
            data = [song_name2, song_bytes]

    except FileNotFoundError:
        logging.debug("File not found (unexpected error):", song_name)
        data = ["error", "file not found"]
    except OSError as e:
        logging.debug(f"OS error while sending {song_name}: {e}")
        data = ["error", f"{str(e)}"]
    except Exception as e:
        data = ["error", f": {str(e)}"]
        logging.debug(f"Unexpected error while sending {song_name}: {e}")
    finally:
        protocol_send(client_socket, cmd, data)
        logging_protocol("send", cmd, data)


def add_song(song_byte, song_name):
    """
   Saves a song (in bytes) to a local MP3 file in the predefined folder.

   :param song_byte: The binary content of the song (as bytes), expected to be a valid MP3 file.
   :param song_name: The name to save the file as (without the .mp3 extension).

   :return: True if the file was saved successfully, False otherwise.

   Notes:
   - The file is saved in the directory specified by the global variable `FOLDER`.
   - Handles all exceptions and logs the error using `logging.debug`.
   """
    temp = False
    try:
        file_name = song_name + ".mp3"
        file_path = os.path.join(FOLDER, file_name)
        with open(file_path, 'wb') as file:
            file.write(song_byte)
        temp = True
    except Exception as e:
        logging.debug(f"Error saving file: {e}")
    finally:
        return temp


def handle_client(client_socket, client_address):
    """
   Handles communication with a connected client or media server, processing various commands.

   :param client_socket: The socket object for the connected client.
   :param client_address: The (IP, port) tuple representing the client's address.

   :return: None

   Functionality:
   - Receives a command and data from the client.
   - Validates the authentication token.
   - Based on the command (`cmd`), performs the appropriate action:
       * "get" – Sends a requested song to the client.
       * "pst" – Receives and saves a song from a client.
       * "bkg" – Sends a song to another media server, upon request from the main server.
       * "vrf" – Responds to the main server whether a song file exists or not.
       * "bkp" – Saves a song received from another media server for backup purposes.

   Notes:
   - All incoming and outgoing messages are logged using `logging_protocol`.
   - Token validation is done before any action except for some server-side backups.
   - Handles connection errors and logs relevant exceptions.
   - Ensures the client socket is closed at the end of the session.
   """
    logging.debug(f"Client connected: {client_address}")
    try:
        cmd, data = protocol_receive(client_socket)
        logging_protocol("recv", cmd, data)
        token = data[0]
        valid = verify_token(token)
        if not valid.get("valid"):
            protocol_send(client_socket, cmd, ["False", "token is not valid"])
            logging_protocol("send", cmd, data)

        elif valid.get("valid"):
            if cmd == "get":
                # [token, name]
                # client send a get msg for a song
                song_name = str(data[1])
                send_song("get", client_socket, song_name)

            elif cmd == "pst":
                # [token, name ,file]
                # receiving a new song from client
                song_name = str(data[1])
                song_bytes = data[2]
                is_worked = add_song(song_bytes, song_name)
                if is_worked:
                    val = ["True", "post song succeeded"]
                else:
                    val = ["False", "post song failed"]
                protocol_send(client_socket, "pst", val)
                logging_protocol("send", cmd, data)

            elif cmd == "bkg":
                # [token, id, ip, port]
                # main server tells you to send a file to another media server
                try:
                    token = data[1]
                    song = str(data[2])
                    address = (data[3], int(data[4]))
                    server2_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server2_socket.connect(address)
                    logging.debug("connecting to server2")
                    cmd = "bkp"
                    send_song(cmd, server2_socket, song, token)
                except Exception as e:
                    logging.debug(f"Failed to connect to secondary server: {e}")

            elif cmd == "vrf":
                # [token, song_id]
                # main server asks if the file is exists
                song_name = str(data[1])
                song_path = os.path.join(FOLDER, f"{song_name}.mp3")
                if os.path.exists(song_path):
                    data = ["found"]
                else:
                    data = ["lost"]
                protocol_send(client_socket, cmd, data)
                logging_protocol("send", cmd, data)

            elif cmd == "bkp":
                # cmd from server to save a file and backup a song
                song_name = str(data[1])
                song_bytes = data[2]
                is_worked = add_song(song_bytes, song_name)
                if is_worked:
                    logging.debug("song uploaded")

    except socket.error as err:
        print('Socket error on client connection: ' + str(err))
    finally:
        client_socket.close()
        print("Client disconnected")


def main():
    """
    Starts the media server, listens for incoming client connections, and handles each in a separate thread.
    :return: None

    Functionality:
    - Creates a TCP socket and binds it to the configured IP and port.
    - Listens for incoming client connections (up to `QUEUE_LEN` in the backlog).
    - For each accepted client connection, spawns a new thread that handles the client via `handle_client`.

    Notes:
    - Exceptions during socket setup or accept are logged.
    - Ensures the main server socket is properly closed on shutdown or error.
    - Designed to run indefinitely, handling multiple clients concurrently.
    """
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.bind((IP, PORT))
        my_socket.listen(QUEUE_LEN)
        while True:
            client_socket, client_address = my_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()

    except socket.error as err:
        logging.debug(f'Socket error on server socket: {err}')

    finally:
        logging.debug("closing main socket")
        my_socket.close()


if __name__ == "__main__":
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    if not os.path.exists(FOLDER):
        os.makedirs(FOLDER)
    logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)
    main()
