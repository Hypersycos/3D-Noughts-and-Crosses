import math
import pygame
import pygame.gfxdraw
from shapely.geometry import Polygon


class Vector3d:

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def clone(self):
        return __class__(self.x, self.y, self.z)

    def __add__(self, addition):
        if isinstance(addition, int) or isinstance(addition, float):
            return __class__(self.x + addition, self.y + addition, self.z + addition)
        else:
            return __class__(self.x + addition.x, self.y + addition.y, self.z + addition.z)

    def __sub__(self, subtraction):
        if isinstance(subtraction, int) or isinstance(subtraction, float):
            return __class__(self.x - subtraction, self.y - subtraction, self.z - subtraction)
        else:
            return __class__(self.x - subtraction.x, self.y - subtraction.y, self.z - subtraction.z)

    def __mul__(self, mult):
        if isinstance(mult, int) or isinstance(mult, float):
            return __class__(self.x * mult, self.y * mult, self.z * mult)
        else:
            return __class__(self.x * mult.x, self.y * mult.y, self.z * mult.z)

    def __truediv__(self, mult):
        if isinstance(mult, int) or isinstance(mult, float):
            return __class__(self.x / mult, self.y / mult, self.z / mult)
        else:
            return __class__(self.x / mult.x, self.y / mult.y, self.z / mult.z)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        elif self.x != other.x:
            return False
        elif self.y != other.y:
            return False
        elif self.z != other.z:
            return False
        else:
            return True

    def __str__(self):
        return str(round(self.x * 1000) / 1000) + ", " + str(round(self.y * 1000) / 1000) + ", " + str(
            round(self.z * 1000) / 1000)

    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def dotProduct(self, vector):
        x = self.x * vector.x
        y = self.y * vector.y
        z = self.z * vector.z
        return x + y + z

    def angleBetween(self, other):
        # returns the angle in radians between two vectors using u.v = |u| * |v| * cos\theta
        # guaranteed to be <=pi
        denom = self.magnitude() * other.magnitude()
        numer = self.dotProduct(other)
        return math.acos(numer / denom)

    def rotateX(self, theta, return_new=False):
        # performs a rotation of theta radians along the x-axis
        # applies the rotation to the current vector, unless return_new == True
        y = self.y * math.cos(theta) - self.z * math.sin(theta)
        z = self.z * math.cos(theta) + self.y * math.sin(theta)
        if return_new:
            return __class__(self.x, y, z)
        else:
            self.y, self.z = y, z

    def rotateY(self, theta, return_new=False):
        # performs a rotation of theta radians along the y-axis
        # applies the rotation to the current vector, unless return_new == True
        x = self.x * math.cos(theta) - self.z * math.sin(theta)
        z = self.z * math.cos(theta) + self.x * math.sin(theta)
        if return_new:
            return __class__(x, self.y, z)
        else:
            self.x, self.z = x, z

    def rotateZ(self, theta, return_new=False):
        # performs a rotation of theta radians along the z-axis
        # applies the rotation to the current vector, unless return_new == True
        x = self.x * math.cos(theta) - self.y * math.sin(theta)
        y = self.y * math.cos(theta) + self.x * math.sin(theta)
        if return_new:
            return __class__(x, y, self.z)
        else:
            self.x, self.y = x, y

    def modifyAxes(self, rotation):
        # applies a Euler angles rotation in the order X->Y->Z
        self.rotateX(rotation.x)
        self.rotateY(rotation.y)
        self.rotateZ(rotation.z)
        return self


