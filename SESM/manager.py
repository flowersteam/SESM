import pykinect
import numpy
import core

np = numpy

import time
import glob
import os

import pygame

from collections import deque
from game import TextGame


STAR_SIZE = 30
star = pygame.image.load("images/star.png")
star = pygame.transform.scale(star, (STAR_SIZE, STAR_SIZE))



def valid_to_plot(value):
    if type(value) == list:
        return list(np.array(np.ceil(value), 'int'))
    return int(np.ceil(value))


def valid_position(pos, w, h):
    x = min(max(pos[0], 0), w)
    y = min(max(pos[1], 0), h)
    return [x, y]



class SkeletonDrawer(object):
    def __init__(self, kinect):
        self.kinect = kinect

    def draw(self, surface, color=(250, 250, 250), radius=0.025):
        img = pygame.image.load('images/skel.png')
        surface.blit(img, (10, 25))

        skel = self.kinect.tracked_skeleton
        if not skel:
            return

        point = []
        for j in pykinect.skeleton_joints:
            p = getattr(skel, j).pixel_coordinate
            point.append([p.x, p.y])

        point = np.array(point)
        spine_idx = pykinect.skeleton_joints.index('spine')

        shift = 0.5 - point[spine_idx, :]
        shift[0] = 0
        point = point + shift

        p_min = np.min(point, 0)
        p_max = np.max(point, 0)
        scale = np.max([p_min[1], p_max[1]])
        point = point * 0.9 / scale

        w, h = surface.get_width(), surface.get_height()
        point[:, 0] = point[:, 0] * w
        point[:, 1] = point[:, 1] * h

        radius = valid_to_plot(radius * w)

        for p in point:
            pygame.draw.circle(surface, color, valid_to_plot(list(p)), radius)

class Timebar(object):
    def __init__(self):
        pass

    def draw(self, surface, score):
        w, h = surface.get_width(), surface.get_height()

        img = pygame.image.load('images/time.png')
        surface.blit(img, (0, 0))

        f = pygame.font.SysFont("Comic Sans MS", 28)
        label = f.render("Temps restant:", 1, (255, 255, 255))
        textpos = label.get_rect()
        textpos.x = 10
        textpos.centery = surface.get_rect().centery
        surface.blit(label, textpos)
        shift = textpos.x + textpos.width + 15

        star_rect = star.get_rect()
        for i in range(int(score / 5) + 1):
            j = i * (STAR_SIZE + 5)
            s = surface.subsurface(shift + j, (h - STAR_SIZE) / 2, STAR_SIZE, STAR_SIZE)
            s.blit(star, star_rect)


class Sidebar(object):
    def __init__(self):
        self.color = (200, 12, 49)
        self.max = 0

    def draw(self, surface, current, rt, n, name):
        h = 145
        pygame.draw.rect(surface, self.color, (90, 258 + (1 - n) * h , 57, n * h))

        f = pygame.font.SysFont("Comic Sans MS", 20)

        img = pygame.image.load('images/score.png')
        surface.blit(img, (55, 445))

        img = pygame.image.load('images/perf.png')
        surface.blit(img, (55, 215))

        img = pygame.image.load('images/thermo.png')
        surface.blit(img, (80, 255))

        img = pygame.image.load('images/temps.png')
        # surface.blit(img, (5, 15))


        label = f.render("Temps total", 1, (255, 255, 255))
        textpos = label.get_rect()
        textpos.centerx = surface.get_rect().centerx - 5
        textpos.y = 25
        # surface.blit(label, textpos)

        label = f.render("Performance", 1, (255, 255, 255))
        textpos = label.get_rect()
        textpos.centerx = surface.get_rect().centerx - 5
        textpos.y = 225
        surface.blit(label, textpos)

        label = f.render("Approche de", 1, (255, 255, 255))
        textpos = label.get_rect()
        textpos.centerx = surface.get_rect().centerx - 5
        textpos.y = 455
        surface.blit(label, textpos)
        label = f.render("l'objectif", 1, (255, 255, 255))
        textpos = label.get_rect()
        textpos.centerx = surface.get_rect().centerx - 5
        textpos.y = 480
        surface.blit(label, textpos)

        self.max = max(self.max, 1 - current)

        w, h = 80, 220
        pygame.draw.rect(surface, self.color, (90, 520 + current * h, w, h - current * h))
        pygame.draw.line(surface, self.color, (90, 520 + (1 - self.max) * h), (w+90, 520 + (1 - self.max) * h), 2)
        pygame.draw.rect(surface, (0, 0, 0), (90, 520, w, h), 3)

        f = pygame.font.SysFont("Comic Sans MS", 35)
        #label = f.render("{}".format(rt), 1, (255, 255, 255))
        label = f.render("{}".format(name), 1, (255, 255, 255))
        textpos = label.get_rect()
        textpos.centerx = surface.get_rect().centerx - 5
        textpos.y = 75
        surface.blit(label, textpos)


