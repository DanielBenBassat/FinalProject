import tkinter as tk

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600


class UserInterface:
    def __init__(self, root):
        self.root = root
        self.frames = {
            "welcome": self.create_welcome_screen(),
            "login": self.create_login_screen(),
            "signup": self.create_signup_screen(),
            "home": self.create_home_screen(),
            "add_song": self.create_add_song_screen(),
            "profile": self.create_profile_screen(),
            "playlist": self.create_playlist_screen()
        }

        # הצגת מסך ברירת המחדל (ברוכים הבאים)
        self.show_frame("welcome")


    def show_frame(self, frame_name):
        # הסתרת כל המסכים
        for frame in self.frames.values():
            frame.pack_forget()

        # הצגת המסך הנבחר
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

        # הוספת שדות קלט למסך התחברות (שם משתמש וסיסמה)
        tk.Entry(frame).pack(pady=10)
        tk.Entry(frame, show="*").pack(pady=10)

        # כפתור להתחברות
        tk.Button(frame, text="Log In", command=self.login_action).pack(pady=10)
        return frame

    def create_signup_screen(self):
        frame = tk.Frame(self.root, bg="lightgray")
        tk.Label(frame, text="Sign Up", font=("Arial", 20)).pack(pady=20)

        # הוספת שדות קלט למסך הרשמה (שם משתמש, סיסמה, אישור סיסמה)
        tk.Entry(frame).pack(pady=10)
        tk.Entry(frame, show="*").pack(pady=10)
        tk.Entry(frame, show="*").pack(pady=10)

        # כפתור להרשמה
        tk.Button(frame, text="Sign Up", command=self.signup_action).pack(pady=10)
        return frame

    def create_home_screen(self):
        frame = tk.Frame(self.root, bg="white")
        tk.Label(frame, text="Home", font=("Arial", 20)).pack(pady=20)
        return frame

    def create_add_song_screen(self):
        frame = tk.Frame(self.root, bg="white")
        tk.Label(frame, text="Add Song", font=("Arial", 20)).pack(pady=20)
        return frame

    def create_profile_screen(self):
        frame = tk.Frame(self.root, bg="white")
        tk.Label(frame, text="My Profile", font=("Arial", 20)).pack(pady=20)
        return frame

    def create_playlist_screen(self):
        frame = tk.Frame(self.root, bg="white")
        tk.Label(frame, text="Playlist", font=("Arial", 20)).pack(pady=20)
        return frame

    def create_player_frame(self):
        frame = tk.Frame(self.root, bg="black", height=60)
        frame.pack_propagate(0)
        frame.place(relx=0, rely=1.0, anchor='sw', relwidth=1.0, height=60)
        tk.Label(frame, text="♪ Now Playing ♪", fg="white", bg="black").pack(side="left", padx=10)
        return frame



    def login_action(self):
        # לוגיקה של התחברות
        print("User logged in")

    def signup_action(self):
        # לוגיקה של הרשמה
        print("User signed up")

    def start(self):
        """
        התחלת הלולאה של tkinter.
        """
        self.root.geometry("600x600")  # הגדרת גודל החלון
        self.root.mainloop()  # התחלת הלולאה של tkinter

# יצירת החלון הראשי והפעלת הממשק
if __name__ == "__main__":
    root = tk.Tk()  # יצירת מופע חלון tkinter
    app = UserInterface(root)  # יצירת מופע של המחלקה UserInterface
    app.start()  # קריאה לפעולה שפותחת את mainloop
