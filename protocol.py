

def protocol_send(my_socket, cmd, data):
    msg = cmd + "!" + str(len(data))
    for i in data:
        msg += str(len(i)) + "!" + str(i)
    print(msg)
    my_socket.send(msg.encode())


def receive_protocol(my_socket):
    b = my_socket.recv(1).decode()
    cmd = ''
    if b != '':
        while b != '!':
            cmd += b
            b = my_socket.recv(1).decode()

        print(cmd)
        num_of_items = my_socket.recv(1).decode()
        data = []
        num_of_items = int(num_of_items)
        for i in range(num_of_items):
            i_length = ''
            b = my_socket.recv(1).decode()
            while b != '!':
                i_length += b
                b = my_socket.recv(1).decode()

            data.append(my_socket.recv(int(i_length)).decode())

        return cmd, data