class Manager(object):
    def __init__(self, kinect, game_list, game2id, screen, log_folder):
        self.screen = screen

        self.kinect = kinect
        
        self.game2id = game2id

        self.games = list(game_list)
        self.current_id = 0

        width, height = self.screen.get_width(), self.screen.get_height()


        self.sidebar = Sidebar()
        sidebar_width = 0.17 * width
        self.sidebar_surface = screen.subsurface((width - sidebar_width, 0, sidebar_width, height))

        self.skeleton = SkeletonDrawer(kinect)
        skel_side = 0.2 * height
        shift = 0.1 * skel_side
        self.skeleton_surface = screen.subsurface((shift, height - (skel_side + shift), skel_side, skel_side))

        self.timebar = Timebar()
        timebar_height = 0.1 * height
        self.timebar_surface = screen.subsurface((shift, shift, width / 2, timebar_height))

        game_size = height - (shift + timebar_height + shift + shift)
        game_shift = shift + skel_side + shift + (width - (shift + skel_side + shift + game_size + shift + sidebar_width)) / 2
        self.game_surface = screen.subsurface((game_shift, shift + timebar_height + shift, game_size, game_size))

        self.base_log_folder = log_folder
        self.xp_log_folder = os.path.join(self.base_log_folder, '{}'.format('shit'))
        if not os.path.exists(self.xp_log_folder):
            os.makedirs(self.xp_log_folder)
        self.goal_log_folder = os.path.join(self.xp_log_folder, '{}'.format('shit'))
        if not os.path.exists(self.goal_log_folder):
            os.makedirs(self.goal_log_folder)
        
        dirs = glob.glob(os.path.join(self.base_log_folder, '[0-9]*'))
        ids = [int(os.path.basename(p)) for p in dirs]
        
        self.game_id = max(ids) if ids else 0
        self.goal_id = 1

        self.skels = []
        self.pos = []
        self.d = []
        
        self.end = False

        self.goal_elapsed_time = None
        self.nb_bons = deque([], )
        self.start = time.time()
        self.duration = core.GAME_TIME

        self.goal_achieved = []
        self.scene = None
        self.__i_up = 0

    @property
    def rt(self):
        return int(round((self.duration - (time.time() - self.start)) / 60))

    @property
    def name(self):

        name = ''

        if str(self.games[self.current_id]) == "EllipseGameCorrelated_[0, 0, 'pluto']":
            name = 'Violette'

        if str(self.games[self.current_id]) == "CircleGame":
            name = 'Chardon'

        if str(self.games[self.current_id]) == "EllipseGameCorrelated_[0, 0, 'donald']":
            name = 'Tournesol'

        if str(self.games[self.current_id]) == "EllipseGameCorrelated_[0, 0, 'mickey']":
            name = 'Bleuet'

        return name

    @property
    def current_game(self):

        return self.games[self.current_id]

    def save_rest(self):
        with open(os.path.join(self.xp_log_folder, 'end.txt'), 'w') as f:
            f.write('{}\n'.format(time.time()))

        a = numpy.array(self.skels)
        with open(os.path.join(self.goal_log_folder, 'skel.npy'), 'wb') as f:
            numpy.save(f, a)

        try:
            a = numpy.array(self.pos)
        except ValueError:
            a = numpy.array([])
            
        with open(os.path.join(self.goal_log_folder, 'pos.npy'), 'wb') as f:
            numpy.save(f, a)
    
        a = numpy.array(self.d)
        with open(os.path.join(self.goal_log_folder, 'dist.npy'), 'wb') as f:
            numpy.save(f, a)

        self.skels = []
        self.pos = []
        self.d = []
        
    def switch_game(self, i):
        self.next_gameid = i
        self.realswitch_game(i)


    def realswitch_game(self, i):
        self.goal_elapsed_time = time.time()
        if self.scene:
            self.scene.start_goal = time.time()

        self.goal_achieved = []

        if self.current_id != 0:
            self.save_rest()

            with open(os.path.join(self.goal_log_folder, 'succeed.txt'), 'w') as f:
                f.write('{}\n'.format(False))
                
            with open(os.path.join(self.goal_log_folder, 'end.txt'), 'w') as f:
                f.write('{}\n'.format(time.time()))

        self.current_id = i
        self.game_id += 1
        self.goal_id = 1

        self.xp_log_folder = os.path.join(self.base_log_folder, '{}'.format(self.game_id))
        os.makedirs(self.xp_log_folder)

        with open(os.path.join(self.xp_log_folder, 'type.txt'), 'w') as f:
            f.write('{}\n'.format(self.current_game))

        with open(os.path.join(self.xp_log_folder, 'start.txt'), 'w') as f:
            f.write('{}\n'.format(time.time()))

        self.goal_log_folder = os.path.join(self.xp_log_folder, '{}'.format(self.goal_id))
        os.makedirs(self.goal_log_folder)

        with open(os.path.join(self.goal_log_folder, 'start.txt'), 'w') as f:
            f.write('{}\n'.format(time.time()))

        with open(os.path.join(self.goal_log_folder, 'target.txt'), 'w') as f:
            f.write('{}\n'.format(self.current_game.target))

        self.current_game.replay()
        self.sidebar.max = 0
            
    @property
    def should_stop(self):
        return self.end
        
    @should_stop.setter
    def should_stop(self, value):
        self.end = value
            

    def get_subsurfaces(self):
        width, height = self.screen.get_width(), self.screen.get_height()

        subsurfaces = []
        for g in range(len(self.games)):
            if g == 0:
                delimiter = (0, 100, width, height-100)
            else:
                continue
            subsurfaces.append(self.screen.subsurface(delimiter))
        return subsurfaces

    def update(self):
        if self.__i_up % 5 == 0:
            self.skels.append(numpy.array(self.kinect.tracked_skeleton.to_np))
            self.pos.append(self.current_game.current_pos)
            self.d.append(self.current_game.dmin)
            self.__i_up = 0

        self.__i_up += 1
        
        self.current_game.update()

    def replay(self, succeed):
        self.goal_elapsed_time = time.time()

        sound = pygame.mixer.Sound('cool.wav' if succeed else 'nono.wav')
        sound.play()

        if succeed:
            self.goal_achieved.append(time.time())

        
        a = numpy.array(self.skels)
        with open(os.path.join(self.goal_log_folder, 'skel.npy'), 'wb') as f:
            numpy.save(f, a)

        try:
            a = numpy.array(self.pos)
        except ValueError:
            a = numpy.array([])
            
        with open(os.path.join(self.goal_log_folder, 'pos.npy'), 'wb') as f:
            numpy.save(f, a)
                
        a = numpy.array(self.d)
        with open(os.path.join(self.goal_log_folder, 'dist.npy'), 'wb') as f:
            numpy.save(f, a)

        self.skels = []
        self.pos = []
        self.d = []

        
            
        with open(os.path.join(self.goal_log_folder, 'succeed.txt'), 'w') as f:
            f.write('{}\n'.format(succeed))
                
        with open(os.path.join(self.goal_log_folder, 'end.txt'), 'w') as f:
            f.write('{}\n'.format(time.time()))
            
        self.goal_id += 1
        

        self.goal_log_folder = os.path.join(self.xp_log_folder, '{}'.format(self.goal_id))
        os.makedirs(self.goal_log_folder)
        
        with open(os.path.join(self.goal_log_folder, 'target.txt'), 'w') as f:
            f.write('{}\n'.format(self.current_game.target))

        with open(os.path.join(self.goal_log_folder, 'start.txt'), 'w') as f:
            f.write('{}\n'.format(time.time()))

        self.current_game.replay()
        self.sidebar.max = 0

    def draw_surface_contour(self, surface, color=(0, 0, 0)):
        w, h = surface.get_size()
        width = 2
        pygame.draw.line(surface, color, [0, 0], [0, h], width)
        pygame.draw.line(surface, color, [0, 0], [w, 0], width)
        pygame.draw.line(surface, color, [w, h], [w, 0], width)
        pygame.draw.line(surface, color, [w, h], [0, h], width)

    def draw(self):
        self.background = pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill(self.current_game.bg)

        self.screen.blit(self.background, (0, 0))

        if not isinstance(self.current_game, TextGame):
            ct = time.time()
            recent_goals = filter(lambda t: (ct - t) < core.PERF_WINDOW, self.goal_achieved)
            n = min(float(len(recent_goals)) / core.PERF_WEIGHT[self.current_game.nid], 1)
            # print len(recent_goals), core.PERF_WEIGHT[self.current_game.nid], n

            self.skeleton.draw(self.skeleton_surface)
            self.sidebar.draw(self.sidebar_surface, self.current_game.distance, self.rt, n, self.name)

            t = (time.time() - self.goal_elapsed_time) if self.goal_elapsed_time else 0
            self.timebar.draw(self.timebar_surface, (core.MAX_TIME_PER_GOAL - t))

            self.current_game.draw(self.game_surface)
        else:
            self.current_game.draw(self.screen)

        pygame.display.flip()

