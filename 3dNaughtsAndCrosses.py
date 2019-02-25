import pygame
import random
import math
from render import *

keybinds = {"Up": pygame.K_e, "Down": pygame.K_q, "Forward": pygame.K_w, "Backward": pygame.K_s, "Left": pygame.K_a, "Right": pygame.K_d, "Place": pygame.K_SPACE}
directions = {"Up": Vector3d(0, 1, 0), "Down": Vector3d(0, -1, 0), "Forward": Vector3d(0, 0, 1), "Backward": Vector3d(0, 0, -1), "Left": Vector3d(-1, 0, 0), "Right": Vector3d(1, 0, 0)}

pygame.init()
pygame.key.set_repeat(350,50)
#infoObject = pygame.display.Info()
windowX = 450#math.ceil(infoObject.current_x*0.6)
windowY = 450#math.ceil(infoObject.current_h*0.5)
screen = pygame.display.set_mode((windowX,windowY),pygame.RESIZABLE, 32)

def reverseDictLookup(dictionary, value):
    items = list(dictionary.items())
    items = list(filter(lambda x:x[1]==value, items))
    items = list(map(lambda x:x[0], items))
    if len(items) == 0:
        return None
    elif len(items) == 1:
        return items[0]
    else:
        return items

class Player:

    def __init__(self, colour=(0, 0, 0), name=""):
        self.colour = colour
        self.name = name