class Rotation3d(Vector3d):
    # A vector storing a Euler angles rotation

    def __init__(self, x, y, z, radians=False):
        super().__init__(x, y, z)
        if not radians:
            self.update(x, y, z, False)

    def update(self, x, y, z, radians=False):
        # sets the vector's angles in degrees unless radians == True
        if radians:
            self.x = x
            self.y = y
            self.z = z
        else:
            self.x = math.radians(x)
            self.y = math.radians(y)
            self.z = math.radians(z)

    def normalise(self):
        # normalises all angles to be below 2pi
        if self.x > 2 * math.pi:
            self.x -= 2 * math.pi
        elif self.x < 0:
            self.x += 2 * math.pi
        if self.y > 2 * math.pi:
            self.y -= 2 * math.pi
        elif self.y < 0:
            self.y += 2 * math.pi
        if self.z > 2 * math.pi:
            self.z -= 2 * math.pi
        elif self.z < 0:
            self.z += 2 * math.pi


class Position3d(Vector3d):

    def getDistance(self, otherPosition):
        return (self - otherPosition).magnitude()


class Camera:
    # a camera which always looks towards a set position

    def __init__(self, position=None, orientation=Rotation3d(0, 0, 0), fov=90, width=10, height=10, zoom=20,
                 target=Position3d(0, 0, 0)):
        self.clock = pygame.time.Clock()
        self.position = None
        self.zoom_linearity = 1.3

        self.target = target
        if position is None:
            self.orientation = orientation
            self.orientation.z = 0
            self.zoom = zoom
        else:
            self.zoom = position.getDistance(target)
            direction = target - position
            ox = math.atan2(direction.y, direction.x)
            oy = math.asin((direction / direction.magnitude()).z)
            self.orientation = Rotation3d(ox, oy, 0)
        self.apply_zoom_and_orientation()

        self.fov = fov
        self.updateScreen(width, height)
        self.sensitivity = 1
        self.zoom_sensitivity = 1
        self.locked = False
        self.radius = 1.8 * fov / 90
        self.xaxis = Position3d(1, 0, 0)
        self.yaxis = Position3d(0, 1, 0)
        self.zaxis = Position3d(0, 0, 1)

    def updateScreen(self, width, height):
        # updates the values used for rendering to a pygame screen
        self.ar = width / height
        self.centre = (width / 2, height / 2)
        self.vfov = math.tan(math.radians(self.fov) / 2)
        self.hfov = self.ar * math.tan(math.radians(self.fov) / 2)

    def toggleLock(self):
        # toggles locking of the mouse
        if self.locked:
            self.locked = False
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)
            pygame.mouse.set_pos(self.centre)
        else:
            self.locked = True
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)

    def move(self, diff, zoom_diff):
        # converts XY mouse movements into rotation and the mouse wheel to forward and backwards movement
        yRot = diff[0] * self.sensitivity
        xRot = diff[1] * -self.sensitivity
        if self.zoom == -2:
            xRot *= -1
            yRot *= -1
        self.zoom += zoom_diff * self.zoom_sensitivity
        if self.zoom < -2:
            self.zoom = -2
        if self.zoom > 20:
            self.zoom = 20
        self.orientation += Rotation3d(xRot, yRot, 0)
        if self.orientation.x > math.pi / 2:
            self.orientation.x = math.pi / 2
        elif self.orientation.x < -math.pi / 2:
            self.orientation.x = -math.pi / 2
        self.apply_zoom_and_orientation()

    def apply_zoom_and_orientation(self):
        self.position = self.target - Position3d(0, 0, self.zoom_linearity**(self.zoom)).modifyAxes(self.orientation)
        self.xaxis = Position3d(1, 0, 0).modifyAxes(self.orientation)
        self.yaxis = Position3d(0, 1, 0).modifyAxes(self.orientation)
        self.zaxis = Position3d(0, 0, 1).modifyAxes(self.orientation)

    def render(self, screen, items, width, height):
        self.updateScreen(width, height)
        order = furthestFirst(items, origin - self.position)
        for item in order:
            item.render(screen, self.vfov, self.hfov, self.position, self.xaxis, self.yaxis, self.zaxis,
                        self.orientation, width, height)