if __name__ == '__main__':
    import pygame
    import pygame.locals
    import recorder
    import skelfeature

    from game import CircleGame, EllipseGameCorrelated, EllipseGameCorrelatedBorder, TextGame

    kinect = recorder.Player('dummy.rec')
    kinect.start()

    kinect_feature = skelfeature.KinectFeature(kinect, 20, 3)
    kinect_feature.start()

    while kinect.tracked_skeleton is None:
        time.sleep(0.1)

    pygame.init()
    resolution = (1024, 768)
    screen = pygame.display.set_mode(resolution)

    games = []
    games.append(CircleGame(kinect_feature, ('mean_hand_x',), image_filename=os.path.join('images', 'circle.jpg'), nid=0))
    games.append(EllipseGameCorrelated(kinect_feature, ('roll_elbow_left', 'roll_elbow_right'), [0, 0, 'mickey'], image_filename=os.path.join('images', 'ellipse_1.jpg'), nid=1))
    games.append(EllipseGameCorrelated(kinect_feature, ('body_z', 'roll_shoulder_left'), [0, 0, 'donald'], (240, 168, 48), (94, 65, 47), (252, 235, 182), image_filename=os.path.join('images', 'ellipse_2.jpg'), nid=2))
    games.append(EllipseGameCorrelatedBorder(kinect_feature, ('roll_shoulder_left', 'roll_elbow_right', 'roll_leg_left'), [-0.2, 0.2], (46, 38, 51), (153, 23, 60), (239, 255, 205), image_filename=os.path.join('images', 'ellipse_border.jpg'), nid=3))
    # games.insert(0, TextGame('Choisissez un jeu.'))

    grid = [0]
    xp_folder = '/tmp/bob'
    games_manager = Manager(kinect, games, grid, screen, xp_folder)

    running = True
    clock = pygame.time.Clock()

    game_id = 0
    games_manager.realswitch_game(game_id)

    start_goal = time.time()
    start_game = time.time()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                running = False

        if games_manager.current_game.has_succeeded():
            games_manager.replay(succeed=True)
            start_goal = time.time()


        if (time.time() - start_goal) > core.MAX_TIME_PER_GOAL:
            games_manager.replay(succeed=False)
            start_goal = time.time()

        if games_manager.should_stop:
            running = False

        if (time.time() - start_game) > 100:
            game_id += 1

            if game_id >= len(games):
                running = False
                break

            games_manager.realswitch_game(game_id)
            start_game = time.time()

        games_manager.update()
        games_manager.draw()

        clock.tick(50)

    games_manager.realswitch_game(0)
