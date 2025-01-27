import socket
import os

FOLDER = r"C:\musicCyber"  # נתיב לתיקיית השירים
IP = '127.0.0.1'
PORT = 2222
QUEUE_LEN = 1



def main():
    """
    מתחבר ללקוח, מקבל בקשות שירים ושולח את תוכן הקובץ אם נמצא.
    """
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        my_socket.bind((IP, PORT))
        my_socket.listen(QUEUE_LEN)

        while True:
            client_socket, client_address = my_socket.accept()
            print(f"Client connected: {client_address}")
            try:
                while True:
                    # קבלת שם השיר מהלקוח
                    song_name = client_socket.recv(10).decode()
                    song_name += ".mp3"
                    print("Requested song name: " + song_name)

                    # בניית הנתיב לשיר
                    song_path = os.path.join(FOLDER, song_name)
                    print("path: " + song_path)
                    # בדיקה אם השיר קיים בתיקייה
                    if os.path.exists(song_path) and os.path.isfile(song_path):
                        # שליחת תוכן הקובץ
                        with open(song_path, "rb") as file:
                            song_bytes = file.read()
                            client_socket.send(song_bytes)
                        print("File sent successfully!")
                    else:
                        # שליחת הודעה ללקוח שהשיר לא נמצא
                        error_msg = "not found"
                        client_socket.send(error_msg.encode())
                        print("File not found: " + song_name)

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
