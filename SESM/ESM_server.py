import os
import sys
import zmq
import glob
import time
import pygame
import socket
import random
import argparse

import manager
import recorder
import pykinect
import skelfeature

from PyQt4 import QtGui, uic

from webserver import HTTPServer
from game import CircleGame, EllipseGameCorrelated, EllipseGameCorrelatedBorder, TextGame
from scene import VideoScene, DummyScene
from test import TestScene
from scan import ScanScene
from esm import ESMScene

addr = socket.gethostbyname(socket.gethostname())
port = 9876
resolution = (1600, 900)
N = (4, 1)
LOG_FOLDER = 'logs'
log_path = os.path.join(os.getcwd(), LOG_FOLDER)


def get_game_grid():
    l = range(1, N[0] + 1) * N[1]
    random.shuffle(l)
    return l

def get_command(sock):
    cmd = sock.recv()
    sock.send('ack')
    return cmd


def cmd_to_scene(cmd):
    if cmd.startswith('videos'):
        return VideoScene, (cmd,)

    # else:
    #     return DummyScene, ()

    if cmd == 'scan':
        return ScanScene, ()

    if cmd == 'ESM':
        return ESMScene, ()

    if cmd == 'test':
        return TestScene, ()


def make_xp_folder(xp_id):
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    xp_log_path = os.path.join(log_path, str(xp_id))
    if not os.path.exists(xp_log_path):
        os.makedirs(xp_log_path)

    return xp_log_path


def remove_temp_data(n=100):
    for i in range(1, n):
        p = 'static/game_{}.jpg'.format(i)
        if os.path.exists(p):
            os.remove(p)


