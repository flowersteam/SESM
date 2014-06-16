import zmq
import numpy
import threading

from collections import namedtuple

Point2D = namedtuple('Point2D', ('x', 'y'))
Point3D = namedtuple('Point3D', ('x', 'y', 'z'))
Quaternion = namedtuple('Quaternion', ('x', 'y', 'z', 'w'))

torso_joints = ('hip_center', 'spine', 'shoulder_center', 'head')
left_arm_joints = ('shoulder_left', 'elbow_left', 'wrist_left', 'hand_left')
right_arm_joints = ('shoulder_right', 'elbow_right', 'wrist_right', 'hand_right')
left_leg_joints = ('hip_left', 'knee_left', 'ankle_left', 'foot_left')
right_leg_joints = ('hip_right', 'knee_right', 'ankle_right', 'foot_right')
skeleton_joints = torso_joints + left_arm_joints + right_arm_joints + left_leg_joints + right_leg_joints


class Skeleton(namedtuple('Skeleton', ('timestamp', 'user_id') + skeleton_joints)):
    joints = skeleton_joints

    @property
    def to_np(self):
        l = []
        
        for j in self.joints:
            p = getattr(self, j).position
            l.append((p.x, p.y, p.z))
            
        return numpy.array(l)
            
Joint = namedtuple('Joint', ('position', 'orientation', 'pixel_coordinate'))


class KinectSensor(object):
    def __init__(self, addr, port):
        self._lock = threading.Lock()
        self._skeleton = None

        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect('tcp://{}:{}'.format(addr, port))

        t = threading.Thread(target=self.get_skeleton)
        t.daemon = True
        t.start()

    @property
    def tracked_skeleton(self):
        with self._lock:
            return self._skeleton

    @tracked_skeleton.setter
    def tracked_skeleton(self, skeleton):
        with self._lock:
            self._skeleton = skeleton

    def get_skeleton(self):
        while True:
            self.socket.send('Hello')

            md = self.socket.recv_json()
            msg = self.socket.recv()

            skeleton_array = numpy.frombuffer(buffer(msg), dtype=md['dtype'])
            skeleton_array = skeleton_array.reshape(md['shape'])

            joints = []
            for i in range(len(skeleton_joints)):
                x, y, z, w = skeleton_array[i][0:4]
                position = Point3D(x / w, y / w, z / w)
                pixel_coord = Point2D(*skeleton_array[i][4:6])
                orientation = Quaternion(*skeleton_array[i][6:10])
                joints.append(Joint(position, orientation, pixel_coord))

            self.tracked_skeleton = Skeleton(md['timestamp'], md['user_index'], *joints)


def draw_position(skel, ax):
    xy, zy = [], []

    if not skel:
        return

    for j in skeleton_joints:
        p = getattr(skel, j).position
        xy.append((p.x, p.y))
        zy.append((p.z, p.y))

    ax.set_xlim(-2, 5)
    ax.set_ylim(-1.5, 1.5)
    ax.scatter(zip(*xy)[0], zip(*xy)[1], 30, 'b')
    ax.scatter(zip(*zy)[0], zip(*zy)[1], 30, 'r')


if __name__ == '__main__':
    import time

    import matplotlib.pyplot as plt
    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111)

    kinect_sensor = KinectSensor('193.50.110.210', 9999)

    import skelangle

    kinect_angle = skelangle.AngleFromSkel()

    try:
        while True:
            ax.clear()
            draw_position(kinect_sensor.tracked_skeleton, ax)
            plt.draw()
            time.sleep(0.1)
    except KeyboardInterrupt:
        plt.close('all')
