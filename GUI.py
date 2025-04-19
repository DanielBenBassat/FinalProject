import tkinter as tk
import pickle
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
from client_function import Client
from player import MusicPlayer
import os
import threading

class UserInterface:
    def __init__(self, root, client):
        self.root = root
        self.client = client
       #self.songs_list = {} #
        self.frames = {
            "welcome": self.create_welcome_screen(),
            "login": self.create_login_screen(),
            "signup": self.create_signup_screen(),
            "home": self.create_home_screen(),
            "add_song": self.create_add_song_screen(),
            "profile": self.create_profile_screen(),
            "playlist": self.create_playlist_screen()
        }
        self.playing = False  # מעקב מצב ניגון
        self.counter = 0


    # הצגת מסך ברירת המחדל (ברוכים הבאים)
        self.show_frame("welcome")





    def show_frame(self, frame_name):
        # הסתרת כל המסכים
        for frame in self.frames.values():
            frame.pack_forget()
        # הצגת המסך הנבחר
        if frame_name == "home":
            self.frames["home"] = self.create_home_screen()


        self.frames[frame_name].pack(fill="both", expand=True)


    def create_welcome_screen(self):
        frame = tk.Frame(self.root, bg="black")
        tk.Label(frame, text="Welcome!", fg="white", bg="black", font=("Arial", 24)).pack(pady=20)

        # כפתור להתחברות
        tk.Button(frame, text="Login", command=lambda: self.show_frame("login")).pack(pady=10)

        # כפתור להרשמה
        tk.Button(frame, text="Sign Up", command=lambda: self.show_frame("signup")).pack(pady=10)

        return frame

    def create_login_screen(self):
        frame = tk.Frame(self.root, bg="gray")
        tk.Label(frame, text="Login", font=("Arial", 20)).pack(pady=20)

        # יצירת משתני טקסט לשם משתמש וסיסמה
        username_var = tk.StringVar()
        password_var = tk.StringVar()

        # שדות קלט שמקושרים למשתנים
        tk.Label(frame, text="Username").pack()
        tk.Entry(frame, textvariable=username_var).pack(pady=5)

        tk.Label(frame, text="Password").pack()
        tk.Entry(frame, textvariable=password_var, show="*").pack(pady=5)

        # כפתור להתחברות
        tk.Button(frame, text="Log In", command=lambda: self.login_action(username_var, password_var)).pack(pady=10)

        return frame

    def login_action(self, username_var, password_var):
        username = username_var.get()
        password = password_var.get()

        print("Username:", username)
        print("Password:", password)
        # כאן אפשר להוסיף בדיקה או לעבור למסך הבית
        # בדוק כאן אם הם ריקים
        if not username or not password:
            print("Error: Username or Password is empty!")
        data = client.start_client("2", username, password)
        if data[0] == "True":
            self.songs_list = pickle.loads(data[2])

            self.show_frame("home")


    def create_signup_screen(self):
        frame = tk.Frame(self.root, bg="gray")
        tk.Label(frame, text="Sign Up", font=("Arial", 20)).pack(pady=20)

        # יצירת משתני טקסט לשם משתמש, סיסמה ואישור סיסמה
        username_var = tk.StringVar()
        password_var = tk.StringVar()
        confirm_password_var = tk.StringVar()

        # שדות קלט לשם משתמש, סיסמה ואישור סיסמה
        tk.Label(frame, text="Username").pack()
        tk.Entry(frame, textvariable=username_var).pack(pady=5)

        tk.Label(frame, text="Password").pack()
        tk.Entry(frame, textvariable=password_var, show="*").pack(pady=5)

        tk.Label(frame, text="Confirm Password").pack()
        tk.Entry(frame, textvariable=confirm_password_var, show="*").pack(pady=5)

        # כפתור הרשמה
        tk.Button(frame, text="Sign Up", command=lambda: self.signup_action(username_var, password_var, confirm_password_var)).pack(pady=10)

        return frame

    def signup_action(self, username_var, password_var, confirm_password_var):
        username = username_var.get()
        password = password_var.get()
        confirm_password = confirm_password_var.get()

        print("Username:", username)
        print("Password:", password)
        print("Confirm Password:", confirm_password)

        # בדיקה אם הסיסמה ואישור הסיסמה תואמים
        if password == confirm_password:
            print("Passwords match!")
            # כאן אפשר להוסיף קוד להירשם למערכת ולעבור למסך הבא
            data = client.start_client("1", username, password)
            if data[0] == "True":
                #self.songs_list = pickle.loads(data[2])
                self.show_frame("home")
        else:
            print("Passwords do not match!")
            # אפשר להוסיף הודעת שגיאה למשתמש במקרה של חוסר התאמה
    def create_music_player_bar(self, main_frame):
        music_player = tk.Frame(main_frame, bg="blue", height=60)
        music_player.pack(side="bottom", fill="x")

        # פריים פנימי שמרכז את כפתור ההפעלה
        controls_frame = tk.Frame(music_player, bg="blue")
        controls_frame.pack(side="top", fill="x", expand=True)

        # כפתור שיר קודם - מצד שמאל
        tk.Button(controls_frame, text="⏮", font=("Arial", 16), command=self.prev_song).pack(side="left", padx=20, pady=10)

        # כפתור הפעלה/השהיה - במרכז
        self.play_pause_button = tk.Button(controls_frame, text="▶", font=("Arial", 16), command=lambda: self.play_pause())
        self.play_pause_button.pack(side="left", padx=20, pady=10, expand=True)

    # כפתור שיר הבא - מצד ימין
        tk.Button(controls_frame, text="⏭", font=("Arial", 16), command=self.next_song).pack(side="left", padx=20, pady=10)
    def prev_song(self):
        print("prev song")
        player_thread = threading.Thread(target=self.client.player, args=("play",), daemon=True)
        player_thread.start()
    def next_song(self):
        print("next song")
        player_thread = threading.Thread(target=self.client.player, args=("next",), daemon=True)
        player_thread.start()
        print(self.playing)

    def play_pause(self):
        print(self.playing)
        if not self.playing:
            self.play_pause_button.config(text="⏹")
            if self.counter == 0:
                player_thread = threading.Thread(target=self.client.player, args=("play",), daemon=True)
            else:
                player_thread = threading.Thread(target=self.client.player, args=("resume",), daemon=True)
            self.counter = 1 + self.counter

        else:
            self.play_pause_button.config(text="▶")
            player_thread = threading.Thread(target=self.client.player, args=("pause",), daemon=True)

        player_thread.start()

        self.playing = not self.playing

    def create_home_screen(self):
        # פריים עיקרי של התוכן והניווט
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(side="top", fill="both", expand=True)

        # ניווט בצד שמאל
        self.add_navigation_buttons(main_frame, "home")

        # נגן מוזיקה בתחתית רק במסך הבית
        self.create_music_player_bar(main_frame)

        # פריים לתוכן המרכזי
        content_frame = tk.Frame(main_frame, bg="white")
        content_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # כותרת עליונה
        tk.Label(content_frame, text="Home", font=("Arial", 20), bg="white").pack(anchor="w", pady=10)

        # שורת כותרות
        header_row = tk.Frame(content_frame, bg="white")
        header_row.pack(anchor="w", pady=5)
        tk.Label(header_row, text="Song Name", bg="white", font=("Arial", 12, "bold"), width=12, anchor="w").pack(side="left", padx=5)
        tk.Label(header_row, text="Artist", bg="white", font=("Arial", 12, "bold"), width=12, anchor="w").pack(side="left", padx=5)
        tk.Label(header_row, text="Play", bg="white", font=("Arial", 12, "bold"), width=12, anchor="w").pack(side="left", padx=5)

        # רשימת שירים
        for key, value in self.client.song_id_dict.items():
            song_name = key
            artist = value[0]
            song_id = value[1]

            song_row = tk.Frame(content_frame, bg="white")
            song_row.pack(fill="x", pady=5)

            tk.Label(song_row, text=song_name, bg="white", font=("Arial", 12), width=12, anchor="w").pack(side="left", padx=5)
            tk.Label(song_row, text=artist, bg="white", font=("Arial", 12), width=12, anchor="w").pack(side="left", padx=5)
            tk.Button(song_row, text="choose", command=lambda sid=song_id: self.play_song(sid)).pack(side="left", padx=5)



        return main_frame


    def play_song(self, song_id):
        print(song_id)
        #self.playing = True
        self.client.listen_song(song_id)


    def create_add_song_screen(self):
        frame = tk.Frame(self.root, bg="white")

        # קודם כל כפתורי ניווט בצד שמאל
        self.add_navigation_buttons(frame, "add_song")

        # מסגרת לתוכן המרכזי (כותרת + שדות קלט)
        content_frame = tk.Frame(frame, bg="white")
        content_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # כותרת "Add Song"
        tk.Label(content_frame, text="Add Song", font=("Arial", 20), bg="white").pack(anchor="w", pady=10)

        # משתנים לשמירת הקלט
        song_name_var = tk.StringVar()
        artist_name_var = tk.StringVar()
        song_path_var = tk.StringVar()

        # שדה שם השיר
        tk.Label(content_frame, text="Song Name:", bg="white").pack(anchor="w", padx=10)
        tk.Entry(content_frame, textvariable=song_name_var, width=50).pack(pady=5)

        # שדה שם האומן
        tk.Label(content_frame, text="Artist Name:", bg="white").pack(anchor="w", padx=10)
        tk.Entry(content_frame, textvariable=artist_name_var, width=50).pack(pady=5)

        # שדה כתיבת הקובץ
        tk.Label(content_frame, text="Song File Path:", bg="white").pack(anchor="w", padx=10)
        tk.Entry(content_frame, textvariable=song_path_var, width=50).pack(pady=5)

        # כפתור להעלאה
        tk.Button(content_frame, text="Upload Song", command=lambda: self.upload_song_action(song_name_var, artist_name_var, song_path_var)).pack(pady=15)

        return frame

    def upload_song_action(self,song_name_var, artist_name_var, song_path_var):
        song_name = song_name_var.get()
        artist_name = artist_name_var.get()
        song_path = song_path_var.get()

        print("Song Name:", song_name)
        print("Artist Name:", artist_name)
        print("Song File Path:", song_path)

        msg = client.add_song(song_name, artist_name, song_path)
        if msg == 'Token has expired' or msg == "Invalid token":
            self.show_frame("home")



    def create_profile_screen(self):
        frame = tk.Frame(self.root, bg="white")

        # קודם כל כפתורי ניווט בצד שמאל
        self.add_navigation_buttons(frame, "profile")

        # מסגרת לתוכן המרכזי (כותרת + פרופיל המשתמש)
        content_frame = tk.Frame(frame, bg="white")
        content_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # כותרת "My Profile"
        tk.Label(content_frame, text="My Profile", font=("Arial", 20), bg="white").pack(anchor="w", pady=10)

        # תוכן נוסף לפרופיל (לדוגמה: מידע על המשתמש, תמונה, וכו')
        # אפשר להוסיף שדות נוספים כפי שתצטרך

        return frame


    def add_navigation_buttons(self, frame, current_screen):
        # כפתור ניווט בצד המסך
        navigation_frame = tk.Frame(frame, bg="gray")
        navigation_frame.pack(side="left", fill="y", padx=10, pady=10)

        # כפתור ניווט ממסך "בית"
        if current_screen == "home":
            tk.Button(navigation_frame, text="Go to Add Song", command=lambda: self.show_frame("add_song")).pack(pady=10)
            tk.Button(navigation_frame, text="Go to Profile", command=lambda: self.show_frame("profile")).pack(pady=10)

        # כפתור ניווט ממסך "הוספת שיר"
        elif current_screen == "add_song":
            tk.Button(navigation_frame, text="Go to Home", command=lambda: self.show_frame("home")).pack(pady=10)
            tk.Button(navigation_frame, text="Go to Profile", command=lambda: self.show_frame("profile")).pack(pady=10)

        # כפתור ניווט ממסך "פרופיל"
        elif current_screen == "profile":
            tk.Button(navigation_frame, text="Go to Home", command=lambda: self.show_frame("home")).pack(pady=10)
            tk.Button(navigation_frame, text="Go to Add Song", command=lambda: self.show_frame("add_song")).pack(pady=10)










    def create_playlist_screen(self):
        frame = tk.Frame(self.root, bg="white")
        tk.Label(frame, text="Playlist", font=("Arial", 20)).pack(pady=20)
        return frame





    def start(self):
        """
        התחלת הלולאה של tkinter.
        """
        self.root.geometry("600x600")  # הגדרת גודל החלון
        self.root.mainloop()  # התחלת הלולאה של tkinter

# יצירת החלון הראשי וה
if __name__ == "__main__":
    client = Client()
    root = tk.Tk()  # יצירת מופע חלון tkinter
    app = UserInterface(root, client)  # יצירת מופע של המחלקה UserInterface
    app.start()  # קריאה לפעולה שפותחת את mainloop