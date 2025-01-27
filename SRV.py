import socket
import os

FOLDER = r"C:\musicCyber"  # נתיב לתיקיית השירים
IP = '127.0.0.1'
PORT = 1111
QUEUE_LEN = 1


db = {}


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
