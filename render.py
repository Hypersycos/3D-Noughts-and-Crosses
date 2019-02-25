import math
import pygame
import pygame.gfxdraw

class Vector3d:

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, addition):
        return __class__(self.x + addition.x, self.y + addition.y, self.z + addition.z)

    def __sub__(self, subtraction):
        return __class__(self.x - subtraction.x, self.y - subtraction.y, self.z - subtraction.z)

    def __mul__(self, mult):
        return __class__(self.x*mult, self.y*mult, self.z*mult)

    def __truediv__(self, mult):
        return __class__(self.x/mult, self.y/mult, self.z/mult)

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
        return str(round(self.x*1000)/1000)+", "+str(round(self.y*1000)/1000)+", "+str(round(self.z*1000)/1000)

    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def dotProduct(self, vector):
        x = self.x * vector.x
        y = self.y * vector.y
        z = self.z * vector.z
        return x+y+z

    def angleBetween(self, other):
        denom = self.magnitude() * other.magnitude()
        numer = self.x*other.x + self.y*other.y + self.z*other.z
        return math.acos(numer/denom)

    def rotateX(self, rotation):
        y = self.y*math.cos(rotation) - self.z*math.sin(rotation)
        z = self.z*math.cos(rotation) + self.y*math.sin(rotation)
        self.y, self.z = y,z

    def rotateY(self, rotation):
        x = self.x*math.cos(rotation) - self.z*math.sin(rotation)
        z = self.z*math.cos(rotation) + self.x*math.sin(rotation)
        self.x, self.z = x,z

    def rotateZ(self, rotation):
        x = self.x*math.cos(rotation) - self.y*math.sin(rotation)
        y = self.y*math.cos(rotation) + self.x*math.sin(rotation)
        self.x, self.y = x,y

    def modifyAxes(self, rotation, rtrn=False, prnt=False):
        self.rotateX(rotation.x)
        self.rotateY(rotation.y)
        self.rotateZ(rotation.z)
        if rtrn:
            return self


class Rotation3d(Vector3d):

    def __init__(self, x, y, z, radians=False):
        self.update(x, y, z, radians)

    def update(self, x, y, z, radians=False):
        if radians:
            self.x = x
            self.y = y
            self.z = z
        else:
            self.x = math.radians(x)
            self.y = math.radians(y)
            self.z = math.radians(z)

    def normalise(self):
        if self.x > 2*math.pi:
            self.x -= 2*math.pi
        elif self.x < 0:
            self.x += 2*math.pi
        if self.y > 2*math.pi:
            self.y -= 2*math.pi
        elif self.y < 0:
            self.y += 2*math.pi
        if self.z > 2*math.pi:
            self.z -= 2*math.pi
        elif self.z < 0:
            self.z += 2*math.pi

class Position3d(Vector3d):

    def getDistance(self, otherPosition):
        return (self-otherPosition).magnitude()

class Camera:

    def __init__(self, position = Position3d(0,0,0), orientation = Rotation3d(0,0,0), fov = 90, width = 10, height = 10):
        self.clock = pygame.time.Clock()
        self.position = position
        self.orientation = orientation
        self.target = Position3d(0, 0, 1)
        self.fov = fov
        self.updateScreen(width, height)
        self.move_speed = 0.01
        self.sensitivity = 1
        self.locked = False
        self.radius = 1.8*fov/90
        self.xaxis = Position3d(1, 0, 0)
        self.yaxis = Position3d(0, 1, 0)
        self.zaxis = Position3d(0, 0, 1)

    def updateScreen(self, width, height):
        self.ar = width/height
        self.centre = (width/2, height/2)
        self.vfov = math.tan(math.radians(self.fov)/2)
        self.hfov = self.ar*math.tan(math.radians(self.fov)/2)

    def toggleLock(self):
        if self.locked:
            self.locked = False
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)
            pygame.mouse.set_pos(self.centre)
        else:
            self.locked = True
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
        
    def move(self, diff, zoom):
        yRot = diff[0] * self.sensitivity
        xRot = diff[1] * -self.sensitivity
        self.orientation += Rotation3d(xRot, yRot, 0)
        self.position = Position3d(0, 0, -zoom).modifyAxes(self.orientation, True)
        if self.orientation.x > math.pi/2:
            self.orientation.x = math.pi/2
        elif self.orientation.x < -math.pi/2:
            self.orientation.x = -math.pi/2
        self.xaxis = Position3d(1, 0, 0).modifyAxes(self.orientation, True)
        self.yaxis = Position3d(0, 1, 0).modifyAxes(self.orientation, True)
        self.zaxis = Position3d(0, 0, 1).modifyAxes(self.orientation, True)

    def render(self, screen, items, width, height):
        self.updateScreen(width, height)
        self.clock.tick()
        order = furthestFirst(items, origin-self.position)
        for item in order:
            item.render(screen, self.vfov, self.hfov, self.position, self.xaxis, self.yaxis, self.zaxis, self.orientation, width, height)

