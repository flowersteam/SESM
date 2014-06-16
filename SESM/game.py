import numpy as np
import numpy

import pygame

from collections import deque

def random_color():
    import random
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


# Normalization method, so the colors are in the range [0, 1]
def normalize(color):
    return color[0] / 255.0, color[1] / 255.0, color[2] / 255.0


# Reformats a color tuple, that uses the range [0, 1] to a 0xFF representation.
def reformat(color):
    return (int(round(color[0] * 255)),
            int(round(color[1] * 255)),
            int(round(color[2] * 255)))


def norm(vector):
    return np.sqrt(np.sum(np.power(vector, 2)))


def valid_to_plot(value):
    if type(value) == list:
        return list(np.array(np.ceil(value), 'int'))
    return int(np.ceil(value))


def valid_position(pos, w, h):
    x = min(max(pos[0], 0), w)
    y = min(max(pos[1], 0), h)
    return [x, y]


class Game(object):
    def __init__(self, kinect_feature, used_features, bg_color=None, image_filename=None, nid=None):
        self.kinect_feature = kinect_feature
        self.used_features = used_features
        self.target = []
        self.current_pos = []
        self.dmin = np.inf
        self.nid = nid
        
        self.distance = 1 # The distance belongs to [0, 1]
        self.normalized_current_pos = self.current_pos[:]
        self.normalized_target = self.target[:]
        
        self.bg = random_color() if not bg_color else bg_color
            
        self.image_filename = image_filename
        self.deque = deque([1] * 50, 50)


    def __repr__(self):
        return self.__class__.__name__

    def replay(self):
        self.deque = deque([1] * 50, 50)
        pass

    def has_succeeded(self):
        # called at 50Hz
        self.deque.append(self.distance)
        return numpy.mean(self.deque) < 0.05
        #return self.distance < 0.05

    def update(self):
        #if self.has_succeeded():
        #    self.replay()
        self.dmin = norm(np.array(self.current_pos) - np.array(self.target))
        l1, l2 = self.normalized_current_pos, self.normalized_target
        
        #self.distance = numpy.sum(np.abs(np.array(l1) - np.array(l2))) / (len(l1) if l1 else 1)
        if l1 is None or None in l1:
            return
            
        self.distance = norm(np.array(l1) - np.array(l2)) / numpy.sqrt(len(l1))
    
    def draw(self, surface):
        surface.fill(self.bg)


class TextGame(Game):
    def __init__(self, text, bg_color=(235, 236, 204)):
        self.text = text
        self.target = [1]
        self.current_pos = [0]
        self.dmin = np.inf
        if not bg_color:
            self.bg = random_color()
        else:
            self.bg = bg_color
                
        self.distance = 1
                
        self.normalized_current_pos = self.current_pos[:]
        self.normalized_target = self.target[:]

    def draw(self, surface):
        Game.draw(self, surface)

        w, h = surface.get_width(), surface.get_height()
        # pick a font you have and set its size
        font_size = w / 15
        myfont = pygame.font.SysFont("Comic Sans MS", font_size)
        # apply it to text on a label
        label = myfont.render(self.text, 1, (126, 129, 72))        
        textpos = label.get_rect()
        textpos.centerx = surface.get_rect().centerx
        textpos.centery = surface.get_rect().centery
        surface.blit(label, textpos)


