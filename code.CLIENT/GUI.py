import tkinter as tk
from client_class import Client
import queue
from tkinter import messagebox
import hashlib
import os
import logging

IP = "127.0.0.1"
PORT = 5555
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 600

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = os.path.join(LOG_DIR, 'gui.log')
if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)
logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)


class UserInterface:
    def __init__(self, root, client):
        """
        Initialize the UserInterface with the main Tkinter root and a client object.

        :param root: The main Tkinter root window.
        :param client: The client object that handles communication with the server.
        """
        try:
            self.root = root
            self.client = client
            self.master = root
            self.playing = False
            self.counter = 0

            # Create all application frames
            self.frames = {
                "welcome": self.create_welcome_screen(),
                "login": self.create_login_screen(),
                "signup": self.create_signup_screen(),
                "home": self.create_home_screen(),
                "add_song": self.create_add_song_screen(),
                "profile": self.create_profile_screen(),
            }

            self.show_frame("welcome")
            self.root.protocol("WM_DELETE_WINDOW", self.closing)


        except Exception as e:
            print(f"[ERROR] Failed to initialize UserInterface: {e}")
            
    def _setup_logging(self):
        try:
            if not os.path.isdir(self.LOG_DIR):
                os.makedirs(self.LOG_DIR)
            logging.basicConfig(format=self.LOG_FORMAT, filename=self.LOG_FILE, level=self.LOG_LEVEL)
        except Exception as e:
            print(f"Failed to setup logging: {e}")

    def show_frame(self, frame_name):
        """
        Display the specified frame on the main window, hiding all others.

        :param frame_name: The name of the frame to display (e.g., 'home', 'login', 'signup', etc.)
        """
        try:
            logging.debug(f"Showing frame: {frame_name}")

            # Hide all frames
            for frame in self.frames.values():
                frame.pack_forget()

            # Refresh specific frames if needed
            if frame_name == "home":
                self.frames["home"] = self.create_home_screen()
            elif frame_name == "profile":
                self.frames["profile"] = self.create_profile_screen()
            elif frame_name == "login":
                self.frames["login"] = self.create_login_screen()
            elif frame_name == "add_song":
                self.frames["add_song"] = self.create_add_song_screen()

            # Show the requested frame
            if frame_name in self.frames:
                self.frames[frame_name].pack(fill="both", expand=True)
            else:
                logging.debug(f"[WARNING] Frame '{frame_name}' not found.")

        except Exception as e:
            logging.debug(f"[ERROR] Failed to show frame '{frame_name}': {e}")

    def add_navigation_buttons(self, frame, current_screen):
        """
        Adds compact navigation buttons on the left side of the given frame.
        """
        try:
            navigation_frame = tk.Frame(frame, bg="#ecf0f1", width=120)
            navigation_frame.pack(side="left", fill="y", padx=5, pady=10)

            button_style = {
                "bg": "#bdc3c7",
                "fg": "black",
                "font": ("Arial", 10),
                "width": 12,  # 👈 רוחב מוקטן
                "relief": "flat",
                "activebackground": "#95a5a6"
            }

            nav_options = {
                "home": [("➕ Add song", "add_song"), ("👤 Profile", "profile")],
                "add_song": [("🏠 Home", "home"), ("👤 Profile", "profile")],
                "profile": [("🏠 Home", "home"), ("➕ Add song", "add_song")]
            }

            for label, target in nav_options.get(current_screen, []):
                tk.Button(
                    navigation_frame,
                    text=label,
                    command=lambda t=target: self.show_frame(t),
                    **button_style
                ).pack(pady=6)

            tk.Button(
                navigation_frame,
                text="🚪 Logout",
                command=self.logout,
                **button_style
            ).pack(pady=6)

        except Exception as e:
            logging.debug(f"Error in add_navigation_buttons: {e}")
            messagebox.showerror("Error", f"Failed to create navigation buttons: {e}")

    def create_welcome_screen(self):
        """
        Create and return the welcome screen frame.

        This screen includes a welcome message and buttons to navigate to
        the login and signup screens.

        :return: A Tkinter Frame object representing the welcome screen.
        """
        try:
            frame = tk.Frame(self.root, bg="#121212")

            tk.Label(
                frame,
                text="Welcome!",
                fg="#E0E0E0",
                bg="#121212",
                font=("Arial", 28, "bold")
            ).pack(pady=30)

            # הגדרת רוחב אחיד לכל הכפתורים
            btn_width = 15

            login_btn = tk.Button(
                frame,
                text="Login",
                command=lambda: self.show_frame("login"),
                bg="#1E90FF",
                fg="white",
                font=("Arial", 14, "bold"),
                activebackground="#1C86EE",
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                width=btn_width
            )
            login_btn.pack(pady=12)

            signup_btn = tk.Button(
                frame,
                text="Sign Up",
                command=lambda: self.show_frame("signup"),
                bg="#32CD32",
                fg="white",
                font=("Arial", 14, "bold"),
                activebackground="#2E8B57",
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                width=btn_width
            )
            signup_btn.pack(pady=12)

            return frame

        except Exception as e:
            logging.debug(f"[ERROR] Failed to create welcome screen: {e}")
            return tk.Frame(self.root)

    def create_signup_screen(self):
        """
        Create and return the sign-up screen frame.

        This screen allows the user to enter a username, password, and password confirmation
        in order to create a new account. Also includes a 'Back' button to return to the welcome screen.

        :return: A Tkinter Frame object representing the sign-up screen.
        """
        try:
            frame = tk.Frame(self.root, bg="#2F2F2F")

            # מרכזים את כל התוכן במסגרת
            content_frame = tk.Frame(frame, bg="#2F2F2F")
            content_frame.pack(pady=40, padx=50)

            # כותרת גדולה ומרכזית מעל תיבות הטקסט
            tk.Label(
                content_frame,
                text="Sign Up",
                font=("Arial", 24, "bold"),
                fg="#F0F0F0",
                bg="#2F2F2F"
            ).pack(pady=(0, 30))

            username_var = tk.StringVar()
            password_var = tk.StringVar()
            confirm_password_var = tk.StringVar()

            label_style = {"bg": "#2F2F2F", "fg": "#CCCCCC", "font": ("Arial", 12, "bold"), "anchor": "center"}
            entry_style = {"bd": 2, "relief": "groove", "font": ("Arial", 12), "justify": "center"}

            # תוויות ותיבות קלט ממורכזים
            tk.Label(content_frame, text="Username", **label_style).pack(fill="x")
            tk.Entry(content_frame, textvariable=username_var, **entry_style).pack(pady=6, fill="x")

            tk.Label(content_frame, text="Password", **label_style).pack(fill="x")
            tk.Entry(content_frame, textvariable=password_var, show="*", **entry_style).pack(pady=6, fill="x")

            tk.Label(content_frame, text="Confirm Password", **label_style).pack(fill="x")
            tk.Entry(content_frame, textvariable=confirm_password_var, show="*", **entry_style).pack(pady=6, fill="x")

            signup_btn = tk.Button(
                content_frame,
                text="Sign Up",
                command=lambda: self.signup_action(username_var, password_var, confirm_password_var),
                bg="#32CD32",
                fg="white",
                font=("Arial", 14, "bold"),
                activebackground="#2E8B57",
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                width=20
            )
            signup_btn.pack(pady=15)

            back_btn = tk.Button(
                content_frame,
                text="Back",
                command=lambda: self.show_frame("welcome"),
                bg="#A9A9A9",
                fg="white",
                font=("Arial", 12, "bold"),
                activebackground="#808080",
                relief="flat",
                padx=15,
                pady=6,
                cursor="hand2",
                width=10
            )
            back_btn.pack()

            return frame

        except Exception as e:
            logging.debug(f"[ERROR] Failed to create sign-up screen: {e}")
            return tk.Frame(self.root)

    def signup_action(self, username_var, password_var, confirm_password_var):
        """
        Handle the sign-up action by retrieving user input,
        validating it, hashing the password, and sending a sign-up request to the server.

        :param username_var: Tkinter StringVar containing the username.
        :param password_var: Tkinter StringVar containing the password.
        :param confirm_password_var: Tkinter StringVar containing the password confirmation.
        """
        try:
            username = username_var.get().strip()
            password = password_var.get()
            confirm_password = confirm_password_var.get()

            logging.debug("Username:", username)
            logging.debug("Password:", password)
            logging.debug("Confirm Password:", confirm_password)

            # Validate input
            if not username or not password or not confirm_password:
                messagebox.showwarning("Input Error", "All fields are required.")
                return

            if password != confirm_password:
                messagebox.showerror("Password Error", "Passwords do not match!")
                return

            # Hash the password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Send sign-up request to server
            data = self.client.start_client("1", username, hashed_password)

            if data[0] == "T":
                self.show_frame("home")
            elif data[0] == "F":
                messagebox.showerror("Sign Up Failed", "Username already exists.")
            else:
                messagebox.showerror("Sign Up Error", f"Unexpected response from server: {data}")

        except Exception as e:
            logging.debug(f"[ERROR] Sign-up action failed: {e}")
            messagebox.showerror("Error", "An unexpected error occurred during sign-up.")

    def create_login_screen(self):
        """
        Create and return the login screen frame.

        This screen allows the user to enter a username and password
        and attempt to log in. Includes a 'Back' button to return to the welcome screen.

        :return: A Tkinter Frame object representing the login screen.
        """
        try:
            frame = tk.Frame(self.root, bg="#2F2F2F")

            # מרכזים את כל התוכן במסגרת פנימית
            content_frame = tk.Frame(frame, bg="#2F2F2F")
            content_frame.pack(pady=40, padx=50)

            # כותרת גדולה ומרכזית
            tk.Label(
                content_frame,
                text="Login",
                font=("Arial", 24, "bold"),
                fg="#F0F0F0",
                bg="#2F2F2F"
            ).pack(pady=(0, 30))

            username_var = tk.StringVar()
            password_var = tk.StringVar()

            label_style = {"bg": "#2F2F2F", "fg": "#CCCCCC", "font": ("Arial", 12, "bold"), "anchor": "center"}
            entry_style = {"bd": 2, "relief": "groove", "font": ("Arial", 12), "justify": "center"}

            # שדות קלט ממורכזים עם תוויות
            tk.Label(content_frame, text="Username", **label_style).pack(fill="x")
            tk.Entry(content_frame, textvariable=username_var, **entry_style).pack(pady=6, fill="x")

            tk.Label(content_frame, text="Password", **label_style).pack(fill="x")
            tk.Entry(content_frame, textvariable=password_var, show="*", **entry_style).pack(pady=6, fill="x")

            btn_width = 20  # רוחב אחיד לכפתורים

            login_btn = tk.Button(
                content_frame,
                text="Log In",
                command=lambda: self.login_action(username_var, password_var),
                bg="#1E90FF",
                fg="white",
                font=("Arial", 14, "bold"),
                activebackground="#1C86EE",
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                width=btn_width
            )
            login_btn.pack(pady=15)

            back_btn = tk.Button(
                content_frame,
                text="Back",
                command=lambda: self.show_frame("welcome"),
                bg="#A9A9A9",
                fg="white",
                font=("Arial", 12, "bold"),
                activebackground="#808080",
                relief="flat",
                padx=15,
                pady=6,
                cursor="hand2",
                width=10
            )
            back_btn.pack()

            return frame

        except Exception as e:
            logging.debug(f"[ERROR] Failed to create login screen: {e}")
            return tk.Frame(self.root)

    def login_action(self, username_var, password_var):
        """
        Handle the login action by retrieving the username and password,
        validating them, hashing the password, and sending the login request to the server.

        :param username_var: Tkinter StringVar containing the username.
        :param password_var: Tkinter StringVar containing the password.
        """
        try:
            username = username_var.get()
            password = password_var.get()

            logging.debug("Username:" + username)
            logging.debug("Password:" + password)

            # Validate inputs
            if not username or not password:
                messagebox.showwarning("Input Error", "Username and password cannot be empty.")
                return

            # Hash the password before sending
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Send login request to the server
            data = self.client.start_client("2", username, hashed_password)
            # Handle server response
            if data[0] == "T":
                self.show_frame("home")
            elif data[0] == "F":
                messagebox.showerror("Login Failed", "Username or password is incorrect.")
            else:
                messagebox.showerror("Login Error", f"Unexpected response from server: {data}")

        except Exception as e:
            logging.debug(f"[ERROR] Login action failed: {e}")
            messagebox.showerror("Error", "An unexpected error occurred during login.")

