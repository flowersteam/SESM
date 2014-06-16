import numpy
import Queue
import time
import zmq

from pykinect import nui
from pykinect.nui import JointId


class KinectServer(object):
    def __init__(self, addr, port):
        context = zmq.Context()

        self.socket = context.socket(zmq.REP)
        self.socket.bind('tcp://{}:{}'.format(addr, port))

        self.msg = Queue.Queue(5)

        self.kinect = nui.Runtime()

        self.kinect.skeleton_frame_ready += self.skeleton_frame_ready
        self.kinect.skeleton_engine.enabled = True

        self.seen_id = []

    def serve_forever(self):
        print 'Server started, waiting for connection...'

        while True:
            self.socket.recv()
            msg = self.msg.get()

            if not self.seen_id.count(msg[0]):
                self.seen_id.append(msg[0])

            self.send_skeleton(msg[0], msg[1])


    def send_skeleton(self, user_index, skeleton_array, flags=0, copy=True, track=False):
        md = dict(
            user_index=user_index,
            timestamp=time.time(),
            dtype=str(skeleton_array.dtype),
            shape=skeleton_array.shape)

        self.socket.send_json(md, flags | zmq.SNDMORE)
        return self.socket.send(skeleton_array, flags, copy=copy, track=track)

    def skeleton_frame_ready(self, frame):
        #self.msg.queue.clear()
        for data in frame.SkeletonData:
            pos = numpy.zeros((JointId.Count, 6))

            for i in range(JointId.Count):
                p = data.SkeletonPositions[i]
                pos[i][0:4] = (p.x, p.y, p.z, p.w)
                pos[i][4:6] = nui.SkeletonEngine.skeleton_to_depth_image(p)

            rot_data = data.calculate_bone_orientations()

            rot = numpy.zeros((JointId.Count, 4))
            for i in range(JointId.Count):
                q = rot_data[i].hierarchical_rotation.rotation_quaternion
                rot[i] = [q.x, q.y, q.z, q.w]

            skeleton_array = numpy.concatenate((pos.T, rot.T)).T

            if not numpy.sum(numpy.isnan(skeleton_array)) == 0:
                print skeleton_array

            if (not (numpy.all(skeleton_array[:, 0:9] == 0) and numpy.all(skeleton_array[:, 9] == 1)) and
                    numpy.sum(numpy.isnan(skeleton_array)) == 0):
                self.msg.put(('{}'.format(data.dwUserIndex), skeleton_array.copy()))


if __name__ == '__main__':
    import socket
    ip = socket.gethostbyname(socket.gethostname())
    port = 9999

    print 'serving on', ip, ':', port
    kinect_server = KinectServer(ip, port)
    kinect_server.serve_forever()
