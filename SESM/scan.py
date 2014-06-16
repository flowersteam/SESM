import pygame
import time

import pygame.locals

import scene
import core


class ScanScene(scene.Scene):
    def run(self):
        running = True
        clock = pygame.time.Clock()

        game_id = 1
        self.games_manager.realswitch_game(game_id)

        start_goal = time.time()
        start_game = time.time()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.locals.QUIT:
                    running = False

            if self.games_manager.current_game.has_succeeded():
                self.games_manager.replay(succeed=True)
                start_goal = time.time()


            if (time.time() - start_goal) > core.MAX_TIME_PER_GOAL:
                self.games_manager.replay(succeed=False)
                start_goal = time.time()

            if self.games_manager.should_stop:
                running = False

            if (time.time() - start_game) > core.SCAN_TIME:
                game_id += 1

                if game_id > 4:
                    running = False
                    break

                self.games_manager.realswitch_game(game_id)
                start_game = time.time()

            self.games_manager.update()
            self.games_manager.draw()

            clock.tick(50)

        self.games_manager.realswitch_game(0)