# ************************************************************************************************************************************************

    def create_home_screen(self):
        """
        Creates the main home screen, including:
        - Navigation menu
        - Music player bar
        - User greeting
        - List of available songs with play, queue, and like buttons
        - Access to liked songs and refresh option
        """
        try:
            # Main container
            main_frame = tk.Frame(self.root, bg="#F9F9F9")
            main_frame.pack(side="top", fill="both", expand=True)

            # Left-side navigation
            self.add_navigation_buttons(main_frame, "home")

            # Bottom music player
            self.create_music_player_bar(main_frame)

            # Main content area
            content_frame = tk.Frame(main_frame, bg="#F9F9F9")
            content_frame.pack(side="left", fill="both", expand=True, padx=25, pady=25)

            # Greeting header
            tk.Label(
                content_frame,
                text=f"Home - Hello {self.client.username}",
                font=("Helvetica", 22, "bold"),
                bg="#F9F9F9",
                fg="#333333"
            ).pack(anchor="w", pady=10)

            # Refresh row
            refresh_frame = tk.Frame(content_frame, bg="#F9F9F9")
            refresh_frame.pack(anchor="w", pady=(0, 15))

            tk.Label(refresh_frame, text="Refresh", font=("Helvetica", 13), bg="#F9F9F9", fg="#555555").pack(side="left", padx=(0, 6))
            tk.Button(
                refresh_frame,
                text="🔄",
                font=("Helvetica", 13),
                bg="#D9EAF7",
                fg="#1A73E8",
                relief="flat",
                command=self.refresh_home_screen,
                cursor="hand2",
                padx=8,
                pady=4
            ).pack(side="left")

            # Liked songs playlist
            liked_frame = tk.Frame(content_frame, bg="#F9F9F9")
            liked_frame.pack(anchor="w", pady=10)

            tk.Label(liked_frame, text="Liked Songs", font=("Helvetica", 16, "bold"), bg="#F9F9F9", fg="#444444").pack(side="left", padx=(0, 12))
            tk.Button(
                liked_frame,
                text="🎵",
                font=("Helvetica", 14),
                bg="#E3F2FD",
                fg="#1A73E8",
                relief="flat",
                cursor="hand2",
                command=lambda: self.play_playlist(self.client.liked_song),
                padx=10,
                pady=5
            ).pack(side="left")

            # Song list headers
            header_row = tk.Frame(content_frame, bg="#F9F9F9")
            header_row.pack(anchor="w", pady=8)

            header_style = {"bg": "#F9F9F9", "font": ("Helvetica", 13, "bold"), "fg": "#222222", "width": 15, "anchor": "w"}
            for header in ["Song Name", "Artist", "Play", "Queue", "Like"]:
                tk.Label(header_row, text=header, **header_style).pack(side="left", padx=8)

            # Song entries
            for song_name, (artist, song_id) in self.client.song_id_dict.items():
                self.create_song_row(content_frame, song_name, artist, song_id)

            return main_frame

        except Exception as e:
            logging.debug(f"[ERROR] Failed to create home screen: {e}")
            return tk.Frame(self.root)  # fallback to empty frame

    def create_song_row(self, parent, song_name, artist, song_id):
        """
        Creates a single row in the song list with song info and control buttons.

        :param parent: Parent frame to attach the row to.
        :param song_name: Name of the song.
        :param artist: Artist name.
        :param song_id: Song's unique identifier.
        """
        try:
            row = tk.Frame(parent, bg="#FFFFFF")
            row.pack(fill="x", pady=3)

            label_style = {"bg": "#FFFFFF", "font": ("Helvetica", 12), "width": 15, "anchor": "w", "fg": "#333333"}
            tk.Label(row, text=song_name, **label_style).pack(side="left", padx=6)
            tk.Label(row, text=artist, **label_style).pack(side="left", padx=6)

            btn_style = {
                "bg": "#1E90FF",  # כחול אחיד לכל הכפתורים
                "fg": "white",
                "font": ("Helvetica", 10, "bold"),
                "relief": "flat",
                "cursor": "hand2",
                "padx": 8,
                "pady": 3,
                "width": 7,
            }

            tk.Button(row, text="Play", command=lambda: self.play_song(song_id), **btn_style).pack(side="left", padx=6)
            tk.Button(row, text="Ad to Queue", command=lambda: self.add_song_to_queue(song_id), **btn_style).pack(side="left", padx=6)

            # Like button - לב אדום אם מאוהב, אפור אם לא
            liked = song_id in self.client.liked_song
            like_text = "❤" if liked else "🤍"
            like_fg = "#E53935" if liked else "#888888"  # אדום עז / אפור כהה

            like_button = tk.Button(
                row,
                text=like_text,
                bg="#FFFFFF",  # רקע לבן פשוט
                fg=like_fg,
                font=("Helvetica", 14),
                relief="flat",
                cursor="hand2",
                width=3,
                bd=0,
                highlightthickness=0,
            )
            like_button.config(command=lambda: self.like_song(song_id, like_button))
            like_button.pack(side="left", padx=6)

        except Exception as e:
            logging.debug(f"Error in creating song row: {e}")
            messagebox.showerror("Error", f"Failed to create song row: {e}")

    def add_song_to_queue(self, song_id):
        """
        Adds the specified song to the playback queue.

        :param song_id: Unique identifier of the song to add.
        """
        try:
            logging.debug(song_id)
            self.client.listen_song(song_id)
            if self.client.is_expired:
                messagebox.showerror("Error", "Token invalid or token has expired")
                self.logout()
        except Exception as e:
            logging.debug(f"Error in add_song_to_queue: {e}")
            messagebox.showerror("Error", f"Failed to add song to queue: {e}")

    def play_song(self, song_id):
        """
        Clears the current queue and plays the specified song.

        :param song_id: Unique identifier of the song to play.
        """
        try:
            logging.debug(song_id)
            self.client.q.clear_queue()
            self.client.listen_song(song_id)

            if self.playing:
                self.playing = False
                self.counter = 0

            self.play_pause()

            if self.client.is_expired:
                messagebox.showerror("Error", "Token invalid or token has expired")
                self.logout()
        except Exception as e:
            logging.debug(f"Error in play_song: {e}")
            messagebox.showerror("Error", f"Failed to play song: {e}")

    def like_song(self, song_id, like_button):
        """
        Toggles the like status of the specified song.

        :param song_id: Unique identifier of the song.
        :param like_button: The button widget to update its text/icon.
        """
        try:
            logging.debug(song_id)
            if song_id in self.client.liked_song:
                result = self.client.song_and_playlist("remove", "liked_song", song_id)
                if result[0] == "T":
                    like_button.config(text="🤍", fg="#888888")
                elif result[0] == "F":
                    messagebox.showerror("Error", result[1])
            else:
                result = self.client.song_and_playlist("add", "liked_song", song_id)
                if result[0] == "T":
                    like_button.config(text="❤", fg="#E53935")
                elif result[0] == "F":
                    messagebox.showerror("Error", result[1])

            if self.client.is_expired:
                messagebox.showerror("Error", "Token invalid or token has expired")
                self.logout()
        except Exception as e:
            logging.debug(f"Error in like_song: {e}")
            messagebox.showerror("Error", f"Failed to toggle like: {e}")

    def play_playlist(self, playlist):
        """
        Plays all songs in the given playlist.

        :param playlist: List or collection of song IDs to play.
        """
        try:
            self.client.play_playlist(playlist)
            self.play_pause()
        except Exception as e:
            logging.debug(f"Error in play_playlist: {e}")
            messagebox.showerror("Error", f"Failed to play playlist: {e}")

    def refresh_home_screen(self):
        """
        Refreshes the song dictionary and reloads the home screen UI.
        """
        try:
            if self.client.refresh_song_dict():
                self.show_frame("home")
                messagebox.showinfo("Refresh", "Refresh has been done successfully")
            else:
                messagebox.showerror("Refresh", "Error while refreshing")
        except Exception as e:
            logging.debug(f"Error in refresh_home_screen: {e}")
            messagebox.showerror("Error", f"Failed to refresh home screen: {e}")

    def create_add_song_screen(self):
        """
        Creates the UI frame for adding a new song, including input fields for song name,
        artist name, and file path, along with navigation buttons.
        """
        try:
            frame = tk.Frame(self.root, bg="#f0f0f0")  # רקע קליל ונעים

            # הוספת כפתורי ניווט בצד שמאל
            self.add_navigation_buttons(frame, "add_song")

            # אזור התוכן המרכזי
            content_frame = tk.Frame(frame, bg="#f0f0f0")
            content_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

            # כותרת
            tk.Label(content_frame, text="Add Song", font=("Arial", 20), bg="#f0f0f0").pack(anchor="w", pady=10)

            # משתנים לשדות הקלט
            song_name_var = tk.StringVar()
            artist_name_var = tk.StringVar()
            song_path_var = tk.StringVar()

            # שדות קלט עם תוויות פשוטות
            tk.Label(content_frame, text="Song Name:", bg="#f0f0f0").pack(anchor="w")
            tk.Entry(content_frame, textvariable=song_name_var, width=50).pack(pady=5)

            tk.Label(content_frame, text="Artist Name:", bg="#f0f0f0").pack(anchor="w")
            tk.Entry(content_frame, textvariable=artist_name_var, width=50).pack(pady=5)

            tk.Label(content_frame, text="Song File Path:", bg="#f0f0f0").pack(anchor="w")
            tk.Entry(content_frame, textvariable=song_path_var, width=50).pack(pady=5)

            # כפתור העלאה עם צבע רקע וניגודיות
            tk.Button(
                content_frame,
                text="Upload Song",
                bg="#4CAF50",
                fg="white",
                font=("Arial", 12, "bold"),
                command=lambda: self.upload_song_action(song_name_var, artist_name_var, song_path_var)
            ).pack(pady=15)

            return frame

        except Exception as e:
            logging.debug(f"Error in create_add_song_screen: {e}")
            messagebox.showerror("Error", f"Failed to create Add Song screen: {e}")

    def upload_song_action(self, song_name_var, artist_name_var, song_path_var):
        """
        Uploads a new song using the provided details.

        :param song_name_var: tk.StringVar holding the song's name
        :param artist_name_var: tk.StringVar holding the artist's name
        :param song_path_var: tk.StringVar holding the song file path
        """
        try:
            song_name = song_name_var.get()
            artist_name = artist_name_var.get()
            song_path = song_path_var.get()

            logging.debug("Song Name:", song_name)
            logging.debug("Artist Name:", artist_name)
            logging.debug("Song File Path:", song_path)

            msg = self.client.upload_song(song_name, artist_name, song_path)
            logging.debug(msg)
            if msg[0] == "F":
                messagebox.showerror("Error", msg[1])
            elif msg[0] == "T":
                messagebox.showinfo("Success", msg[1])

            if self.client.is_expired:
                messagebox.showerror("Error", "Token invalid or token has expired")
                self.logout()

        except Exception as e:
            logging.debug(f"Error in upload_song_action: {e}")
            messagebox.showerror("Error", f"Failed to upload song: {e}")

    def create_profile_screen(self):
        """
        Creates the profile screen frame displaying user info and liked songs.
        Includes navigation buttons on the left side.
        """
        try:
            frame = tk.Frame(self.root, bg="white")

            # Navigation
            self.add_navigation_buttons(frame, "profile")

            # Content
            content_frame = tk.Frame(frame, bg="white")
            content_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

            # Title
            tk.Label(
                content_frame,
                text="My Profile",
                font=("Arial", 20, "bold"),
                fg="#2c3e50",
                bg="white"
            ).pack(anchor="w", pady=10)

            # Section Title
            tk.Label(
                content_frame,
                text="Liked Songs",
                font=("Arial", 16, "bold"),
                fg="#1abc9c",
                bg="white"
            ).pack(anchor="w", pady=(10, 5))

            # Liked Songs List
            for song_id in self.client.liked_song:
                for song_name, (artist, sid) in self.client.song_id_dict.items():
                    if sid == song_id:
                        song_row = tk.Frame(content_frame, bg="#f7f7f7")
                        song_row.pack(fill="x", pady=3, padx=5)

                        tk.Label(
                            song_row,
                            text=song_name,
                            bg="#f7f7f7",
                            font=("Arial", 12),
                            width=20,
                            anchor="w"
                        ).pack(side="left", padx=5)

                        tk.Label(
                            song_row,
                            text=artist,
                            bg="#f7f7f7",
                            font=("Arial", 12),
                            width=20,
                            anchor="w"
                        ).pack(side="left", padx=5)

            return frame

        except Exception as e:
            logging.debug(f"Error in create_profile_screen: {e}")
            messagebox.showerror("Error", f"Failed to create profile screen: {e}")

    def logout(self):
        """
        Logs out the current user by sending a logout command to the client,
        resetting the client state, and showing the welcome screen.
        """
        try:
            self.client.gui_to_client_queue.put("logout")
            self.client.reset()
            self.show_frame("welcome")
        except Exception as e:
            logging.debug(f"Error during logout: {e}")
            messagebox.showerror("Error", f"Logout failed: {e}")

    def closing(self):
        """
        Handles application closing:
        Sends a shutdown command to the client,
        calls client exit cleanup,
        and destroys the main window.
        """
        try:
            logging.debug("closing")
            self.client.gui_to_client_queue.put("shutdown")
            self.client.exit()
        except Exception as e:
            logging.debug(f"Error during closing: {e}")
        finally:
            logging.debug("good bye")
            self.root.destroy()

