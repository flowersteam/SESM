import pylab as plt
import threading
import cPickle
import copy
import time


class Record(threading.Thread):
    def __init__(self, sensor):
        threading.Thread.__init__(self)
        self.sensor = sensor
        self.data = []

    def run(self):
        self.running = True

        while self.running:
            skel = self.sensor.tracked_skeleton
            self.data.append(copy.copy(skel))

            time.sleep(0.02)

    def save(self, name):
        self.running = False
        self.join()

        cPickle.dump(self.data, open(name, 'w'))


class Player(threading.Thread):
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.daemon = True

        self.data = cPickle.load(open(filename))
        self.skel = None

    def run(self):
        while True:
            i = 0
            while i < len(self.data) - 1:
                if self.data[i]:
                    self.t = self.data[i].timestamp
                    self.skel = copy.copy(self.data[i])
                    if self.data[i + 1]:
                        time.sleep(self.data[i + 1].timestamp - self.t)
                i = i + 1

    @property
    def tracked_skeleton(self):
        return self.skel


if __name__ == '__main__':
    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111)

    import pykinect

    #sensor = Player('elbow_right.rec')
    #sensor.start()

    sensor = pykinect.KinectSensor('193.50.110.131', 9999)
    record = Record(sensor)
    name = raw_input('Xp: ')
    record.start()


    try:
        while True:
            ax.clear()
            kinect.draw_position(sensor.tracked_skeleton, ax)
            plt.draw()
            time.sleep(0.1)
    except KeyboardInterrupt:
        record.save(name)
        plt.close('all')