class Face:

    def __init__(self, points, colour=(0, 200, 0)):
        self.points = points
        # self.generateTriangles()
        self.position = Position3d(0, 0, 0)
        self.getPos()
        self.colour = colour

    def __str__(self):
        toReturn = ""
        for item in self.points:
            toReturn += "(" + str(item) + "), "
        return toReturn[:-2]

    def getPos(self):
        for item in self.points:
            self.position += item.position
        self.position /= len(self.points)

    # def generateTriangles(self):
    #     self.triangles = []
    #     for i in range(1, len(self.points) - 1, 1):
    #         self.triangles.append((self.points[0], self.points[i], self.points[i + 1]))

    def draw(self, screen, relativePos):
        coords = [(point.lastRenderX, point.lastRenderY) for point in self.points]
        length_cutoff = min(screen.get_width(), screen.get_height()) ** 2 / 2
        line_cutoff = len(self.points)
        long_lines = 0

        for i in range(len(coords)-1):
            x = coords[i+1][0] - coords[i][0]
            y = coords[i+1][1] - coords[i][1]
            length = x**2 + y**2
            if length > length_cutoff:
                long_lines += length // length_cutoff
                if long_lines > line_cutoff:
                    break
        if long_lines <= line_cutoff:
            pygame.draw.polygon(screen, self.colour, coords, 0)
        else:
            pygame.draw.polygon(screen, self.colour, coords, 5)

    def render(self, screen, relativePos):
        for i in range(0, 5):
            count = len(list(filter(lambda x: not x.offScreen[i], self.points)))
            if count == 0:
                # ensure that not all of the points are off-screen in the same direction
                # (i.e. the object is off-screen)
                return

        self.draw(screen, relativePos)


class WireframeFace(Face):

    def __init__(self, points, colour=(0, 200, 0), width=5, min_width=1):
        super().__init__(points, colour)
        self.width = width
        self.min_width = min_width

    def draw(self, screen: pygame.Surface, relativePos):
        coords = [(point.lastRenderX, point.lastRenderY) for point in self.points]
        width = int(max(self.width / relativePos.magnitude(), self.min_width))
        pygame.draw.polygon(screen, self.colour, coords, width)
        pygame.gfxdraw.aapolygon(screen, coords, self.colour)

    @classmethod
    def from_face(cls, face, width=5, min_width=1):
        return WireframeFace(face.points, face.colour, width, min_width)


class Point:

    def __init__(self, x, y, z, colour=(0, 200, 0), radians=False):
        self.origPos = Position3d(x, y, z)
        self.position = Position3d(x, y, z)
        self.colour = colour
        self.colours = []
        self.lastRenderX = 0
        self.lastRenderY = 0
        self.offScreen = [False, False, False, False, False]
        self.radius = 1
        self.canvas = pygame.Surface((self.radius * 2 + 1, self.radius * 2 + 1))
        pygame.draw.circle(self.canvas, self.colour, (self.radius, self.radius), self.radius)

    def __str__(self):
        return str(self.position)

    def render(self, screen, vfov, hfov, camera_pos, xaxis, yaxis, zaxis, screenWidth, screenHeight):
        relativePos = self.position + camera_pos
        x, y, z = relativePos.dotProduct(xaxis), relativePos.dotProduct(yaxis), relativePos.dotProduct(zaxis)
        if z == 0:
            # avoid div 0 error
            return -1
        dist = relativePos.magnitude()
        # projects point onto screen
        self.lastRenderX = math.floor((x / (z * hfov) + 1 / 2) * screenWidth)
        self.lastRenderY = math.floor((1 - (y / (z * vfov) + 1 / 2)) * screenHeight)
        if z < 0:
            self.lastRenderX = -self.lastRenderX
            self.lastRenderY = -self.lastRenderY
        if z < 0:  # behind, left, right, above, below
            self.offScreen[0] = True
        else:
            self.offScreen[0] = False
        if self.lastRenderX < 0:
            self.offScreen[1] = True
            self.offScreen[2] = False
        elif self.lastRenderX > screenWidth:
            self.offScreen[1] = False
            self.offScreen[2] = True
        else:
            self.offScreen[1] = False
            self.offScreen[2] = False
        if self.lastRenderY < 0:
            self.offScreen[3] = True
            self.offScreen[4] = False
        elif self.lastRenderY > screenHeight:
            self.offScreen[3] = False
            self.offScreen[4] = True
        else:
            self.offScreen[3] = False
            self.offScreen[4] = False