# ***********************************************************************************
    def create_music_player_bar(self, main_frame):
        """
        Creates the music player bar at the bottom of the main frame with
        buttons for previous song (left), play/pause (center), and next song (right),
        using only pack geometry manager.
        """
        try:
            music_player = tk.Frame(main_frame, bg="blue", height=60)
            music_player.pack(side="bottom", fill="x")

            controls_frame = tk.Frame(music_player, bg="blue")
            controls_frame.pack(side="top", fill="x", expand=True)

            # Previous song button - packed to left
            tk.Button(controls_frame, text="⏮", font=("Arial", 16),
                      command=self.prev_song).pack(side="left", padx=20, pady=10)

            # Play/pause button wrapped in a frame, packed to left with expand to center it
            center_frame = tk.Frame(controls_frame, bg="blue")
            center_frame.pack(side="left", expand=True)

            self.play_pause_button = tk.Button(center_frame, text="▶", font=("Arial", 16), command=self.play_pause)
            self.play_pause_button.pack(padx=20, pady=10)

            # Next song button - packed to right
            tk.Button(controls_frame, text="⏭", font=("Arial", 16),
                      command=self.next_song).pack(side="right", padx=20, pady=10)

        except Exception as e:
            logging.debug(f"Error in create_music_player_bar: {e}")
            messagebox.showerror("Error", f"Failed to create music bar: {e}")

    def prev_song(self):
        """
        Plays the previous song if one exists.
        Sends a 'prev' command to the client via queue and updates the UI.
        """
        try:
            logging.debug("prev song")
            if self.client.q.prev_song_path != "":
                logging.debug(self.client.q.prev_song_path)
                self.client.gui_to_client_queue.put("prev")
                self.playing = True
                self.play_pause_button.config(text="⏹")
        except Exception as e:
            logging.debug(f"Error in prev_song: {e}")
            messagebox.showerror("Error", f"Failed to play previous song: {e}")

    def next_song(self):
        """
        Plays the next song in the queue if available.
        Sends a 'next' command to the client via queue and updates the UI.
        """
        try:
            logging.debug("next song")
            if not self.client.q.my_queue.empty():
                self.playing = True
                self.play_pause_button.config(text="⏹")
                self.client.gui_to_client_queue.put("next")
            logging.debug(self.playing)
        except Exception as e:
            logging.debug(f"Error in next_song: {e}")
            messagebox.showerror("Error", f"Failed to play next song: {e}")

    def play_pause(self):
        """
        Toggles between play and pause.
        Sends 'play', 'resume', or 'pause' command via the client queue based on the current state.
        """
        try:
            logging.debug(self.playing)
            logging.debug(self.client.q.my_queue.empty())

            if not self.playing:
                if not (self.client.q.my_queue.empty() and self.client.p.current_file == ""):
                    logging.debug(self.client.p.current_file)
                    self.play_pause_button.config(text="⏹")

                    if self.counter == 0:
                        self.client.gui_to_client_queue.put("play")
                    else:
                        self.client.gui_to_client_queue.put("resume")

                    self.counter += 1
                    self.master.after(100, self.check_result_queue)
                    self.playing = True

            else:  # currently playing
                self.play_pause_button.config(text="▶")
                self.client.gui_to_client_queue.put("pause")
                self.playing = False

        except Exception as e:
            logging.debug(f"Error in play_pause: {e}")
            messagebox.showerror("Error", f"Failed to toggle play/pause: {e}")

    def check_result_queue(self):
        """
        Checks for messages from the client thread to the GUI.
        If 'nothing to play' is received, stops playback and updates UI.
        If no message, checks again after 100ms.
        """
        try:
            result = self.client.client_to_gui_queue.get_nowait()
            logging.debug("Result from thread:", result)
            if result == "nothing to play":
                self.playing = False
                self.play_pause_button.config(text="▶")
                self.counter = 0
        except queue.Empty:
            self.master.after(100, self.check_result_queue)

    def start(self):
        """
        start tkinter loop
        """
        self.root.geometry("700x600")
        self.root.mainloop()


if __name__ == "__main__":
    try:
        client1 = Client(IP, PORT)
        root1 = tk.Tk()
        app = UserInterface(root1, client1)
        app.start()
    except Exception as error:
        logging.debug(error)
