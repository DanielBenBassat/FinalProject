import pygame
from time import sleep
import os
import logging


class MusicPlayer:
    def __init__(self):
        """
        Initializes the pygame mixer and sets up the player state.
        """
        try:
            pygame.mixer.init()
            self.is_playing = False
            self.is_paused = False
            self.current_file = ""

            self.LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
            self.LOG_LEVEL = logging.DEBUG
            self.LOG_DIR = 'log'
            self.LOG_FILE = os.path.join(self.LOG_DIR, 'player_class.log')
            self._setup_logging()
        except pygame.error as e:
            logging.debug(f"Failed to initialize mixer: {e}")

    def _setup_logging(self):
        try:
            if not os.path.isdir(self.LOG_DIR):
                os.makedirs(self.LOG_DIR)
            logging.basicConfig(format=self.LOG_FORMAT, filename=self.LOG_FILE, level=self.LOG_LEVEL)
        except Exception as e:
            print(f"Failed to setup logging: {e}")


    def play_song(self, file_path, cmd_queue):
        """
        Plays the specified song from the beginning.

        :param file_path: Path to the audio file to be played.
        :param cmd_queue: A queue to check for incoming commands (e.g., stop or change song).
        """
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.current_file = file_path
            self.is_playing = True
            self.is_paused = False
            logging.debug(f"🎵 Playing: {file_path}")

            sleep(1)
            while self.is_playing:
                if not pygame.mixer.music.get_busy() and not self.is_paused:
                    self.is_playing = False
                    self.is_paused = False
                    self.current_file = ""
                    logging.debug("Playback finished")
                    try:
                        pygame.mixer.music.unload()  # Available in some pygame versions
                    except AttributeError:
                        pass
                    break

                if not cmd_queue.empty():
                    logging.debug("Received new command, stopping playback")
                    break

                pygame.time.Clock().tick(30)

            logging.debug("⏹️ Song ended.")

        except pygame.error as e:
            logging.debug(f"Error playing song '{file_path}': {e}")

    def stop_song(self):
        """
        Stops the currently playing song completely.
        """
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.current_file = ""
            logging.debug("⏹️ Song stopped.")
        except pygame.error as e:
            logging.debug(f"Error stopping song: {e}")

    def pause_song(self):
        """
        Pauses the currently playing song.
        """
        try:
            if self.is_playing and not self.is_paused:
                pygame.mixer.music.pause()
                self.is_paused = True
                logging.debug("⏸️ Song paused.")
                logging.debug(f"is_paused: {self.is_paused}")
        except pygame.error as e:
            logging.debug(f"Error pausing song: {e}")

    def resume_song(self):
        """
        Resumes playback of a paused song.
        """
        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                logging.debug("▶️ Playback resumed.")
                logging.debug(f"After unpause: busy={pygame.mixer.music.get_busy()}")
        except pygame.error as e:
            logging.debug(f"Error resuming song: {e}")

    def shutdown(self):
        """
        Stops playback, releases resources, and shuts down the mixer.
        """
        try:
            if self.is_playing or self.is_paused:
                pygame.mixer.music.stop()
                logging.debug("⏹️ Song stopped.")
            pygame.mixer.quit()
            self.is_playing = False
            self.is_paused = False
            self.current_file = None
            logging.debug("🎧 Player shut down and resources cleaned up.")
        except pygame.error as e:
            logging.debug(f"Error during shutdown: {e}")