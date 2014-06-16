import time
import threading
import subprocess
import pygame.locals

vlc_path = 'C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe'

class Scene(threading.Thread):
    def __init__(self, screen, games, games_manager):
        threading.Thread.__init__(self)

        self.screen = screen
        self.games = games
        self.games_manager = games_manager


class DummyScene(Scene):
    def run(self):
        time.sleep(5)


class VideoScene(Scene):
    def __init__(self, screen, games, games_manager, filename):
        Scene.__init__(self, screen, games, games_manager)

        self.filename = filename

    def run(self):
        subprocess.call([vlc_path, self.filename, '--play-and-exit', '--fullscreen'])#, shell=True)


if __name__ == '__main__':
    import pygame

    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((700, 800))

    s = VideoScene(screen, None, None, 'videos/p2.mpg')
    s.start()
    s.join()