class Object3d:

    def __init__(self, position, size, rotation, colour=(0, 200, 0), static=True):
        self.position = position
        self.size = size
        self.rotation = rotation
        self.colour = colour
        self.points = []
        self.faces = []
        self.static = static
        self.setup()
        self.rotate(rotation, True)

    def rotate(self, rotation, absolute=False):
        for item in self.points:
            item.position = item.origPos * 1
        if absolute:
            self.rotation = rotation
        else:
            self.rotation += rotation
        for item in self.points:
            item.position.modifyAxes(self.rotation)
        for item in self.faces:
            item.getPos()

    def render(self, screen, vfov, hfov, camera_pos, xaxis, yaxis, zaxis, cameraRotation, width, height):
        relativePos = self.position - camera_pos
        posList = []
        for item in self.points:
            posList.append(item.render(screen, vfov, hfov, relativePos, xaxis, yaxis, zaxis, width, height))
        order = furthestFirst(self.faces, relativePos)
        for item in order:
            item.render(screen, relativePos)

    def sortClockwise(self, points, fx, fy):
        if len(points) < 2:
            return points
        mid = len(points) // 2
        a = self.sortClockwise(points[:mid], fx, fy)
        b = self.sortClockwise(points[mid:], fx, fy)
        return self.mergeLists(a, b, fx, fy)

    def compareClockwise(self, point1, point2, fx, fy):
        x1, x2, y1, y2 = fx(point1), fx(point2), fy(point1), fy(point2)
        if x1 >= 0 and x2 < 0:
            return True
        elif x1 == 0 and x2 == 0:
            return y1 > y2

        det = x1 * y2 - x2 * y1
        if det < 0:
            return True
        elif det > 0:
            return False
        else:
            return False

    def mergeLists(self, list1, list2, fx, fy):
        endList = []
        while len(list1) > 0 and len(list2) > 0:  # while items in both lists
            if self.compareClockwise(list1[0], list2[0], fx, fy):  # which has smallest item?
                endList.append(list2.pop(0))
            else:  # remove 1st item of smaller and add to newlist
                endList.append(list1.pop(0))
        if len(list1) > 0:  # if list1 still has items
            endList.extend(list1)
        else:  # add all items(already sorted)
            endList.extend(list2)
        return endList

    def setup(self):
        pass


class Line(Object3d):

    def __init__(self, p1: Position3d, p2: Position3d, width, width_vector, colour):
        self.p1 = p1
        self.p2 = p2
        self.width = width
        self.direction = (p2 - p1)
        self.length = self.direction.magnitude()
        self.direction /= self.length
        self.width_vector = width_vector
        super().__init__((p1 + p2) / 2, None, Rotation3d(0, 0, 0), colour)

    def setup(self):
        width = self.width_vector * (self.width / 2)
        points = []
        for mult in [-0.5, 0.5]:
            point = origin + self.direction * self.length * mult
            points.append(point + width)
            points.append(point - width)
            width = Position3d(0, 0, 0)-width
        for point in points:
            self.points.append(Point(point.x, point.y, point.z, self.colour))
        self.faces = [Face(self.points, self.colour)]


