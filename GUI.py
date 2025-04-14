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

        # יצירת משתני טקסט לשם משתמש וסיסמה
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        # שדות קלט שמקושרים למשתנים
        tk.Entry(frame, textvariable=self.username_var).pack(pady=10)
        tk.Entry(frame, textvariable=self.password_var, show="*").pack(pady=10)

        # כפתור להתחברות
        tk.Button(frame, text="Log In", command=self.login_action).pack(pady=10)

        return frame

    def login_action(self):
        username = self.username_var.get()
        password = self.password_var.get()
        print("Username:", username)
        print("Password:", password)
        # כאן אפשר להוסיף בדיקה או לעבור למסך הבית
        self.show_frame("home")


    def create_signup_screen(self):
        frame = tk.Frame(self.root, bg="gray")
        tk.Label(frame, text="Sign Up", font=("Arial", 20)).pack(pady=20)

        # יצירת משתני טקסט לשם משתמש, סיסמה ואישור סיסמה
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_password_var = tk.StringVar()

        # שדות קלט לשם משתמש, סיסמה ואישור סיסמה
        tk.Label(frame, text="Username").pack()
        tk.Entry(frame, textvariable=self.username_var).pack(pady=5)

        tk.Label(frame, text="Password").pack()
        tk.Entry(frame, textvariable=self.password_var, show="*").pack(pady=5)

        tk.Label(frame, text="Confirm Password").pack()
        tk.Entry(frame, textvariable=self.confirm_password_var, show="*").pack(pady=5)

        # כפתור הרשמה
        tk.Button(frame, text="Sign Up", command=self.signup_action).pack(pady=10)

        return frame

    def signup_action(self):
        username = self.username_var.get()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()

        print("Username:", username)
        print("Password:", password)
        print("Confirm Password:", confirm_password)

        # בדיקה אם הסיסמה ואישור הסיסמה תואמים
        if password == confirm_password:
            print("Passwords match!")
            # כאן אפשר להוסיף קוד להירשם למערכת ולעבור למסך הבא
            self.show_frame("home")
        else:
            print("Passwords do not match!")
            # אפשר להוסיף הודעת שגיאה למשתמש במקרה של חוסר התאמה


    def create_home_screen(self):
        frame = tk.Frame(self.root, bg="white")
        tk.Label(frame, text="Home", font=("Arial", 20)).pack(pady=20)
        # הוספת כפתורי ניווט
        self.add_navigation_buttons(frame, "home")
        return frame

    def create_add_song_screen(self):
        frame = tk.Frame(self.root, bg="white")
        tk.Label(frame, text="Add Song", font=("Arial", 20)).pack(pady=20)
        # הוספת כפתורי ניווט
        self.add_navigation_buttons(frame, "add_song")
        return frame

    def create_profile_screen(self):
        frame = tk.Frame(self.root, bg="white")
        tk.Label(frame, text="My Profile", font=("Arial", 20)).pack(pady=20)
        # הוספת כפתורי ניווט
        self.add_navigation_buttons(frame, "profile")
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

    def create_player_frame(self):
        frame = tk.Frame(self.root, bg="black", height=60)
        frame.pack_propagate(0)
        frame.place(relx=0, rely=1.0, anchor='sw', relwidth=1.0, height=60)
        tk.Label(frame, text="♪ Now Playing ♪", fg="white", bg="black").pack(side="left", padx=10)
        return frame



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
