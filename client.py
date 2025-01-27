"""
Author: Daniel Ben Bassat
Date: 10/12/2023
Description: client side
"""
import socket
import logging
import os
import subprocess



IP = '127.0.0.1'
PORT = 1111

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = LOG_DIR + '/client.log'


def get_song(client_socket):
    song = input("enter song's name: ")
    client_socket.send(song.encode())
    data = client_socket.recv(500000)
    file_name = song + ".mp3"
    with open(file_name, 'wb') as file:
        file.write(data)
    print(f"file saved as {song}")

def post_song(client_socket):


def main():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((IP, PORT))
        while True:
            try:
                cmd = input("enter cmd: get or post or exit ")
                if cmd == "exit":
                    break
                elif cmd == "get":
                    get_song(client_socket)
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