class Match:

    def __init__(self, x=3, y=3, z=3, players=[], wrapping=False):
        self.players = players
        self.currentTurn = 0
        self.x = x
        self.y = y
        self.z = z
        self.grid = self.generateGrid(x, y, z)
        self.currentlySelected = [0, 0, 0]
        self.winner = -1
        self.wrapping = wrapping
        self.render3d = True
        self.lastDrag = None
        self.zoom = 20
        self.generatePlayerColours()
        self.camera = Camera()
        self.camera.move((0, 0), 20)

    def generatePlayerColours(self):
        colourSpread = math.ceil(len(self.players)/3)
        if colourSpread == 0:
            return
        currentColour = 0
        i = 0
        ticks = 0
        while i < len(self.players):
            colour = [0, 0, 0]
            shade = (colourSpread-ticks) * 255 / colourSpread
            colour[currentColour] = shade
            self.players[i].colour = colour
            currentColour += 1
            if currentColour == 3:
                currentColour = 0
                ticks += 1
            i += 1

    def generateGrid(self, x, y, z):
        temp = []
        for i in range(x):
            tempX = []
            for j in range(y):
                tempY = []
                for k in range(z):
                    num = random.randint(1, 10)
                    if num > 10:
                        toAdd = random.randint(0, len(self.players)-1)
                    else:
                        toAdd = -1
                    tempY.append(toAdd)
                tempX.append(tempY)
            temp.append(tempX)
        return temp

    def generate2dGrid(self, x, y):
        temp = []
        for i in range(x):
            tempX = []
            for j in range(y):
                tempX.append(-1)
            temp.append(tempX)
        return temp

    def checkForWin(self, position, player):
        position = currentlySelected
        won = False
        for i in range(2):
            position[0] += 1
            if position[0] > self.x:
                if self.wrapping:
                    position[0] = 0
                else:
                    break
            if grid[position[0]][position[1]][position[2]] != player:
                break
        else:
            won = False
        if won:
            return True
        
        for i in range(2):
            position[0] -= 1
            if position[0] < 0:
                if self.wrapping:
                    position[0] = self.x-1
                else:
                    break
            if grid[position[0]][position[1]][position[2]] != player:
                break
        else:
            won = False
        if won:
            return True

    def makeMove(self, position, player):
        if self.grid[position[0]][position[1]][position[2]] != -1:
            return
        self.changePoint(position, player)
        self.checkForWin(position, player)
        self.currentTurn += 1
        if self.currentTurn >= len(self.players):
            self.currentTurn = 0

    def changePoint(self, position, new):
        x = position[0]
        y = position[1]
        z = position[2]
        self.grid[x][y][z] = new

    def eventLoop(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.winner = -2
            elif event.type == pygame.KEYDOWN:
                if event.key == keybinds["Forward"]:
                    self.moveSelection("Forward")
                elif event.key == keybinds["Backward"]:
                    self.moveSelection("Backward")
                elif event.key == keybinds["Left"]:
                    self.moveSelection("Left")
                elif event.key == keybinds["Right"]:
                    self.moveSelection("Right")
                elif event.key == keybinds["Up"]:
                    self.moveSelection("Up")
                elif event.key == keybinds["Down"]:
                    self.moveSelection("Down")
                elif event.key == keybinds["Place"]:
                    self.makeMove(self.currentlySelected, self.currentTurn)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.zoom -= 1
                    if (self.zoom < 5):
                        self.zoom = 5
                    self.camera.move((0, 0), self.zoom)
                elif event.button == 5:
                    self.zoom += 1
                    self.camera.move((0, 0), self.zoom)
        if self.render3d and pygame.mouse.get_pressed()[0]:
            if self.lastDrag == None:
                self.lastDrag = pygame.mouse.get_pos()
            else:
                newDrag = pygame.mouse.get_pos()
                diff = (self.lastDrag[0] - newDrag[0], self.lastDrag[1] - newDrag[1])
                self.camera.move(diff, self.zoom)
                self.lastDrag = newDrag
        else:
            self.lastDrag = None

    
    def translateMove(self, direction):
        angle = math.pi/2
        vector = directions[direction] + Vector3d(0,0,0)
        rotation = self.camera.orientation
        rotation /= angle
        vector.rotateX(round(rotation.x)*angle)
        vector.rotateY(round(rotation.y)*angle)
        vector.rotateZ(round(rotation.z)*angle)
        vector.x = round(vector.x)
        vector.y = round(vector.y)
        vector.z = round(vector.z)
        return reverseDictLookup(directions, vector)
            

    def moveSelection(self, direction):
        if self.render3d:
            direction = self.translateMove(direction)
        if direction == "Forward":
            if self.currentlySelected[2] < self.z-1:
                self.currentlySelected[2] += 1
            elif self.wrapping:
                self.currentlySelected[2] = 0
        elif direction == "Backward":
            if self.currentlySelected[2] > 0:
                self.currentlySelected[2] -= 1
            elif self.wrapping:
                self.currentlySelected[2] = self.z-1
        elif direction == "Right":
            if self.currentlySelected[0] < self.x-1:
                self.currentlySelected[0] += 1
            elif self.wrapping:
                self.currentlySelected[0] = 0
        elif direction == "Left":
            if self.currentlySelected[0] > 0:
                self.currentlySelected[0] -= 1
            elif self.wrapping:
                self.currentlySelected[0] = self.x-1
        elif direction == "Up":
            if self.currentlySelected[1] < self.y-1:
                self.currentlySelected[1] += 1
            elif self.wrapping:
                self.currentlySelected[1] = 0
        elif direction == "Down":
            if self.currentlySelected[1] > 0:
                self.currentlySelected[1] -= 1
            elif self.wrapping:
                self.currentlySelected[1] = self.y-1

    def getLayer(self, y):
        if y < 0 or y >= self.y:
            return None

        temp = self.generate2dGrid(self.x, self.z)
        for x in range(self.x):
            for z in range(self.z):
                temp[x][z] = self.grid[x][y][z]

        return temp
        

    def printGrid(self):
        for y in range(self.y):
            for z in range(self.z):
                for x in range(self.x):
                    print(self.grid[x][y][z], end = "")
                print()
            print()
            print()

    def render(self, width, height):
        if self.render3d:
            return self.renderIn3d(width, height)
        else:
            return self.renderSideBySide(width, height)

    def invertColour(self, colour):
        newColour = []
        for i in range(len(colour)):
            newColour.append(255 - colour[i])
        return newColour

    def renderSideBySide(self, width, height):
        grids = []
        for i in range(self.currentlySelected[1]-1, self.currentlySelected[1]+2):
            if i < 0 and self.wrapping:
                i += self.y
            elif i >= self.y and self.wrapping:
                i -= self.y
            grids.append(self.getLayer(i))

        canvas = pygame.Surface((width, height), pygame.SRCALPHA)
        gridSize = min(width//3, height)
        if gridSize == width//3:
            offset = (0, (height-gridSize)//2)
        else:
            offset = ((width-gridSize*3)//2, 0)
        markerSize = min(gridSize // self.x, gridSize // self.z)-4
        if self.x > self.z:
            gridOffset = (0, markerSize * (self.x - self.z))
        elif self.x < self.z:
            gridOffset = (markerSize * (self.z - self.x), 0)
        else:
            gridOffset = (0, 0)


        for i in range(len(grids)):
            grid = grids[i]
            if grid == None:
                continue
            gridLeft = gridOffset[0]+(gridSize + gridOffset[0])*i + offset[0] + 4
            gridBottom = gridSize - gridOffset[1] - markerSize - 4 + offset[1]
            for x in range(len(grid)):
                for y in range(len(grid[0])):
                    player = grid[x][y]
                    left = gridLeft + x*(markerSize+2)
                    top = gridBottom - y*(markerSize+2)
                    if player != -1:
                        colour = self.players[player].colour
                        if (x, y) == (self.currentlySelected[0], self.currentlySelected[2]) and i == 1:
                            colour = self.invertColour(colour)
                        pygame.draw.rect(canvas, colour, pygame.Rect(left, top, markerSize, markerSize))
                    elif (x, y) == (self.currentlySelected[0], self.currentlySelected[2]) and i == 1:
                        pygame.draw.rect(canvas, self.players[self.currentTurn].colour, pygame.Rect(left, top, markerSize, markerSize))
                        
            top = gridBottom - (self.z-1)*(markerSize+2)
            for x in range(1, len(grid)):
                left = gridLeft + x*(markerSize+2) - 2
                pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(left, top, 2, (markerSize+2)*self.z-2))

            for y in range(0, len(grid[0])-1):
                top = gridBottom - y*(markerSize+2) - 2
                pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(gridLeft, top, (markerSize+2)*self.x-2, 2))

        return canvas
        
    def renderIn3d(self, width, height):
        canvas = pygame.Surface((width, height))
        canvas.fill((255, 255, 255))
        centre = Position3d((self.x - 1) / 2, (self.y - 1) / 2, (self.z - 1) / 2)
        objects = []
        rotation = Rotation3d(0, 0, 0)
        for x in range(self.x):
            for y in range(self.y):
                for z in range(self.z):
                    position = Position3d(x,y,z) - centre
                    size = Vector3d(0.5, 0.5, 0.5)
                    index = self.grid[x][y][z]
                    if index == -1:
                        if [x, y, z] == self.currentlySelected:
                            colour = self.players[self.currentTurn].colour
                        else:
                            continue
                    else:
                        if [x, y, z] == self.currentlySelected:
                            colour = self.invertColour(self.players[index].colour)
                        else:
                            colour = self.players[index].colour
                    objects.append(Cuboid(position, size, rotation, colour))
        colour = (0, 0, 0)
        thickness = 0.05
        for x in range(1, self.x):
            for y in range(1, self.y):
                position = Position3d(x-0.5, y-0.5, (self.z-1)/2)-centre
                size = Vector3d(thickness, thickness, self.z)
                objects.append(Cuboid(position, size, rotation, colour))
                for z in range(1, self.z):
                    position = Position3d((self.x-1)/2, y-0.5, z-0.5)-centre
                    size = Vector3d(self.x, thickness, thickness)
                    objects.append(Cuboid(position, size, rotation, colour))
            for z in range(1, self.z):
                position = Position3d(x-0.5, (self.y-1)/2, z-0.5)-centre
                size = Vector3d(thickness, self.y, thickness)
                objects.append(Cuboid(position, size, rotation, colour))
        self.camera.render(canvas, objects, width, height)
        return canvas

def applyResize(width, height):
    global windowX
    global windowY
    global screen
    windowX = math.ceil(width)
    windowY = math.ceil(height)
    screen = pygame.display.set_mode((windowX,windowY),pygame.RESIZABLE, 32)

players = []
for i in range(0, 5):
    players.append(Player())

test = Match(3, 3, 3, players, False)
while True:
    screen.fill((255, 255, 255))
    screen.blit(test.render(windowX, windowY), (0, 0))
    pygame.display.flip()
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.VIDEORESIZE:
            applyResize(event.w,event.h)
    test.eventLoop(events)
