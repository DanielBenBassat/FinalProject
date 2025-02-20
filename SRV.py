import socket
import threading
import protocol
import logging
import os
from music_db import MusicDB




IP = "127.0.0.1"
PORT = 5555
CLIENTS_SOCKETS = []
THREADS = []
MD5_TARGET = "25f9e794323b453885f5181f1b624d0b"
NUM_PER_CORE = 10000
lock = threading.Lock()
task_start = 0
found = False
ADDRESS_LIST = [("127.0.0.1", 2222)]


def handle_client(client_socket):
    try:
        db = MusicDB("my_db.db")
        cmd, data = protocol.protocol_receive(client_socket)
        if cmd == "gad": # [id]
            id = data[0]
            server_address = db.get_address(id)
            protocol.protocol_send(client_socket, "gad", [server_address])

        elif cmd == "pad": # [name ,artist]
            name = data[0]
            artist = data[1]
            id, address = db.add_song(name, artist, ADDRESS_LIST)
            id = id[0][0]
            print(id, address)
            protocol.protocol_send(client_socket, "pad", [id, address[0], address[1]])


    except socket.error:
        logging.debug(f"[ERROR] Connection  lost.")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((IP, PORT))
        server.listen()

        while True:
            try:

                client_socket, client_address = server.accept()
                CLIENTS_SOCKETS.append(client_socket)
                thread = threading.Thread(target=handle_client, args=([client_socket]))
                THREADS.append(thread)
                thread.start()
                logging.debug(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            except socket.error:
                logging.debug("socket error")

    except socket.error:
        logging.debug("socket error")
    finally:
        server.close()
        logging.debug("server is closed")


if __name__ == "__main__":
    main()
