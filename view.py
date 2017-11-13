# View class
# Written by Arthur Makumbi
# CS251

# import necessary packages
import numpy as np
import math


# create a class to manage the data
class View:
    # init method that calls the reset method to initialize default values
    def __init__(self):
        self.reset()

    # reset method called from init
    def reset(self):
        self.vrp = np.matrix([0.5, 0.5, 1])     # a NumPy matrix with the default value [0.5, 0.5, 1].
        self.vpn = np.matrix([0, 0, -1])        # a NumPy matrix with the default value [0, 0, -1].
        self.vup = np.matrix([0, 1, 0])         # a NumPy matrix with the default value [0, 1, 0].
        self.u = np.matrix([-1, 0, 0])          # a NumPy matrix with the default value [-1, 0, 0].
        self.extent = [1, 1, 1]                 # a list or NumPy matrix with the default value [1, 1, 1]
        self.screen = [350, 350]                # a list or NumPy matrix with the default value [400, 400]
        self.offset = [40, 40]                  # a list or NumPy matrix with the default value [20, 20]

    # uses the current viewing parameters to return a view matrix.
    def build(self):
        vtm = np.identity(4, float)

        # move the reference axes to the centre of the view volume by translation
        t1 = np.matrix([[1, 0, 0, -self.vrp[0, 0]],
                        [0, 1, 0, -self.vrp[0, 1]],
                        [0, 0, 1, -self.vrp[0, 2]],
                       [0, 0, 0, 1]])

        vtm = t1 * vtm

        # tu is the cross product (np.cross) of the vup and vpn vectors.
        tu = np.cross(self.vup, self.vpn)

        # tvup is the cross product of the vpn and tu vectors.
        tvup = np.cross(self.vpn, tu)

        # tvpn is a copy of the vpn vector.
        tvpn = np.copy(self.vpn)

        # copy normalized views back to fields
        self.u = self.normalize(tu)
        self.vup = self.normalize(tvup)
        self.vpn = self.normalize(tvpn)

        # align the axes
        r1 = np.matrix([[tu[0, 0], tu[0, 1], tu[0, 2], 0.0],
                        [tvup[0, 0], tvup[0, 1], tvup[0, 2], 0.0],
                        [tvpn[0, 0], tvpn[0, 1], tvpn[0, 2], 0.0],
                        [0.0, 0.0, 0.0, 1.0]])

        vtm = r1 * vtm

        # Translating the lower left corner of the view space to the origin
        # vtm = T(0.5*self.extent[0], 0.5*self.extent[1], 0) * vtm
        vtm = np.matrix([[1, 0, 0, 0.5*self.extent[0]],
                         [0, 1, 0, 0.5*self.extent[1]],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]]) * vtm

        # Using the extent and screen size values to scale to the screen.
        # vtm = S(-self.screen[0] / self.extent[0], -self.screen[1] / self.extent[1], 1.0 / self.extent[2]) * vtm
        vtm = np.matrix([[-self.screen[0] / self.extent[0], 0, 0, 0],
                         [0, -self.screen[1] / self.extent[1], 0, 0],
                         [0, 0, 1.0 / self.extent[2], 0],
                         [0, 0, 0, 1]]) * vtm

        # translating the lower left corner to the origin and add the view offset, to give a little buffer
        #  around the top and left edges of the window.
        # vtm = T(self.screen[0] + self.offset[0], self.screen[1] + self.offset[1], 0) * vtm
        vtm = np.matrix([[1, 0, 0, self.screen[0] + self.offset[0]],
                         [0, 1, 0, self.screen[1] + self.offset[1]],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]]) * vtm

        return vtm

    # Normalize the view axes tu, tvup, and tvpn to unit length
    def normalize(self, matrix):

        Vnorm = []
        Vx = matrix[0, 0]
        Vy = matrix[0, 1]
        Vz = matrix[0, 2]
        length = math.sqrt(Vx*Vx + Vy*Vy + Vz*Vz)
        Vnorm.append(Vx / length)
        Vnorm.append(Vy / length)
        Vnorm.append(Vz / length)

        matrix = np.matrix(Vnorm)
        return matrix

    # Create a clone method for your View object that makes a duplicate View object and returns it. That means you
    # need to create a new View object and the manually copy each field from the current View to the new View object.
    def clone(self):
        duplicate = View()
        duplicate.vpn = self.vpn.copy()
        duplicate.vrp = self.vrp.copy()
        duplicate.vup = self.vup.copy()
        duplicate.u = self.u.copy()
        duplicate.extent = self.extent[:]
        duplicate.offset = self.offset[:]
        duplicate.screen = self.screen[:]

        return duplicate

    def rotateVRC(self, angle_vup, angle_u):
        # point ( VRP + VPN * extent[Z] * 0.5 )
        d = np.matrix(self.vrp + self.vpn * self.extent[2] * 0.5)
        # a translation matrix to move the point ( VRP + VPN * extent[Z] * 0.5 ) to the origin
        t1 = np.matrix([[1, 0, 0, -d[0, 0]],
                        [0, 1, 0, -d[0, 1]],
                        [0, 0, 1, -d[0, 2]],
                        [0, 0, 0, 1]])

        # an axis alignment matrix Rxyz using u, vup and vpn.
        # uT = self.u
        # vupT = self.vup
        # vpnT = self.vpn
        uT = self.u.T
        vupT = self.vup.T
        vpnT = self.vpn.T

        Rxyz = np.matrix([[uT[0, 0], uT[1, 0], uT[2, 0], 0],
                          [vupT[0, 0], vupT[1, 0], vupT[2, 0], 0],
                          [vpnT[0, 0], vpnT[1, 0], vpnT[2, 0], 0],
                          [0, 0, 0, 1]])

        # rotation matrix about the Y axis by the VUP angle, put it in r1.
        r1 = np.matrix([[math.cos(angle_vup), 0, math.sin(angle_vup), 0],
                        [0, 1, 0, 0],
                        [-(math.sin(angle_vup)), 0, math.cos(angle_vup), 0],
                        [0, 0, 0, 1]])

        # a rotation matrix about the X axis by the U angle. Put it in r2.
        r2 = np.matrix([[1, 0, 0, 0],
                        [0, math.cos(angle_u), -(math.sin(angle_u)), 0],
                        [0, math.sin(angle_u), (math.cos(angle_u)), 0],
                        [0, 0, 0, 1]])

        # a translation matrix that has the opposite translation from step 1.
        t2 = np.matrix([[1, 0, 0, d[0, 0]],
                        [0, 1, 0, d[0, 1]],
                        [0, 0, 1, d[0, 2]],
                        [0, 0, 0, 1]])

        # a numpy matrix where the VRP is on the first row, with a 1 in the homogeneous coordinate, and u, vup, and
        # vpn are the next three rows, with a 0 in the homogeneous coordinate.
        tvrc = np.matrix([[self.vrp[0, 0], self.vrp[0, 1], self.vrp[0, 2], 1],
                          [self.u[0, 0], self.u[0, 1], self.u[0, 2], 0],
                          [self.vup[0, 0], self.vup[0, 1], self.vup[0, 2], 0],
                          [self.vpn[0, 0], self.vpn[0, 1], self.vpn[0, 2], 0]])

        tvrc = (t2*Rxyz.T*r2*r1*Rxyz*t1*tvrc.T).T

        # copy the values from tvrc back into the VPR, U, VUP, and VPN fields and normalize U, VUP, and VPN.
        self.vrp = tvrc[0, :3]
        self.u = self.normalize(tvrc[1, :3])
        self.vup = self.normalize(tvrc[2, :3])
        self.vpn = self.normalize(tvrc[3, :3])

        # print "d is ", d
        # print "t1 is :", t1
        # print "rxyz is: ", Rxyz
        # print "r1 is :", r1
        # print "r2 is :", r2
        # print self.u
        # print tvrc.T


if __name__ == "__main__":
    view = View()
    # print view.build()
    duplicate = view.clone()
    # print duplicate.extent
    # print duplicate.vpn
    view.rotateVRC(10, 10)
