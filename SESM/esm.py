import time
import pygame

import scene
import core

class ESMScene(scene.Scene):
    def run(self):
        running = True
        clock = pygame.time.Clock()

        self.start_goal = time.time()
        total_time = time.time()

        self.games_manager.realswitch_game(0)

        while running:
            for event in pygame.event.get():
                if event.type == pygame.locals.QUIT or \
                                (event.type == pygame.locals.KEYDOWN and event.key == pygame.locals.K_ESCAPE):
                    running = False

            if self.games_manager.current_game.has_succeeded():
                self.games_manager.replay(succeed=True)
                self.start_goal = time.time()

            if (time.time() - self.start_goal) > core.MAX_TIME_PER_GOAL:
                self.games_manager.replay(succeed=False)
                self.start_goal = time.time()

            if self.games_manager.should_stop:
                running = False

            if (time.time() - total_time) > core.GAME_TIME:
                running = False

            self.games_manager.update()
            self.games_manager.draw()

            clock.tick(50)

        self.games_manager.save_rest()
        self.games_manager.realswitch_game(0)