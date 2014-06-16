import sys
import zmq
import socket
from PyQt4 import QtGui, uic



ip = open("kinect_ip.txt","r")
ip = ip.read()
#ip = '192.168.0.100'

port = 9876

class MyApp(QtGui.QApplication):
    def __init__(self, argv):
        QtGui.QApplication.__init__(self, argv)
        self.window = uic.loadUi('client.ui')

        self.window.video1.clicked.connect(lambda: self.switch_video(1))
        self.window.video2.clicked.connect(lambda: self.switch_video(2))
        self.window.video3.clicked.connect(lambda: self.switch_video(3))
        self.window.video4.clicked.connect(lambda: self.switch_video(4))
        self.window.video5.clicked.connect(lambda: self.switch_video(5))
        self.window.video6.clicked.connect(lambda: self.switch_video(6))

        self.window.scan.clicked.connect(lambda: self.switch_scene('scan'))
        self.window.exploration.clicked.connect(lambda: self.switch_scene('ESM'))
        self.window.tests.clicked.connect(lambda: self.switch_scene('test'))
        self.window.end.clicked.connect(lambda: self.switch_scene('END'))

        c = zmq.Context()
        self.s = c.socket(zmq.REQ)
        self.s.connect('tcp://{}:{}'.format(ip, port))

    def switch_scene(self, name):
        print 'scene', name
        self.s.send(name)
        print self.s.recv()

    def switch_video(self, i):
        self.switch_scene('videos/p{}.mpg'.format(i))


if __name__ == '__main__':
    print 'trying to connect on', ip
    app = MyApp(sys.argv)
    app.window.show()
    app.exec_()