def save_time(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write('{}\n'.format(time.time()))


def get_xp_id():
    dirs = glob.glob(os.path.join(log_path, '[0-9]*'))
    ids = [int(os.path.basename(p)) for p in dirs]

    suggest_id = max(ids) + 1 if ids else 1

    class MyApp(QtGui.QApplication):
        def __init__(self, argv):
            QtGui.QApplication.__init__(self, argv)
            self.window = uic.loadUi('ESM.ui')

            self.window.id_spin.setValue(suggest_id)
            self.window.start_button.clicked.connect(self.on_click)

        def on_click(self):
            self.chosen_id = self.window.id_spin.value()

            if self.chosen_id in ids:
                ret = QtGui.QMessageBox.warning(self.window,
                                                'Attention', 'L\'id indique a deja ete utilise. Continuer ?',
                                                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
                if ret == QtGui.QMessageBox.Cancel:
                    return

            self.exit(0)

    app = MyApp(sys.argv)
    app.window.show()
    app.exec_()

    return app.chosen_id


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--without-kinect', action='store_true')
    parser.add_argument('--no-fullscreen', action='store_true')
    args = parser.parse_args()

    # TMP HACK
    args.no_fullscreen = False
    args.without_kinect = False
    # FIN TMP

    ###################################
    # Clean the previous session mess #
    ###################################

    remove_temp_data()

    ##################
    # Prepare the XP #
    ##################

    xp_id = get_xp_id()
    xp_folder = make_xp_folder(xp_id)

    xp_start = time.time()
    save_time(os.path.join(xp_folder, 'xp_start.txt'))


    ###################
    # Load the Kinect #
    ###################

    with open('kinect_ip.txt') as f:
        KINECT_IP = f.readline().strip()

    if args.without_kinect:
        kinect = recorder.Player('dummy.rec')
        kinect.start()

    else:
        kinect = pykinect.KinectSensor(KINECT_IP, 9999)

    kinect_feature = skelfeature.KinectFeature(kinect, 20, 3)
    kinect_feature.start()

    # yet another ugly hack: wait skeleton to be not None (Skeleton is set to None in the first place)
    print "Waiting to tracked first skeleton"
    while kinect.tracked_skeleton is None:
        time.sleep(0.1)
    print "First skeleton ok"


    ###################
    # Starting Pygame #
    ###################

    # pygame.init()

    # if args.no_fullscreen:
    #     screen = pygame.display.set_mode(resolution)
    # else:
    #     screen = pygame.display.set_mode(resolution, pygame.FULLSCREEN)

    # pygame.mouse.set_visible(False)


    #################################
    # Load the game and the manager #
    #################################

    games = []

    games.append(CircleGame(kinect_feature, ('mean_hand_x',), image_filename=os.path.join('images', 'circle.jpg'), nid=0))
    games.append(EllipseGameCorrelated(kinect_feature, ('roll_elbow_left', 'roll_elbow_right'), [0, 0, 'mickey'], image_filename=os.path.join('images', 'ellipse_1.jpg'), nid=1))
    games.append(EllipseGameCorrelated(kinect_feature, ('right_hand_x', 'roll_shoulder_left'), [0, 0, 'donald'], (240, 168, 48), (94, 65, 47), (252, 235, 182), image_filename=os.path.join('images', 'ellipse_2.jpg'), nid=2))
    # games.append(EllipseGameCorrelatedBorder(kinect_feature, ('roll_shoulder_left', 'roll_elbow_right', 'roll_leg_left'), [-0.2, 0.2], (46, 38, 51), (153, 23, 60), (239, 255, 205), image_filename=os.path.join('images', 'ellipse_border.jpg'), nid=3))
    # games.append(EllipseGameCorrelated(kinect_feature, ('roll_shoulder_left', 'roll_leg_right'), [0, 0, 'pluto'],  (46, 38, 51), (153, 23, 60), (239, 255, 205), image_filename=os.path.join('images', 'ellipse_border.jpg'), nid=3))
    games.append(EllipseGameCorrelated(kinect_feature, ('roll_shoulder_left', 'mean_hand_y'), [0, 0, 'pluto'],  (46, 38, 51), (153, 23, 60), (239, 255, 205), image_filename=os.path.join('images', 'ellipse_border.jpg'), nid=3))
    random.shuffle(games)

    games.insert(0, TextGame('Choisissez un jeu.'))
    games.append(TextGame('Remplissez le questionnaire.'))
    games.append(TextGame('Merci d\'avoir joue !'))

    grid = get_game_grid()
    print 'generated grid', grid
    # games_manager = manager.Manager(kinect, games, grid, screen, xp_folder)

    ###########################
    # Starting the zmq server #
    ###########################

    c = zmq.Context()
    s = c.socket(zmq.REP)
    s.bind('tcp://{}:{}'.format(addr, port))
    print 'Serving on {}:{}'.format(addr, port)

    #########################
    # Set up the web server #
    #########################

    server = HTTPServer(None, xp_id, host=KINECT_IP)
    server.start()

    ################################
    # Starting the scene sequences #
    ################################

    # background = pygame.Surface(screen.get_size())
    # background = background.convert()
    # background.fill((0, 0, 0))

    while True:
        cmd = get_command(s)

        if cmd == 'END':
            break

        scene_cls, scene_args = cmd_to_scene(cmd)

        if scene_cls == VideoScene:
            print 'quit pygame'
            pygame.quit()
            screen = None
            games_manager = None

        else:
            print 'start pygame'
            pygame.init()

            if args.no_fullscreen:
                screen = pygame.display.set_mode(resolution)
            else:
                screen = pygame.display.set_mode(resolution, pygame.FULLSCREEN)

            pygame.mouse.set_visible(False)

            games_manager = manager.Manager(kinect, games, grid, screen, xp_folder)
        server.manager = games_manager

        scene_args = [screen, games, games_manager] + list(scene_args)
        scene = scene_cls(*scene_args)
        games_manager.scene = scene

        print 'Starting scene', scene
        scene.start()
        scene.join()
        print 'Scene done'


        if scene_cls == VideoScene:
            pygame.init()

            if args.no_fullscreen:
                screen = pygame.display.set_mode(resolution)
            else:
                screen = pygame.display.set_mode(resolution, pygame.FULLSCREEN)

            pygame.mouse.set_visible(False)  

        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((0, 0, 0))

        screen.blit(background, (0, 0))
        pygame.display.flip()

    save_time(os.path.join(xp_folder, 'xp_end.txt'))
