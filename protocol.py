import socket
import ssl
import logging
import os

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'protocol_log'
LOG_FILE = os.path.join(LOG_DIR, 'protocol.log')
#if not os.path.isdir(LOG_DIR):
 #   os.makedirs(LOG_DIR)
#logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)


def protocol_send(my_socket, cmd, data):
    """
    Sends a command and associated data to a socket using a custom protocol.
    :param my_socket: socket, the socket to send the data through
    :param cmd: str, a 3-character command indicating the request type
    :param data: list, a list of strings or bytes objects to send
    :return: None, raises exceptions on timeout or SSL error
    """
    try:
        msg = cmd + str(len(data))
        msg = msg.encode()
        for i in data:
            if isinstance(i, bytes):
                sign = 'b'
                encoded_data = i
                i_length = str(len(i))
                logging.debug("sending bytes")
                logging.debug(len(encoded_data))
            else:
                i = str(i)
                sign = 's'
                i_length = str(len(i))
                encoded_data = str(i).encode()

            temp = sign + i_length + "!"
            msg += temp.encode() + encoded_data
        my_socket.send(msg)

        #print(msg[20])
        print("sent_succe")
    except socket.timeout:
        print("Timeout occurred while waiting for response")
        raise

    except ssl.SSLError as e:
        print(f"SSL error: {e}")
        raise


def protocol_receive(my_socket):
    """
    Receives a command and associated data from a socket using a custom protocol.
    :param my_socket: socket, the socket to receive the data from
    :return: tuple, (cmd: str, data: list) on success, or ("error", [error_message]) on failure
    """
    try:
        cmd = ""
        while len(cmd) < 3:
            b = my_socket.recv(1).decode()
            if b:
                cmd += b

        num_of_items = my_socket.recv(1).decode()
        data = []
        num_of_items = int(num_of_items)
        for i in range(num_of_items):
            sign = my_socket.recv(1).decode()
            i_length = ""
            b = my_socket.recv(1).decode()
            while b != '!':
                i_length += b
                b = my_socket.recv(1).decode()
            if sign == 'b':
                item = b''
                while len(item) < int(i_length):
                    item += my_socket.recv(int(i_length) - len(item))
                data.append(item)
            elif sign == 's':
                item = ''
                for j in range(int(i_length)):
                    item += my_socket.recv(1).decode()
                data.append(item)

        return cmd, data

    except socket.timeout:
        print("socket timeout over in recv")
        return "error", ["timeout"]

    except ssl.SSLError as e:
        print(f"SSL error during receive: {e}")
        return "error", [f"ssl error: {e}"]

    except Exception as e:
        print("Error in protocol_receive:", e)
        return "error", [str(e)]


def recv_all(sock, length):
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise Exception("Connection closed while receiving data")
        data += chunk
    return data.decode()
