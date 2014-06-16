import numpy as np
import threading
import time

import angletools

from collections import namedtuple
from collections import deque

features = ('roll_shoulder_right', 'pitch_shoulder_right', 'roll_elbow_right', 'roll_shoulder_left', 'pitch_shoulder_left', 'roll_elbow_left', 'right_hand_x', 'right_hand_y', 'left_hand_x', 'left_hand_y', 'body_x', 'body_z', 'mean_hand_x', 'mean_hand_y', 'mean_hand_z', 'roll_leg_right', 'roll_leg_left')


class Features(namedtuple('a', features)):
    pass


def Point3D_to_tuple(p3d):
    return (p3d.x, p3d.y, p3d.z)


class KinectFeature(threading.Thread):
    def __init__(self, kinect, freq=20, filter_size=5):
        threading.Thread.__init__(self)
        self.daemon = True
        self.kinect = kinect
        self.period = 1. / freq

        self.deque_features = namedtuple('Features', features)
        for fieldname in self.deque_features._fields:
            setattr(self.deque_features, fieldname, deque([None] * filter_size, filter_size))

    def get_features(self):
        skel = self.kinect.tracked_skeleton
        if skel:
            features_values = []
            for fieldname in features:
                function_to_call = getattr(self, 'compute_{}'.format(fieldname))
                features_values.append(function_to_call(skel))
            return Features(*features_values)

    def get_filtered_features(self):
        features_values = []
        for fieldname in features:
            feature_deque = getattr(self.deque_features, fieldname)
            data = np.array(list(feature_deque))
            valid_id = np.not_equal(None, data)
            if np.sum(valid_id):
                features_values.append(np.mean(data[valid_id]))
            else:
                features_values.append(None)

        return Features(*features_values)

    def run(self):
        while True:
            start = time.time()

            f = self.get_features()
            #append features values to filter
            for fieldname in features:
                feature_deque = getattr(self.deque_features, fieldname)
                if f:
                    value = getattr(f, fieldname)
                    if value is None or np.isnan(value):
                        feature_deque.append(None)
                    else:
                        feature_deque.append(value)
                else:
                    feature_deque.append(None)

            elapsed = time.time() - start
            pause = self.period - elapsed
            if pause > 0:
                time.sleep(pause)
            else:
                print '[KinectFeatures] thread loop out of time: {}'.format(pause)

    def compute_roll_shoulder_right(self, skel):
        if skel:
            O = Point3D_to_tuple(skel.spine.position)
            A = Point3D_to_tuple(skel.shoulder_left.position)
            B = Point3D_to_tuple(skel.shoulder_right.position)
            plane = angletools.plane3D3point(A, O, B)

            O = Point3D_to_tuple(skel.shoulder_right.position)
            A = Point3D_to_tuple(skel.hip_right.position)
            B = Point3D_to_tuple(skel.elbow_right.position)
            angle = angletools.findAngle33DPointOnPlane(A, O, B, plane)

            return (min(max(-angle, 0.5), 2) - 0.5) / 1.5  # normalize between [0 1]

    def compute_roll_shoulder_left(self, skel):
        if skel:
            O = Point3D_to_tuple(skel.spine.position)
            A = Point3D_to_tuple(skel.shoulder_right.position)
            B = Point3D_to_tuple(skel.shoulder_left.position)
            plane = angletools.plane3D3point(A, O, B)

            O = Point3D_to_tuple(skel.shoulder_left.position)
            A = Point3D_to_tuple(skel.hip_left.position)
            B = Point3D_to_tuple(skel.elbow_left.position)
            angle = angletools.findAngle33DPointOnPlane(A, O, B, plane)

            return (min(max(-angle, 0.5), 2) - 0.5) / 1.5  # normalize between [0 1]

    def compute_pitch_shoulder_right(self, skel):
        if skel:
            O = Point3D_to_tuple(skel.shoulder_left.position)
            I = Point3D_to_tuple(skel.shoulder_right.position)
            plane = angletools.plane3DNormalVector(I, O)

            A = Point3D_to_tuple(skel.hip_right.position)
            O = Point3D_to_tuple(skel.shoulder_right.position)
            B = Point3D_to_tuple(skel.elbow_right.position)
            angle = angletools.findAngle33DPointOnPlane(A, O, B, plane)

            return min(max(angle, 0), 1.5) / 1.5

    def compute_pitch_shoulder_left(self, skel):
        if skel:
            O = Point3D_to_tuple(skel.shoulder_right.position)
            I = Point3D_to_tuple(skel.shoulder_left.position)
            plane = angletools.plane3DNormalVector(I, O)

            A = Point3D_to_tuple(skel.hip_left.position)
            O = Point3D_to_tuple(skel.shoulder_left.position)
            B = Point3D_to_tuple(skel.elbow_left.position)
            angle = angletools.findAngle33DPointOnPlane(A, O, B, plane)

            return min(max(-angle, 0), 1.5) / 1.5

    def compute_roll_elbow_right(self, skel):
        if skel:
            O = Point3D_to_tuple(skel.elbow_right.position)
            A = Point3D_to_tuple(skel.shoulder_right.position)
            B = Point3D_to_tuple(skel.wrist_right.position)
            plane = angletools.plane3D3point(A, O, B)
            angle = angletools.findAngle33DPointOnPlane(A, O, B, plane)
            angle = angle - np.pi

            return (min(max(-angle, 0.5), 2) - 0.5) / 1.5  # normalize between [0 1]

    def compute_roll_elbow_left(self, skel):
        if skel:
            O = Point3D_to_tuple(skel.elbow_left.position)
            A = Point3D_to_tuple(skel.shoulder_left.position)
            B = Point3D_to_tuple(skel.wrist_left.position)
            plane = angletools.plane3D3point(A, O, B)
            angle = angletools.findAngle33DPointOnPlane(A, O, B, plane)
            angle = angle - np.pi

            return (min(max(-angle, 0.5), 2) - 0.5) / 1.5  # normalize between [0 1]

    def compute_right_hand_x(self, skel):
        if skel:
            shoulder_left_pos = skel.shoulder_left.pixel_coordinate
            shoulder_right_pos = skel.shoulder_right.pixel_coordinate
            ref = np.abs(shoulder_left_pos.x - shoulder_right_pos.x)
            if ref:
                hand_right_pos = skel.hand_right.pixel_coordinate
                shoulder_center_pos = skel.shoulder_center.pixel_coordinate
                return np.abs(min(max((hand_right_pos.x - shoulder_center_pos.x) / ref, 0), 1.5) / 1.5)  # normalize between [0 1]

    def compute_right_hand_y(self, skel):
        if skel:
            shoulder_center_pos = skel.shoulder_center.pixel_coordinate
            spine_pos = skel.spine.pixel_coordinate
            ref = np.abs(shoulder_center_pos.y - spine_pos.y)
            if ref:
                hand_right_pos = skel.hand_right.pixel_coordinate
                shoulder_right_pos = skel.shoulder_right.pixel_coordinate
                return np.abs((min(max((hand_right_pos.y - shoulder_right_pos.y) / ref, -1), 1) - 1) / 2)  # normalize between [0 1]

    def compute_left_hand_x(self, skel):
        if skel:
            shoulder_left_pos = skel.shoulder_left.pixel_coordinate
            shoulder_right_pos = skel.shoulder_right.pixel_coordinate
            ref = np.abs(shoulder_left_pos.x - shoulder_right_pos.x)
            if ref:
                hand_left_pos = skel.hand_left.pixel_coordinate
                shoulder_center_pos = skel.shoulder_center.pixel_coordinate
                return np.abs(min(max((hand_left_pos.x - shoulder_center_pos.x) / ref, -1.5), 0) / 1.5)  # normalize between [0 1]

    def compute_left_hand_y(self, skel):
        if skel:
            shoulder_center_pos = skel.shoulder_center.pixel_coordinate
            spine_pos = skel.spine.pixel_coordinate
            ref = np.abs(shoulder_center_pos.y - spine_pos.y)
            if ref:
                hand_left_pos = skel.hand_left.pixel_coordinate
                shoulder_left_pos = skel.shoulder_left.pixel_coordinate
                return np.abs((min(max((hand_left_pos.y - shoulder_left_pos.y) / ref, -1), 1) - 1) / 2)  # normalize between [0 1]

    def compute_body_x(self, skel):
        if skel:
            spine_pos = skel.spine.pixel_coordinate
            return np.abs((min(max(spine_pos.x, 0.3), 0.7) - 0.3) / 0.4)  # normalize between [0 1]

    def compute_body_z(self, skel):
        if skel:
            return np.abs((min(max(skel.spine.position.z, 2.5), 3.5) - 2.5) / 1.)  # normalize between [0 1]

    def compute_mean_hand_x(self, skel):
        if skel:
            shoulder_left_pos = skel.shoulder_left.pixel_coordinate
            shoulder_right_pos = skel.shoulder_right.pixel_coordinate
            ref = np.abs(shoulder_left_pos.x - shoulder_right_pos.x)
            if ref:
                shoulder_center_pos = skel.shoulder_center.pixel_coordinate
                hand_left_pos = skel.hand_left.pixel_coordinate
                hand_right_pos = skel.hand_right.pixel_coordinate
                rel_hand_left_x = shoulder_center_pos.x - hand_left_pos.x
                rel_hand_right_x = shoulder_center_pos.x - hand_right_pos.x
                mean_hand_x = rel_hand_left_x + (rel_hand_right_x - rel_hand_left_x) / 2.
                return np.abs((min(max(mean_hand_x / ref, -1), 1) + 1) / 2)  # normalize between [0 1]

    def compute_mean_hand_y(self, skel):
        if skel:
            shoulder_center_pos = skel.shoulder_center.pixel_coordinate
            spine_pos = skel.spine.pixel_coordinate
            ref = np.abs(shoulder_center_pos.y - spine_pos.y)
            if ref:
                hand_left_pos = skel.hand_left.pixel_coordinate
                hand_right_pos = skel.hand_right.pixel_coordinate
                rel_hand_left_y = shoulder_center_pos.y - hand_left_pos.y
                rel_hand_right_y = shoulder_center_pos.y - hand_right_pos.y
                mean_hand_y = rel_hand_left_y + (rel_hand_right_y - rel_hand_left_y) / 2.
                return np.abs((min(max(mean_hand_y / ref, -1.), 0.5) + 1.) / 1.5)  # normalize between [0 1]

    def compute_mean_hand_z(self, skel):
        if skel:
            shoulder_center_pos = skel.shoulder_center.position

            hand_left_pos = skel.hand_left.position
            hand_right_pos = skel.hand_right.position
            rel_hand_left_z = hand_left_pos.z - shoulder_center_pos.z
            rel_hand_right_z = hand_right_pos.z - shoulder_center_pos.z
            mean_hand_z = rel_hand_left_z + (rel_hand_right_z - rel_hand_left_z) / 2.
            return np.abs((min(max(mean_hand_z, -0.4), -0.2) + 0.2) / 0.2)  # normalize between [0 1]

    def compute_roll_leg_right(self, skel):
        if skel:
            O = Point3D_to_tuple(skel.spine.position)
            A = Point3D_to_tuple(skel.shoulder_left.position)
            B = Point3D_to_tuple(skel.shoulder_right.position)
            plane = angletools.plane3D3point(A, O, B)

            O = Point3D_to_tuple(skel.hip_right.position)
            A = Point3D_to_tuple(skel.knee_right.position)
            B = Point3D_to_tuple(skel.shoulder_right.position)
            angle = angletools.findAngle33DPointOnPlane(A, O, B, plane)
            return np.abs((min(max(angle, -2.7), -2) + 2.7) / 0.7)  # normalize between [0 1]

    def compute_roll_leg_left(self, skel):
        if skel:
            O = Point3D_to_tuple(skel.spine.position)
            A = Point3D_to_tuple(skel.shoulder_left.position)
            B = Point3D_to_tuple(skel.shoulder_right.position)
            plane = angletools.plane3D3point(A, O, B)

            O = Point3D_to_tuple(skel.hip_left.position)
            A = Point3D_to_tuple(skel.knee_left.position)
            B = Point3D_to_tuple(skel.shoulder_left.position)
            angle = angletools.findAngle33DPointOnPlane(A, O, B, plane)
            return np.abs((min(max(-angle, -2.7), -2) + 2.7) / 0.7)  # normalize between [0 1]


def draw_values(dequevalues, ax):
    length = 0
    cnt = 0
    for fieldname in dequevalues._fields:
        data = list(getattr(dequevalues, fieldname))
        length = len(data)
        to_plot = np.array(data)
        is_valid = np.not_equal(None, to_plot)
        to_plot[is_valid] += cnt
        ax.plot(to_plot)
        cnt = cnt + 1
    ax.set_xlim([0, length])
    ax.set_ylim([0, cnt])


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    plt.ion()
    fig = plt.figure(figsize=(20, 8))
    ax = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    #import recorder
    #sensor = recorder.Player('elbow_right.rec')
    #sensor.start()

    import pykinect
    with open('kinect_ip.txt') as f:
        KINECT_IP = f.readline().strip()

    kinect = pykinect.KinectSensor(KINECT_IP, 9999)

    kinect_feature = KinectFeature(kinect, 20, 200)
    kinect_feature.start()

    try:
        while True:
            ax.clear()
            pykinect.draw_position(kinect.tracked_skeleton, ax)

            ax2.clear()
            draw_values(kinect_feature.deque_features, ax2)

            plt.draw()

            time.sleep(kinect_feature.period)

    except KeyboardInterrupt:
        kinect_feature.join()
        plt.close('all')
