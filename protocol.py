import socket
import ssl

def protocol_send(my_socket, cmd, data):
    try:
        #msg = cmd + "!" + str(len(data))
        msg = cmd + str(len(data))
        #print("send: " + msg)
        msg = msg.encode()
        for i in data:
            if isinstance(i, bytes):
                sign = 'b'
                encoded_data = i
                i_length = str(len(i))
                print("sending bytes")
                print(len(encoded_data))
            else:
                #print(i)
                #print(type(i))
                i = str(i)
                sign = 's'
                i_length = str(len(i))
                encoded_data = str(i).encode()

            temp = sign + i_length + "!"
            msg += temp.encode() + encoded_data
        my_socket.send(msg)

    except socket.timeout:
        print("Timeout occurred while waiting for response")
        raise  # תזרוק את השגיאה למעלה, שה-caller יתמודד

    except ssl.SSLError as e:
        print(f"SSL error: {e}")
        raise  # תאפשר ל-caller להחזיר 'F' או להציג למשתמש



def protocol_receive(my_socket):
    try:
        cmd = ""
        while len(cmd) < 3:
            b = my_socket.recv(1).decode()
            if b is not None:
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
        print("socket timeout over")
        return "error", ["timeout"]

    except ssl.SSLError as e:
        print(f"SSL error during receive: {e}")
        return "error", [f"ssl error: {e}"]

    except Exception as e:
        print("Error in protocol_receive:", e)
        return "error", [str(e)]