class CircleGame(Game):
    def __init__(self, kinect_feature, used_features, bg_color=(173, 183, 172),
                 circle_color=(152, 155, 76), target_color=(189, 97, 56),
                 image_filename=None, nid=None):
        Game.__init__(self, kinect_feature, used_features, bg_color, image_filename, nid=nid)
        self.min_value = 0.1
        self.max_value = 1

        self.current_pos = self.min_value
        self.normalized_current_pos = [self.min_value]
        
        self.circle_color = circle_color
        self.target_color = target_color
        self.replay()

    def replay(self):
        Game.replay(self)
        self.normalized_target = [np.random.rand()]
        self.target = self.min_value + self.normalized_target[0] * (self.max_value - self.min_value)
        self.distance = 1

    # def has_succeeded(self):
    #     return norm(np.array([self.current_pos] - np.array([self.target]))) < 0.025

    def update(self):
        Game.update(self)

        features = self.kinect_feature.get_filtered_features()

        self.normalized_current_pos = [getattr(features, f) for f in self.used_features]

        if None not in self.normalized_current_pos:
            self.current_pos = self.min_value + self.normalized_current_pos[0] * (self.max_value - self.min_value)

    def draw(self, surface):
        Game.draw(self, surface)

        w, h = surface.get_width(), surface.get_height()
        #draw current elipse filled
        box = np.array([0.5 - (self.current_pos / 2.), 0.5 - (self.current_pos / 2.), self.current_pos, self.current_pos]) * w
        box = valid_to_plot(list(box))
        pygame.draw.ellipse(surface, self.circle_color, box)
        # draw goal ellipse not filled
        linewidth = int(0.01 * w)
        box = np.array([0.5 - (self.target / 2.), 0.5 - (self.target / 2.),
                        self.target, self.target]) * w
        box = valid_to_plot(list(box))
        pygame.draw.ellipse(surface, self.target_color, box, linewidth)



        
        


class EllipseGameCorrelated(Game):
    def __init__(self, kinect_feature, used_features, r_cor, bg_color=(0, 160, 176),
                 circle_color=(204, 51, 63), target_color=(106, 74, 60),
                 image_filename=None, nid=None):
        Game.__init__(self, kinect_feature, used_features, bg_color, image_filename, nid=nid)
        self.min_value = 0.1
        self.max_value = 1
        self.r_cor = r_cor  # r_cor is a tuple or a list of two element between -1 and 1
        self.current_pos = [self.min_value, self.min_value]
        self.normalized_current_pos = self.current_pos[:]
        self.circle_color = circle_color
        self.target_color = target_color
        self.replay()

    def __repr__(self):
        return self.__class__.__name__ + '_' + str(self.r_cor)

    def replay(self):
        Game.replay(self)
        self.distance = 1
        self.normalized_target = [np.random.rand(), np.random.rand()]

        target_a = self.min_value + self.normalized_target[0] * (self.max_value - self.min_value)
        target_b = self.min_value + self.normalized_target[1] * (self.max_value - self.min_value)
        #apply correlation
        tmp_add_b = target_a * self.r_cor[0]
        tmp_add_a = target_b * self.r_cor[1]
        target_a += tmp_add_a
        target_b += tmp_add_b
        target_a = max(min(target_a, self.max_value), self.min_value)
        target_b = max(min(target_b, self.max_value), self.min_value)
        self.target = [target_a, target_b]

    # def has_succeeded(self):
    #     return self.dmin < 0.025

    def update(self):
        Game.update(self)

        features = self.kinect_feature.get_filtered_features()

        self.normalized_current_pos = [getattr(features, f) for f in self.used_features]

        if None not in self.normalized_current_pos:
            a = self.min_value + self.normalized_current_pos[0] * (self.max_value - self.min_value)
            b = self.min_value + self.normalized_current_pos[1] * (self.max_value - self.min_value)
            #apply correlation
            tmp_add_b = a * self.r_cor[0]
            tmp_add_a = b * self.r_cor[1]
            a += tmp_add_a
            b += tmp_add_b
            a = max(min(a, self.max_value), self.min_value)
            b = max(min(b, self.max_value), self.min_value)
            self.current_pos = [a, b]

    def draw(self, surface):
        Game.draw(self, surface)

        w, h = surface.get_width(), surface.get_height()
        #draw current elipse filled
        box = np.array([0.5 - (self.current_pos[0] / 2.), 0.5 - (self.current_pos[1] / 2.), self.current_pos[0], self.current_pos[1]]) * w
        box = valid_to_plot(list(box))
        pygame.draw.ellipse(surface, self.circle_color, box)
        # draw goal ellipse not filled
        linewidth = int(0.01 * w)
        box = np.array([0.5 - (self.target[0] / 2.), 0.5 - (self.target[1] / 2.), self.target[0], self.target[1]]) * w
        box = valid_to_plot(list(box))
        pygame.draw.ellipse(surface, self.target_color, box, linewidth)
        


