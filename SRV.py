import socket
import threading
import protocol
import logging
import os




IP = "127.0.0.1"
PORT = 5555
CLIENTS_SOCKETS = []
THREADS = []
MD5_TARGET = "25f9e794323b453885f5181f1b624d0b"
NUM_PER_CORE = 10000
lock = threading.Lock()
task_start = 0
found = False


def handle_client(client_socket, address):
    try:


    except socket.error:
        logging.debug(f"[ERROR] Connection with {address} lost.")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((IP, PORT))
        server.listen()

        while True:
            try:
                client_socket, client_address = server.accept()
                CLIENTS_SOCKETS.append(client_socket)
                thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
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
