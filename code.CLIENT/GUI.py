import tkinter as tk
from client_class import Client
import queue
from tkinter import messagebox
import hashlib

IP = "127.0.0.1"
PORT = 5555
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 600


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

    def show_frame(self, frame_name):
        """
        Display the specified frame on the main window, hiding all others.

        :param frame_name: The name of the frame to display (e.g., 'home', 'login', 'signup', etc.)
        """
        try:
            print(f"Showing frame: {frame_name}")

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
                print(f"[WARNING] Frame '{frame_name}' not found.")

        except Exception as e:
            print(f"[ERROR] Failed to show frame '{frame_name}': {e}")

    def add_navigation_buttons(self, frame, current_screen):
        """
        Adds navigation buttons on the left side of the given frame.
        Buttons vary depending on the current screen to allow navigation between
        'home', 'add_song', and 'profile' screens, plus a logout button.

        :param frame: The parent tkinter frame to place navigation buttons into.
        :param current_screen: String identifier of the current screen ("home", "add_song", "profile").
        """
        try:
            navigation_frame = tk.Frame(frame, bg="gray")
            navigation_frame.pack(side="left", fill="y", padx=10, pady=10)

            if current_screen == "home":
                tk.Button(navigation_frame, text="Go to Add Song", command=lambda: self.show_frame("add_song")).pack(pady=10)
                tk.Button(navigation_frame, text="Go to Profile", command=lambda: self.show_frame("profile")).pack(pady=10)

            elif current_screen == "add_song":
                tk.Button(navigation_frame, text="Go to Home", command=lambda: self.show_frame("home")).pack(pady=10)
                tk.Button(navigation_frame, text="Go to Profile", command=lambda: self.show_frame("profile")).pack(pady=10)

            elif current_screen == "profile":
                tk.Button(navigation_frame, text="Go to Home", command=lambda: self.show_frame("home")).pack(pady=10)
                tk.Button(navigation_frame, text="Go to Add Song", command=lambda: self.show_frame("add_song")).pack(pady=10)

            tk.Button(navigation_frame, text="Logout", command=self.logout).pack(pady=10)

        except Exception as e:
            print(f"Error in add_navigation_buttons: {e}")
            messagebox.showerror("Error", f"Failed to create navigation buttons: {e}")

    def create_welcome_screen(self):
        """
        Create and return the welcome screen frame.

        This screen includes a welcome message and buttons to navigate to
        the login and signup screens.

        :return: A Tkinter Frame object representing the welcome screen.
        """
        try:
            frame = tk.Frame(self.root, bg="black")
            tk.Label(frame, text="Welcome!", fg="white", bg="black", font=("Arial", 24)).pack(pady=20)

            # Login button
            tk.Button(frame, text="Login", command=lambda: self.show_frame("login")).pack(pady=10)

            # Sign Up button
            tk.Button(frame, text="Sign Up", command=lambda: self.show_frame("signup")).pack(pady=10)

            return frame

        except Exception as e:
            print(f"[ERROR] Failed to create welcome screen: {e}")
            return tk.Frame(self.root)

    def create_signup_screen(self):
        """
        Create and return the sign-up screen frame.

        This screen allows the user to enter a username, password, and password confirmation
        in order to create a new account. Also includes a 'Back' button to return to the welcome screen.

        :return: A Tkinter Frame object representing the sign-up screen.
        """
        try:
            frame = tk.Frame(self.root, bg="gray")
            tk.Label(frame, text="Sign Up", font=("Arial", 20)).pack(pady=20)

            # Text variables for user input
            username_var = tk.StringVar()
            password_var = tk.StringVar()
            confirm_password_var = tk.StringVar()

            # Input fields
            tk.Label(frame, text="Username").pack()
            tk.Entry(frame, textvariable=username_var).pack(pady=5)

            tk.Label(frame, text="Password").pack()
            tk.Entry(frame, textvariable=password_var, show="*").pack(pady=5)

            tk.Label(frame, text="Confirm Password").pack()
            tk.Entry(frame, textvariable=confirm_password_var, show="*").pack(pady=5)

            # Buttons
            tk.Button(
                frame,
                text="Sign Up",
                command=lambda: self.signup_action(username_var, password_var, confirm_password_var)
            ).pack(pady=10)
            tk.Button(frame, text="Back", command=lambda: self.show_frame("welcome")).pack(pady=5)

            return frame

        except Exception as e:
            print(f"[ERROR] Failed to create sign-up screen: {e}")
            return tk.Frame(self.root)  # fallback to empty frame

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

            print("Username:", username)
            print("Password:", password)
            print("Confirm Password:", confirm_password)

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
            print(f"[ERROR] Sign-up action failed: {e}")
            messagebox.showerror("Error", "An unexpected error occurred during sign-up.")

    def create_login_screen(self):
        """
        Create and return the login screen frame.

        This screen allows the user to enter a username and password
        and attempt to log in. Includes a 'Back' button to return to the welcome screen.

        :return: A Tkinter Frame object representing the login screen.
        """
        try:
            frame = tk.Frame(self.root, bg="gray")
            tk.Label(frame, text="Login", font=("Arial", 20)).pack(pady=20)

            # Text variables for username and password input
            username_var = tk.StringVar()
            password_var = tk.StringVar()

            # Username input field
            tk.Label(frame, text="Username").pack()
            tk.Entry(frame, textvariable=username_var).pack(pady=5)

            # Password input field
            tk.Label(frame, text="Password").pack()
            tk.Entry(frame, textvariable=password_var, show="*").pack(pady=5)

            # Login and Back buttons
            tk.Button(frame, text="Log In", command=lambda: self.login_action(username_var, password_var)).pack(pady=10)
            tk.Button(frame, text="Back", command=lambda: self.show_frame("welcome")).pack(pady=5)

            return frame

        except Exception as e:
            print(f"[ERROR] Failed to create login screen: {e}")
            return tk.Frame(self.root)  # fallback to empty frame

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

            print("Username:", username)
            print("Password:", password)

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
            print(f"[ERROR] Login action failed: {e}")
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
            main_frame = tk.Frame(self.root, bg="white")
            main_frame.pack(side="top", fill="both", expand=True)

            # Left-side navigation
            self.add_navigation_buttons(main_frame, "home")

            # Bottom music player
            self.create_music_player_bar(main_frame)

            # Main content area
            content_frame = tk.Frame(main_frame, bg="white")
            content_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

            # Greeting header
            tk.Label(
                content_frame,
                text=f"Home - Hello {self.client.username}",
                font=("Arial", 20),
                bg="white"
            ).pack(anchor="w", pady=10)

            # Refresh row
            refresh_frame = tk.Frame(content_frame, bg="white")
            refresh_frame.pack(anchor="w", pady=(0, 10))

            tk.Label(refresh_frame, text="Refresh", font=("Arial", 12), bg="white").pack(side="left", padx=(0, 5))
            tk.Button(refresh_frame, text="🔄", font=("Arial", 12), command=self.refresh_home_screen).pack(side="left")

            # Liked songs playlist
            liked_frame = tk.Frame(content_frame, bg="white")
            liked_frame.pack(anchor="w", pady=10)

            tk.Label(liked_frame, text="Liked Songs", font=("Arial", 14), bg="white").pack(side="left", padx=(0, 10))
            tk.Button(
                liked_frame,
                text="🎵",
                font=("Arial", 12),
                command=lambda: self.play_playlist(self.client.liked_song)
            ).pack(side="left")

            # Song list headers
            header_row = tk.Frame(content_frame, bg="white")
            header_row.pack(anchor="w", pady=5)
            for header in ["Song Name", "Artist", "Play"]:
                tk.Label(header_row, text=header, bg="white", font=("Arial", 12, "bold"), width=12, anchor="w").pack(side="left", padx=5)

            # Song entries
            for song_name, (artist, song_id) in self.client.song_id_dict.items():
                self.create_song_row(content_frame, song_name, artist, song_id)

            return main_frame

        except Exception as e:
            print(f"[ERROR] Failed to create home screen: {e}")
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
            row = tk.Frame(parent, bg="white")
            row.pack(fill="x", pady=5)

            tk.Label(row, text=song_name, bg="white", font=("Arial", 12), width=12, anchor="w").pack(side="left", padx=5)
            tk.Label(row, text=artist, bg="white", font=("Arial", 12), width=12, anchor="w").pack(side="left", padx=5)

            tk.Button(row, text="play", command=lambda: self.play_song(song_id)).pack(side="left", padx=5)
            tk.Button(row, text="add to queue", command=lambda: self.add_song_to_queue(song_id)).pack(side="left", padx=5)

            liked = song_id in self.client.liked_song
            like_text = "❤" if liked else "🤍"
            like_button = tk.Button(row, text=like_text)
            like_button.config(command=lambda: self.like_song(song_id, like_button))
            like_button.pack(side="left", padx=5)
        except Exception as e:
            print(f"Error in creating song row: {e}")
            messagebox.showerror("Error", f"Failed to create song row: {e}")

    def add_song_to_queue(self, song_id):
        """
        Adds the specified song to the playback queue.

        :param song_id: Unique identifier of the song to add.
        """
        try:
            print(song_id)
            self.client.listen_song(song_id)
            if self.client.is_expired:
                messagebox.showerror("Error", "Token invalid or token has expired")
                self.logout()
        except Exception as e:
            print(f"Error in add_song_to_queue: {e}")
            messagebox.showerror("Error", f"Failed to add song to queue: {e}")

    def play_song(self, song_id):
        """
        Clears the current queue and plays the specified song.

        :param song_id: Unique identifier of the song to play.
        """
        try:
            print(song_id)
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
            print(f"Error in play_song: {e}")
            messagebox.showerror("Error", f"Failed to play song: {e}")

    def like_song(self, song_id, like_button):
        """
        Toggles the like status of the specified song.

        :param song_id: Unique identifier of the song.
        :param like_button: The button widget to update its text/icon.
        """
        try:
            print(song_id)
            if song_id in self.client.liked_song:
                result = self.client.song_and_playlist("remove", "liked_song", song_id)
                if result[0] == "T":
                    like_button.config(text="🤍")
                elif result[0] == "F":
                    messagebox.showerror("Error", result[1])
            else:
                result = self.client.song_and_playlist("add", "liked_song", song_id)
                if result[0] == "T":
                    like_button.config(text="❤")
                elif result[0] == "F":
                    messagebox.showerror("Error", result[1])

            if self.client.is_expired:
                messagebox.showerror("Error", "Token invalid or token has expired")
                self.logout()
        except Exception as e:
            print(f"Error in like_song: {e}")
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
            print(f"Error in play_playlist: {e}")
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
            print(f"Error in refresh_home_screen: {e}")
            messagebox.showerror("Error", f"Failed to refresh home screen: {e}")

    def create_add_song_screen(self):
        """
        Creates the UI frame for adding a new song, including input fields for song name,
        artist name, and file path, along with navigation buttons.
        """
        try:
            frame = tk.Frame(self.root, bg="white")

            # Add navigation buttons on the left
            self.add_navigation_buttons(frame, "add_song")

            # Main content frame for title and input fields
            content_frame = tk.Frame(frame, bg="white")
            content_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

            # Title label
            tk.Label(content_frame, text="Add Song", font=("Arial", 20), bg="white").pack(anchor="w", pady=10)

            # Variables to hold input data
            song_name_var = tk.StringVar()
            artist_name_var = tk.StringVar()
            song_path_var = tk.StringVar()

            # Song Name input
            tk.Label(content_frame, text="Song Name:", bg="white").pack(anchor="w", padx=10)
            tk.Entry(content_frame, textvariable=song_name_var, width=50).pack(pady=5)

            # Artist Name input
            tk.Label(content_frame, text="Artist Name:", bg="white").pack(anchor="w", padx=10)
            tk.Entry(content_frame, textvariable=artist_name_var, width=50).pack(pady=5)

            # Song File Path input
            tk.Label(content_frame, text="Song File Path:", bg="white").pack(anchor="w", padx=10)
            tk.Entry(content_frame, textvariable=song_path_var, width=50).pack(pady=5)

            # Upload button
            tk.Button(content_frame, text="Upload Song", command=lambda: self.upload_song_action(song_name_var, artist_name_var, song_path_var)).pack(pady=15)

            return frame

        except Exception as e:
            print(f"Error in create_add_song_screen: {e}")
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

            print("Song Name:", song_name)
            print("Artist Name:", artist_name)
            print("Song File Path:", song_path)

            msg = self.client.upload_song(song_name, artist_name, song_path)
            print(msg)
            if msg[0] == "F":
                messagebox.showerror("Error", msg[1])
            elif msg[0] == "T":
                messagebox.showinfo("Success", msg[1])

            if self.client.is_expired:
                messagebox.showerror("Error", "Token invalid or token has expired")
                self.logout()

        except Exception as e:
            print(f"Error in upload_song_action: {e}")
            messagebox.showerror("Error", f"Failed to upload song: {e}")

    def create_profile_screen(self):
        """
        Creates the profile screen frame displaying user info and liked songs.
        Includes navigation buttons on the left side.

        :return: The main tkinter Frame for the profile screen.
        """
        try:
            frame = tk.Frame(self.root, bg="white")

            # Add navigation buttons on the left
            self.add_navigation_buttons(frame, "profile")

            # Main content frame for profile details
            content_frame = tk.Frame(frame, bg="white")
            content_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

            # Title label
            tk.Label(content_frame, text="My Profile", font=("Arial", 20), bg="white").pack(anchor="w", pady=10)

            liked_frame = tk.Frame(content_frame, bg="white")
            liked_frame.pack(fill="x", pady=(10, 5))

            tk.Label(liked_frame, text="Liked Songs", font=("Arial", 16), bg="white").pack(side="left", padx=(0, 10))

            # Display liked songs with their artist
            for song in self.client.liked_song:
                for song_name, (artist, song_id) in self.client.song_id_dict.items():
                    if song_id == song:
                        song_row = tk.Frame(content_frame, bg="white")
                        song_row.pack(fill="x", pady=5)

                        tk.Label(song_row, text=song_name, bg="white", font=("Arial", 12), width=12, anchor="w").pack(side="left", padx=5)
                        tk.Label(song_row, text=artist, bg="white", font=("Arial", 12), width=12, anchor="w").pack(side="left", padx=5)

            return frame

        except Exception as e:
            print(f"Error in create_profile_screen: {e}")
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
            print(f"Error during logout: {e}")
            messagebox.showerror("Error", f"Logout failed: {e}")

    def closing(self):
        """
        Handles application closing:
        Sends a shutdown command to the client,
        calls client exit cleanup,
        and destroys the main window.
        """
        try:
            print("closing")
            self.client.gui_to_client_queue.put("shutdown")
            self.client.delete_files()
            self.client.exit()
        except Exception as e:
            print(f"Error during closing: {e}")
        finally:
            print("good bye")
            self.root.destroy()
















































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
        if self.client.q.prev_song_path != "":
            print(self.client.q.prev_song_path)
            self.client.gui_to_client_queue.put("prev")
            self.playing = True
            self.play_pause_button.config(text="⏹")


    def next_song(self):
        print("next song")
        if not self.client.q.my_queue.empty():
            self.playing = True
            self.play_pause_button.config(text="⏹")
            self.client.gui_to_client_queue.put("next")

        print(self.playing)

    def play_pause(self):
        print(self.playing)
        print(self.client.q.my_queue.empty())
        if not self.playing:
            if not (self.client.q.my_queue.empty() and self.client.p.current_file == ""):
                print(self.client.p.current_file)
                self.play_pause_button.config(text="⏹")
                if self.counter == 0:
                    self.client.gui_to_client_queue.put("play")
                else:
                    self.client.gui_to_client_queue.put("resume")

                self.counter = 1 + self.counter

                self.master.after(100, self.check_result_queue)  # המשך לבדוק כל 100ms

                self.playing = not self.playing

        elif self.playing:
            self.play_pause_button.config(text="▶")
            self.client.gui_to_client_queue.put("pause")

            self.playing = not self.playing



    def check_result_queue(self):
        try:
            result = self.client.client_to_gui_queue.get_nowait()
            print("Result from thread:", result)
            if result == "nothing to play":
                self.playing = False
                self.play_pause_button.config(text="▶")
                self.counter = 0
        except queue.Empty:
            self.master.after(100, self.check_result_queue)

    def start(self):
        """
        התחלת הלולאה של tkinter.
        """
        self.root.geometry("700x600")  # הגדרת גודל החלון
        self.root.mainloop()  # התחלת הלולאה של tkinter


if __name__ == "__main__":
    try:
        client1 = Client(IP, PORT)
        root1 = tk.Tk()
        app = UserInterface(root1, client1)  # �
        app.start()
    except Exception as error:
        print(error)

