import pygame
import queue
import threading
from time import sleep


class MusicPlayer2:
    def __init__(self):
        pygame.mixer.init()  # אתחול המיקסר של pygame
        self.is_playing = False
        self.is_paused = False
        self.song = None
        self.queue = queue.Queue()  # לנהל את ההודעות בין הטרדים
        self.play_thread = None  # ניהול ה-Thread של הניגון


    def play_song(self, file_path):
        """
        מקבל קובץ MP3 ומנגן אותו
        """
        self.song = pygame.mixer.Sound(file_path)
        self.song.play()
        self.is_playing = True
        self.is_paused = False  # Ensure is_paused starts as False
        sleep(1)
        while self.is_playing:
            if not pygame.mixer.get_busy():  # Check if the song is over
                self.is_playing = False
                break

            sleep(0.1)
    def stop_song(self):
        if self.is_playing and self.song:
            self.song.stop()
            print("stop song from player class")
            self.is_playing = False
            self.song = None

import pygame


class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.is_playing = False
        self.is_paused = False
        self.current_file = ""

    def play_song(self, file_path, stop_event):
        """
        מנגן את השיר מהתחלה.
        """
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        self.current_file = file_path
        self.is_playing = True
        self.is_paused = False
        print(f"🎵 מנגן: {file_path}")

        sleep(1)
        while self.is_playing:
            if not pygame.mixer.music.get_busy() and not self.is_paused:
                self.is_playing = False
                self.is_paused = False
                self.current_file = ""
                break
            if stop_event.is_set():
                break
            pygame.time.Clock().tick(30)


        print("⏹️ השיר הסתיים.")


    def stop_song(self):
        """
        עוצר את השיר לגמרי.
        """

        pygame.mixer.music.stop()
        self.is_playing = False
        #self.is_paused = False
        self.current_file= ""
        print("⏹️ השיר נעצר.")

    def pause_song(self):
        """
        משהה את השיר.
        """
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            print("⏸️ השיר הושהה.")
            print(self.is_paused)

    def resume_song(self):
        """
        ממשיך לנגן שיר ממצב של השהייה.
        """
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            print("▶️ המשך ניגון.")

    def shutdown(self):
        """
        עוצר את הניגון, משחרר קבצים, וסוגר את המיקסר.
            """
        if self.is_playing or self.is_paused:
            pygame.mixer.music.stop()
            print("⏹️ השיר נעצר.")
        pygame.mixer.quit()
        self.is_playing = False
        self.is_paused = False
        self.current_file = None
        print("🎧 הנגן נסגר וניקוי המשאבים הושלם.")

