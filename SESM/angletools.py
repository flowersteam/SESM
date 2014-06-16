import math
import numpy as np


def printaxis():
    '''
    Y
    |
    |___X
   /
  Z

    '''
    print ""
    print "    Y"
    print "    |"
    print "    |___X"
    print "   /"
    print "  Z"
    print ""


def plane3DNormalVector(A, O):
    '''
    vector OA is the normal vector with O on the plane
    '''
    r = np.array(XYZtuple_sub(A, O))
    norm = np.linalg.norm(r)
    r = r / norm
    a = r[0]
    b = r[1]
    c = r[2]
    d = - (a * O[0] + b * O[1] + c * O[2])

    return (a, b, c, d)


def plane3D3point(A, O, B):
    '''
    ax + by + cz + d = 0
    '''
    #first find OA and OB vectors
    U = XYZtuple_sub(A, O)
    V = XYZtuple_sub(B, O)

    r = np.cross(np.array(U), np.array(V))
    norm = np.linalg.norm(r)
    r = r / norm
    a = r[0]
    b = r[1]
    c = r[2]
    d = - (a * A[0] + b * A[1] + c * A[2])

    return (a, b, c, d)


def project3Dpointonplane(A, (a, b, c, d)):
    '''
    The closest point is along the normal to the plane. So define a point W that is offset from A along that normal.

    W = A - N*t
    Then solve for t that puts W in the plane:

    dot(W,N) + d = 0
    dot(A-N*t,N) + d = 0
    dot(A,N) - t*dot(N,N) = -d
    t = (dot(A,N)+d)/dot(N,N)
    Where dot((x1,y1,z1),(x2,y2,z2)) = x1*x2 + y1*y2 + z1*z2, scalar product

    W = A - N*t  W is the projected point, A is the current point, N is the normal vector, and t is the variable we are looking for
    '''
    A = np.array(A)
    N = np.array([a, b, c])

    t = (np.inner(A, N) + d) / np.linalg.norm(N)
    W = A - N * t
    return (W[0], W[1], W[2])


def XYZtuple_sub(A, B):
    '''
    This function substract X,Y,Z as A-B (xA-xB, ...
    '''
    return (A[0] - B[0], A[1] - B[1], A[2] - B[2])


def rotate2D(A, rad):
    x = A[0] * math.cos(rad) - A[1] * math.sin(rad)
    y = A[1] * math.cos(rad) + A[0] * math.sin(rad)
    return (x, y)


def angle2D2point(A, B):
    '''
    angle between Origin-A vector and Origin-B vector
    think we are rotating all poin that the OA vector get aligned with the O-positiveX.
The outputed angle is the classic sogned one that you see on the cos sin table in radian. well it's all classic geometry.
    '''
    OAtoOXangle = math.atan2(A[1], A[0])
    B = rotate2D(B, -OAtoOXangle)

    return math.atan2(B[1], B[0])


def findAnyPerpendicularVectorToVector(V):
    V = np.array(V)
    #find smallest direction
    smallest = np.argmin(np.abs(V))
    cardinal = np.array([0, 0, 0])
    cardinal[smallest] = 1
    #compute the cross_product V and this cardinal
    U = np.cross(V, cardinal)
    norm = np.linalg.norm(U)
    U = U / norm
    return U


def find2OrthoNormalVectorInPlane((a, b, c, d)):
    #be carefull when using this function
    #you should see the output as correctly oriented ex and ey where ez is the plan normal vector

    N = (a, b, c)
    Y = findAnyPerpendicularVectorToVector(N)

    X = np.cross(Y, N)
    norm = np.linalg.norm(X)
    X = X / norm

    return X, Y


def decomposePointOnVector(P, VList):
    W = []
    for V in VList:
        W.append(np.inner(P, V))

    return W


def findAngle33DPointOnPlane(A, O, B, (a, b, c, d)):
    X, Y = find2OrthoNormalVectorInPlane((a, b, c, d))

    Ap = project3Dpointonplane(A, (a, b, c, d))
    Op = project3Dpointonplane(O, (a, b, c, d))
    Bp = project3Dpointonplane(B, (a, b, c, d))

    Adc = tuple(decomposePointOnVector(Ap, [X, Y]))
    Odc = tuple(decomposePointOnVector(Op, [X, Y]))
    Bdc = tuple(decomposePointOnVector(Bp, [X, Y]))

    U = (Adc[0] - Odc[0], Adc[1] - Odc[1])
    V = (Bdc[0] - Odc[0], Bdc[1] - Odc[1])

    return angle2D2point(U, V)


if __name__ == '__main__':
    printaxis()
    A = (0., 0., 1.)
    O = (0., 0., 0.5)
    B = (1., 0., 0.5)

    print plane3DNormalVector((0, 1, 0), (0, 0, 0))

    (a, b, c, d) = plane3D3point((0, 0, 1), (0, 0, 0), (1, 0, 0))
    print (a, b, c, d)

    print project3Dpointonplane(XYZtuple_sub(A, O), (a, b, c, d))
    print project3Dpointonplane(XYZtuple_sub(B, O), (a, b, c, d))

    print angle2D2point((1, 0), (-1, -1))

    print findAnyPerpendicularVectorToVector((1, 0, 0))

    print find2OrthoNormalVectorInPlane((a, b, c, d))

    print decomposePointOnVector((0, 1, 1), [(1, 0, 0), (0, 1, 1), (0, 0, 1)])

    print angle2D2point((0, 1), (1, 1))
    print findAngle33DPointOnPlane((1, 2, 10), (1, 1, 0), (3, 3, 0.5), (0, 0, 1, 0))