class Face:

    def __init__(self, points, colour=(0, 200, 0)):
        self.points = points
        #self.generateTriangles()
        self.position = Position3d(0,0,0)
        self.getPos()
        self.colour = colour

    def __str__(self):
        toReturn = ""
        for item in self.points:
            toReturn += "("+str(item)+"), "
        return toReturn[:-2]

    def getPos(self):
        for item in self.points:
            self.position += item.position
        self.position /= len(self.points)

    def generateTriangles(self):
        self.triangles = []
        for i in range(1,len(self.points)-1,1):
            self.triangles.append((self.points[0],self.points[i],self.points[i+1]))

    def render(self, screen):
        for i in range(0,5):
            if len(list(filter(lambda x: not x.offScreen[i], self.points)))==0:
                return
        coords = [(point.lastRenderX,point.lastRenderY) for point in self.points]
        for i in range(1,len(self.points)-1):
            pygame.gfxdraw.aapolygon(screen, [coords[0], coords[i], coords[i+1]], self.colour)
            pygame.draw.polygon(screen, self.colour, [coords[0], coords[i], coords[i+1]], 0)
            

class Point:

    def __init__(self, x, y, z, colour=(0,200,0), radians=False):
        self.origPos = Position3d(x, y, z)
        self.position = Position3d(x,y,z)
        self.colour = colour
        self.colours = []
        self.lastRenderX = 0
        self.lastRenderY = 0
        self.offScreen = [False,False,False,False,False]
        self.radius = 1
        self.canvas = pygame.Surface((self.radius*2+1, self.radius*2+1))
        pygame.draw.circle(self.canvas, self.colour, (self.radius, self.radius), self.radius)

    def __str__(self):
        return str(self.position)

    def render(self, screen, vfov, hfov, camera_pos, xaxis, yaxis, zaxis, screenWidth, screenHeight):
        relativePos = self.position + camera_pos
        x, y, z = relativePos.dotProduct(xaxis), relativePos.dotProduct(yaxis), relativePos.dotProduct(zaxis)
        if z == 0:
            return -1
        dist = relativePos.magnitude()
        self.lastRenderX = math.floor((x/(z*hfov)+1/2)*screenWidth)
        self.lastRenderY = math.floor((1-(y/(z*vfov)+1/2))*screenHeight)
        if z < 0:
            self.lastRenderX = -self.lastRenderX
            self.lastRenderY = -self.lastRenderY
##        if z < 0 or self.lastRenderX < 0 or self.lastRenderX > screenWidth or self.lastRenderY < 0 or self.lastRenderY > screenHeight:
##            self.offScreen = True
##        else:
##            self.offScreen = False
        if z < 0: #behind, left, right, above, below
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

    def rasterise(self):
        if len(self.connections) == 0:
            return
        if len(self.colours) == 0:
            for i in range(0, len(self.connections)):
                self.colours.append((random.randint(0,255), random.randint(0,255), random.randint(0,255)))
        for i in range(len(self.connections)-1):
            #colour = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
            coords = [(item.lastRenderX,item.lastRenderY) for item in [self]+self.connections[i:i+2]]
            pygame.draw.polygon(screen, self.colours[i], coords, 0)