class Cuboid(Object3d):

    def __init__(self, position, size, rotation, colour=(0, 200, 0), outline_width=0, outline_colour=(0, 0, 0),
                 static=True):
        self.connections = []
        self.outline_width = outline_width
        self.outline_colour = outline_colour
        super().__init__(position, size, rotation, colour, static)

    def setup(self):
        self.points = []
        self.faces = []
        size = self.size
        values = ((size.x / 2, size.y / 2, size.z / 2),
                  (-size.x / 2, size.y / 2, size.z / 2),
                  (size.x / 2, -size.y / 2, size.z / 2),
                  (-size.x / 2, -size.y / 2, size.z / 2))
        for item in values:
            self.points.append(Point(item[0], item[1], item[2], self.colour))
            self.points.append(Point(-item[0], -item[1], -item[2], self.colour))
        values = [size.x / 2, size.y / 2, size.z / 2]
        for i in range(2):
            points = []
            for item in self.points:
                if item.position.x == values[0]:
                    points.append(item)
            # points.sort(key=lambda x: math.acos(x.position.y/math.sqrt(x.position.y**2+x.position.z**2)))
            points = self.sortClockwise(points, lambda x: x.position.y, lambda x: x.position.z)
            self.faces.append(Face(points, self.colour))
            values[0] = -values[0]
        del values[0]
        for i in range(2):
            points = []
            for item in self.points:
                if item.position.y == values[0]:
                    points.append(item)
            # points.sort(key=lambda x: math.acos(x.position.z/math.sqrt(x.position.x**2+x.position.z**2)))
            points = self.sortClockwise(points, lambda x: x.position.x, lambda x: x.position.z)
            # for item in points:
            #    print(item, math.sqrt(item.position.x**2+item.position.z**2) / item.position.z)
            self.faces.append(Face(points, self.colour))
            values[0] = -values[0]
        del values[0]
        for i in range(2):
            points = []
            for item in self.points:
                if item.position.z == values[0]:
                    points.append(item)
            # points.sort(key=lambda x: math.acos(x.position.y/math.sqrt(x.position.x**2+x.position.y**2)))
            points = self.sortClockwise(points, lambda x: x.position.x, lambda x: x.position.y)
            self.faces.append(Face(points, self.colour))
            values[0] = -values[0]

        if self.outline_width > 0:
            outlines = []
            pairs = [(0, 2), (0, 4), (0, 7),
                     (1, 3), (1, 5), (1, 6),
                     (2, 5), (2, 6),
                     (3, 4), (3, 7),
                     (4, 6),
                     (5, 7)]
            for pair in pairs:
                p1 = self.points[pair[0]].position
                p2 = self.points[pair[1]].position
                mid = (p1 + p2) / 2
                position = mid * (self.outline_width / 2 * math.sqrt(2) + 1)
                direction = p2 - p1
                if direction.dotProduct(Vector3d(1, 1, 1)) < 0:
                    direction /= -1
                size = direction + self.outline_width
                # print(p1, p2, mid, position, size, sep=" | ")
                outlines.append(Cuboid(position, size, Rotation3d(0, 0, 0), self.outline_colour, outline_width=0))
            for outline in outlines:
                for point in outline.points:
                    point.origPos += outline.position
                    self.points.append(point)
                for face in outline.faces:
                    self.faces.append(face)


class WireframeCuboid(Cuboid):

    def __init__(self, position, size, rotation, colour=(0, 200, 0), outline_width=5, min_width=1, static=True):
        super().__init__(position, size, rotation, colour, outline_width=0, static=static)
        self.outline_width = outline_width
        self.min_width = min_width
        for i in range(len(self.faces)):
            self.faces[i] = WireframeFace.from_face(self.faces[i], outline_width, min_width)


def furthestFirst(li, relativePos):
    order = []
    for item in li:
        pos = (item.position + relativePos)
        order.append([item, pos.magnitude()])
    order.sort(key=lambda x: -x[1])
    order = list(map(lambda x: x[0], order))
    return order


origin = Rotation3d(0, 0, 0)
