

def protocol_send(my_socket, cmd, data):
    msg = cmd + "!" + str(len(data))
    print("send: " + msg)
    msg = msg.encode()
    for i in data:
        if isinstance(i, bytes):
            sign = 'b'
            encoded_data = i
        else:
            sign = 's'
            print(i)
            encoded_data = str(i).encode()
        temp = sign + str(len(str(i))) + "!"
        msg += temp.encode() + encoded_data

    my_socket.send(msg)


def protocol_receive(my_socket):
    b = my_socket.recv(1).decode()
    if b != '':
        cmd = ''
        while b != '!':
            cmd += b
            b = my_socket.recv(1).decode()
        print("cmd: receive " + cmd)

        num_of_items = my_socket.recv(1).decode()
        print("num of items: " + num_of_items)
        data = []
        num_of_items = int(num_of_items)
        for i in range(num_of_items):
            sign = my_socket.recv(1).decode()
            print("sign: " + sign)
            i_length = ""
            b = my_socket.recv(1).decode()
            while b != '!':
                i_length += b
                b = my_socket.recv(1).decode()
            if sign == 'b':
                item = my_socket.recv(int(i_length))
            elif sign == 's':
                item = ''
                for j in range(int(i_length)):
                    item += my_socket.recv(1).decode()
                print("item: " + item)
            data.append(item)
        result = (cmd, data)
        return result


