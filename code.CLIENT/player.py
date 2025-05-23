import pygame
from time import sleep


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
        except pygame.error as e:
            print(f"Failed to initialize mixer: {e}")

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
            print(f"🎵 Playing: {file_path}")

            sleep(1)
            while self.is_playing:
                if not pygame.mixer.music.get_busy() and not self.is_paused:
                    self.is_playing = False
                    self.is_paused = False
                    self.current_file = ""
                    print("Playback finished")
                    try:
                        pygame.mixer.music.unload()  # Available in some pygame versions
                    except AttributeError:
                        pass
                    break

                if not cmd_queue.empty():
                    print("Received new command, stopping playback")
                    try:
                        pygame.mixer.music.unload()
                    except AttributeError:
                        pass
                    break

                pygame.time.Clock().tick(30)

            print("⏹️ Song ended.")

        except pygame.error as e:
            print(f"Error playing song '{file_path}': {e}")

    def stop_song(self):
        """
        Stops the currently playing song completely.
        """
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.current_file = ""
            print("⏹️ Song stopped.")
        except pygame.error as e:
            print(f"Error stopping song: {e}")

    def pause_song(self):
        """
        Pauses the currently playing song.
        """
        try:
            if self.is_playing and not self.is_paused:
                pygame.mixer.music.pause()
                self.is_paused = True
                print("⏸️ Song paused.")
                print(f"is_paused: {self.is_paused}")
        except pygame.error as e:
            print(f"Error pausing song: {e}")

    def resume_song(self):
        """
        Resumes playback of a paused song.
        """
        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                print("▶️ Playback resumed.")
        except pygame.error as e:
            print(f"Error resuming song: {e}")

    def shutdown(self):
        """
        Stops playback, releases resources, and shuts down the mixer.
        """
        try:
            if self.is_playing or self.is_paused:
                pygame.mixer.music.stop()
                print("⏹️ Song stopped.")
            pygame.mixer.quit()
            self.is_playing = False
            self.is_paused = False
            self.current_file = None
            print("🎧 Player shut down and resources cleaned up.")
        except pygame.error as e:
            print(f"Error during shutdown: {e}")