class Object3d:

    def __init__(self,position,size,rotation,colour=(0,200,0), static=True):
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
            item.position = item.origPos*1
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
        order = furthestFirst(self.points, relativePos)
        for item in order:
            posList.append(item.render(screen, vfov, hfov, relativePos, xaxis, yaxis, zaxis, width, height))
        order = furthestFirst(self.faces, relativePos)
        for item in order:
            item.render(screen)

    def sortClockwise(self, points, fx, fy):
        if len(points)<2:
            return points
        mid = len(points)//2
        a = self.sortClockwise(points[:mid], fx, fy)
        b = self.sortClockwise(points[mid:], fx, fy)
        return self.mergeLists(a, b, fx, fy)

    def compareClockwise(self, point1, point2, fx, fy):
        x1, x2, y1, y2 = fx(point1), fx(point2), fy(point1), fy(point2)
        if x1 >= 0 and x2 < 0:
            return True
        elif x1 == 0 and x2 == 0:
            return y1 > y2

        det = x1*y2 - x2*y1
        if det < 0:
            return True
        elif det > 0:
            return False
        else:
            return False

    def mergeLists(self, list1, list2, fx, fy):
        endList = []
        while len(list1)>0 and len(list2)>0:    #while items in both lists
            if self.compareClockwise(list1[0],list2[0], fx, fy):             #which has smallest item?
                endList.append(list2.pop(0))    
            else:               #remove 1st item of smaller and add to newlist
                endList.append(list1.pop(0))
        if len(list1)>0:            #if list1 still has items
            endList.extend(list1)
        else:                       #add all items(already sorted)
            endList.extend(list2)
        return endList

class Cuboid(Object3d):

    def setup(self):
        self.connections = []
        size = self.size
        values = ((size.x/2, size.y/2, size.z/2),
                  (-size.x/2, size.y/2, size.z/2),
                  (size.x/2, -size.y/2, size.z/2),
                  (-size.x/2, -size.y/2, size.z/2))
        for item in values:
            self.points.append(Point(item[0], item[1], item[2], self.colour))
            self.points.append(Point(-item[0], -item[1], -item[2], self.colour))
        values = [size.x/2, size.y/2, size.z/2]
        for i in range(2):
            points = []
            for item in self.points:
                if item.position.x == values[0]:
                    points.append(item)
            #points.sort(key=lambda x: math.acos(x.position.y/math.sqrt(x.position.y**2+x.position.z**2)))
            points = self.sortClockwise(points, lambda x: x.position.y, lambda x: x.position.z)
            self.faces.append(Face(points, self.colour))
            values[0] = -values[0]
        del values[0]
        for i in range(2):
            points = []
            for item in self.points:
                if item.position.y == values[0]:
                    points.append(item)
            #points.sort(key=lambda x: math.acos(x.position.z/math.sqrt(x.position.x**2+x.position.z**2)))
            points = self.sortClockwise(points, lambda x: x.position.x, lambda x: x.position.z)
            #for item in points:
            #    print(item, math.sqrt(item.position.x**2+item.position.z**2) / item.position.z)
            self.faces.append(Face(points, self.colour))
            values[0] = -values[0]
        del values[0]
        for i in range(2):
            points = []
            for item in self.points:
                if item.position.z == values[0]:
                    points.append(item)
            #points.sort(key=lambda x: math.acos(x.position.y/math.sqrt(x.position.x**2+x.position.y**2)))
            points = self.sortClockwise(points, lambda x: x.position.x, lambda x: x.position.y)
            self.faces.append(Face(points, self.colour))
            values[0] = -values[0]


def furthestFirst(li, relativePos):
    order = []
    for item in li:
        pos = (item.position+relativePos)
        order.append([item,pos.magnitude()])
    order.sort(key=lambda x:-x[1])
    order = list(map(lambda x:x[0], order))
    return order

origin = Rotation3d(0,0,0)
