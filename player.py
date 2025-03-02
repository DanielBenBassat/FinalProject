import pygame
import queue
import threading
from time import sleep


class MusicPlayer:
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

        while self.is_playing:
         #   if self.is_paused:
          #     while self.is_paused:
           #         sleep(0.1)
            #    pygame.mixer.music.unpause()  # המשך הניגון

            if not pygame.mixer.get_busy():  # Check if the song is over
                self.is_playing = False
                #self.is_paused = False  # Reset is_paused when song ends
                break

            sleep(0.1)


            #self.play_thread = threading.Thread(target=play)
            #self.play_thread.start()

    def stop_song(self):
        """
        עוצר את השיר שמתנגן
        """
        if self.is_playing:
            pygame.mixer.music.stop()  # מפסיק את הניגון
            self.is_playing = False
            self.song = None

    def pause_song(self):
        """
        משהה את השיר שמתנגן
        """
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True

    def resume_song(self):
        """
        ממשיך לנגן את השיר מהנקודה שהופסק
        """
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False

    def forward(self, seconds=10):
        """
        מעביר את השיר קדימה בכמה שניות
        """
        if self.is_playing:
            # דילוג קדימה
            current_time = pygame.mixer.music.get_pos() / 1000  # הזמן הנוכחי בשניות
            new_time = current_time + seconds
            pygame.mixer.music.set_pos(new_time)

    def backward(self, seconds=10):
        """
        מחזיר את השיר אחורה בכמה שניות
        """
        if self.is_playing:
            # דילוג אחורה
            current_time = pygame.mixer.music.get_pos() / 1000  # הזמן הנוכחי בשניות
            new_time = max(0, current_time - seconds)  # מוודא שלא נעבור את תחילת השיר
            pygame.mixer.music.set_pos(new_time)