class EllipseGameCorrelatedBorder(Game):
    def __init__(self, kinect_feature, used_features, r_cor, bg_color=(0, 160, 176),
                 circle_color=(204, 51, 63), target_color=(106, 74, 60),
                 image_filename=None, nid=None):
        Game.__init__(self, kinect_feature, used_features, bg_color, image_filename, nid=nid)
        self.min_value = 0.1
        self.max_value = 1
        self.r_cor = r_cor  # r_cor is a tuple or a list of two element between -1 and 1

        self.min_linewidth = 0.02
        self.max_linewidth = 0.2
        self.linewidth = self.min_linewidth

        self.circle_color = circle_color
        self.target_color = target_color

        self.current_pos = [self.min_value, self.min_value, self.min_linewidth]
        self.normalized_current_pos = [self.min_value, self.min_value, self.min_linewidth]

        self.replay()

    def replay(self):
        Game.replay(self)
        import random # pour le lol (mdr)
        self.distance = 1
        
        self.normalized_target = [np.random.rand(), numpy.random.rand(), random.random()]
        
        target_a = self.min_value + self.normalized_target[0] * (self.max_value - self.min_value)
        target_b = self.min_value + self.normalized_target[1] * (self.max_value - self.min_value)
        target_linewidth = (self.min_linewidth + self.normalized_target[2] * (self.max_linewidth - self.min_linewidth))
        #apply correlation
        tmp_add_b = target_a * self.r_cor[0]
        tmp_add_a = target_b * self.r_cor[1]
        target_a += tmp_add_a
        target_b += tmp_add_b
        target_a = max(min(target_a, self.max_value), self.min_value)
        target_b = max(min(target_b, self.max_value), self.min_value)
        #correct linewidth
        target_linewidth = min(min(target_linewidth, target_a / 2. - 0.01), target_b / 2. - 0.01)
        self.target = [target_a, target_b, target_linewidth]

    # def has_succeeded(self):
    #     b1 = norm(np.array([self.current_pos[0], self.current_pos[1]] - np.array([self.target[0], self.target[1]]))) < 0.025
    #     b2 = norm(np.array([self.current_pos[2]] - np.array([self.target[2]]))) < 0.002
    #     return b1 and b2

    def update(self):
        Game.update(self)
        #b1 = norm(np.array([self.current_pos[0], self.current_pos[1]] - np.array([self.target[0], self.target[1]])))
        #b2 = norm(np.array([self.current_pos[2]] - np.array([self.target[2]])))
        #self.dmin = b1 + b2

        features = self.kinect_feature.get_filtered_features()

        self.normalized_current_pos = [getattr(features, f) for f in self.used_features]


        if None not in self.normalized_current_pos:
            a = self.min_value + self.normalized_current_pos[0] * (self.max_value - self.min_value)
            b = self.min_value + self.normalized_current_pos[1] * (self.max_value - self.min_value)
            linewidth = self.min_linewidth + self.normalized_current_pos[2] * (self.max_linewidth - self.min_linewidth)
            #apply correlation
            tmp_add_b = a * self.r_cor[0]
            tmp_add_a = b * self.r_cor[1]
            a += tmp_add_a
            b += tmp_add_b
            a = max(min(a, self.max_value), self.min_value)
            b = max(min(b, self.max_value), self.min_value)
            #correct linewidth
            linewidth = min(min(linewidth, a / 2. - 0.01), b / 2. - 0.01)
            self.current_pos = [a, b, linewidth]

    def draw(self, surface):
        Game.draw(self, surface)

        w, h = surface.get_width(), surface.get_height()
        # draw goal ellipse not filled
        box = np.array([0.5 - (self.target[0] / 2.), 0.5 - (self.target[1] / 2.), self.target[0], self.target[1]]) * w
        box = valid_to_plot(list(box))
        linewidth = int(self.target[2] * w)
        #print linewidth, box[2], box[3]
        pygame.draw.ellipse(surface, self.target_color, box, linewidth)
        #draw current elipse filled
        box = np.array([0.5 - (self.current_pos[0] / 2.), 0.5 - (self.current_pos[1] / 2.), self.current_pos[0], self.current_pos[1]]) * w
        box = valid_to_plot(list(box))
        linewidth = int(self.current_pos[2] * w)
        #print linewidth, box[2], box[3]
        pygame.draw.ellipse(surface, self.circle_color, box, linewidth)


