import socket


def protocol_send(my_socket, cmd, data):
    msg = cmd + str(len(data))
    for i in data:
        msg += str(len(i)) + "!" + str(i)
    my_socket.send(msg.encode())


def receive_protocol(my_socket):
    cmd = my_socket.recv(1).decode()
    if cmd != '':
        cmd += my_socket.recv(1).decode()

        length = ''
        b = my_socket.recv(1).decode()
        while b != '!':
            length += b
            b = my_socket.recv(1).decode()

        data = []
        length = int(length)
        for i in range(length):
            i_length = ''
            b = my_socket.recv(1).decode()
            while b != '!':
                i_length += b
                b = my_socket.recv(1).decode()

            data.append(my_socket.recv(i_length).decode())

        return cmd, data


