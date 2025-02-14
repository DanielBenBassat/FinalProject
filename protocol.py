

def protocol_send(my_socket, cmd, data):
    msg = (cmd + "!" + str(len(data))).encode()

    for i in data:
        if isinstance(i, bytes):
            sign = 'b'
            encoded_data = i
        else:
            sign = 's'
            encoded_data = str(i).encode()
        temp=  sign + str(len(i)) + "!"
        print(temp)
        msg += temp.encode() + encoded_data
    my_socket.send(msg)


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
            sign = my_socket.recv(1).decode()
            print(sign)
            i_length = ""
            b = my_socket.recv(1).decode()
            while b != '!':
                i_length += b
                b = my_socket.recv(1).decode()

            if sign == 'b':

                for i in range(int(i_length)):
                    item= my_socket.recv(1)
            elif sign == 's':
                for i in range(int(i_length)):
                    item= my_socket.recv(1).decode()
            data.append(data)

        return cmd, data


