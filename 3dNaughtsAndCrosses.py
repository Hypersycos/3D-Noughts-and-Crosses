import itertools

import pygame
import random
import math
from render import *
from UI import *

keybinds = {"Up": pygame.K_e, "Down": pygame.K_q, "Forward": pygame.K_w, "Backward": pygame.K_s, "Left": pygame.K_a,
            "Right": pygame.K_d, "Place": pygame.K_SPACE, "Rotate_Right": pygame.K_RIGHT, "Rotate_Left": pygame.K_LEFT,
            "Rotate_Up": pygame.K_UP, "Rotate_Down": pygame.K_DOWN, "Reset_Camera": pygame.K_r, "Toggle_FPS": pygame.K_z,
            "Cam_Up": pygame.K_o, "Cam_Down": pygame.K_u, "Cam_Left": pygame.K_j, "Cam_Right": pygame.K_l,
            "Cam_Forward": pygame.K_i, "Cam_Backward": pygame.K_k, "Swap_View": pygame.K_c, "Toggle_Transparent_Cubes": pygame.K_t,
            "Increase_Explosion": pygame.K_EQUALS, "Decrease_Explosion": pygame.K_MINUS, "Toggle_Focus": pygame.K_f, "Toggle_Cursor": pygame.K_h}
directions = {"Up": Vector3d(0, 1, 0), "Down": Vector3d(0, -1, 0), "Forward": Vector3d(0, 0, 1),
              "Backward": Vector3d(0, 0, -1), "Left": Vector3d(-1, 0, 0), "Right": Vector3d(1, 0, 0)}
colours = {"background": (255, 255, 255, 255), "triButton": (100, 150, 255, 255), "text": (0, 0, 0, 255),
           "button": (200, 200, 200, 255)}

pygame.init()
pygame.key.set_repeat(350, 50)
# infoObject = pygame.display.Info()
windowX = 450  # math.ceil(infoObject.current_x*0.6)
windowY = 450  # math.ceil(infoObject.current_h*0.5)
screen = pygame.display.set_mode((windowX, windowY), pygame.RESIZABLE, 32)


def reverseDictLookup(dictionary, value):
    items = list(dictionary.items())
    items = list(filter(lambda x: x[1] == value, items))
    items = list(map(lambda x: x[0], items))
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

    def __init__(self, x=3, y=3, z=3, explosion=1, players=[], wrapping=False, demo=False):
        self.winningLine = None
        self.winningDirection = None
        self.running = not demo
        self.players = players
        self.currentTurn = 0
        self.x = x
        self.y = y
        self.z = z
        self.grid = self.generateGrid(x, y, z)
        self.objects = []
        self.currentlySelected = Position3d(0, 0, 0)
        self.winner = -1
        self.wrapping = wrapping
        self.render3d = True
        self.zoom2d = 3
        self.lastDrag = None
        self.camera = Camera()
        self.explosion = explosion
        self.lod = 0
        self.focus_centre = True
        self.solid_cubes = False
        self.draw_selected = True
        if demo:
            self.set_default_view()
            self.currentlySelected = Position3d(-1, -1, -1)
        else:
            self.generatePlayerColours()

    def set_default_view(self):
        # calculates required zoom to display entire grid
        fov = self.camera.fov / 2
        zoom = math.log(math.tan(math.radians(fov)) * math.sqrt((self.x) ** 2 + (self.y * self.explosion) ** 2) + self.z / 2, self.camera.zoom_linearity)
        zoom = math.ceil(zoom)
        self.camera.zoom = zoom
        self.camera.move((0, -10), 0)

    def generatePlayerColours(self):
        # number of different shades required given 6 distinct colours
        colourSpread = math.ceil(len(self.players) / 6)
        if colourSpread == 0:
            return
        currentColour = 0
        i = 0
        ticks = 0
        # all distinct colours, excluding black & white
        colours = list(itertools.product([0,1], repeat=3))[1:-1]

        # swaps blue and yellow
        colours[2], colours[3] = colours[3], colours[2]
        while i < len(self.players):
            colour = colours[currentColour]
            shade = (colourSpread - ticks) * 255 / colourSpread
            # using indices in reverse to get R->G->B rather than B->G->R
            colour = [colour[2-j] * shade for j in range(3)]
            self.players[i].colour = colour
            currentColour += 1
            if currentColour == len(colours):
                currentColour = 0
                ticks += 1
            i += 1

    def generateGrid(self, x, y, z):
        """Generates grid[x][y][z] filled with -1"""
        temp = []
        for i in range(x):
            tempX = []
            for j in range(y):
                tempY = []
                for k in range(z):
                    tempY.append(-1)
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

    def checkForWrap(self, position):
        """Checks whether position is in bounds. If in bounds or self.wrapping == true, returns the new position
        (modified to be in-bounds if necessary). Otherwise, returns None."""
        if position.x > self.x - 1:
            if self.wrapping:
                position.x = 0
            else:
                return None
        elif position.x < 0:
            if self.wrapping:
                position.x = self.x - 1
            else:
                return None

        if position.y > self.y - 1:
            if self.wrapping:
                position.y = 0
            else:
                return None
        elif position.y < 0:
            if self.wrapping:
                position.y = self.y - 1
            else:
                return None

        if position.z > self.z - 1:
            if self.wrapping:
                position.z = 0
            else:
                return None
        elif position.z < 0:
            if self.wrapping:
                position.z = self.z - 1
            else:
                return None

        return position

    def checkForWin(self, point_to_check, player):
        """Checks whether the latest change results in a line. Returns line_found, points_in_line, direction"""
        directions = [Position3d(0, 0, 1), Position3d(0, 1, 0), Position3d(1, 0, 0),
                      Position3d(1, 0, 1), Position3d(0, 1, 1), Position3d(1, 1, 0), Position3d(1, 1, 1),
                      Position3d(-1, 0, 1), Position3d(0, -1, 1), Position3d(-1, 1, 0),
                      Position3d(1, 1, -1), Position3d(1, -1, 1), Position3d(-1, 1, 1)]

        for direction in directions:
            # clone since Vector3D is mutable
            position = point_to_check.clone()
            points = [position.clone()]

            # go as far as possible in positive direction, either until no match found or victory found
            for i in range(2):
                position += direction
                temp = self.checkForWrap(position)
                # edge found
                if temp is None:
                    position -= direction
                    break
                position = temp
                points.append(position.clone())
                if self.grid[position.x][position.y][position.z] != player:
                    position -= direction
                    position = self.checkForWrap(position)
                    break
            else:
                return True, points, direction

            # start again in opposite direction from furthest point found
            # could be more efficient by re-using earlier progress, but it's not very expensive anyway
            points = [position.clone()]

            for i in range(2):
                position -= direction
                temp = self.checkForWrap(position)
                if temp is None:
                    break
                position = temp
                points.append(position.clone())
                if self.grid[position.x][position.y][position.z] != player:
                    break
            else:
                return True, points, direction

        return False, None, None

    def makeMove(self, position, player):
        """Attempts to put player's marker at position. If a valid move, will increment self.currentTurn and check for victory."""
        if self.grid[position.x][position.y][position.z] != -1 or not self.draw_selected:
            return
        self.changePoint(position, player)
        game_won, self.winningLine, self.winningDirection = self.checkForWin(position, player)
        if game_won:
            self.winner = self.currentTurn
            self.draw_selected = False
        self.currentTurn += 1
        if self.currentTurn >= len(self.players):
            self.currentTurn = 0
        self.objects = []

    def changePoint(self, position, new):
        """Converts Vector3D values to grid indices, saves on boilerplate code."""
        x = position.x
        y = position.y
        z = position.z
        self.grid[x][y][z] = new

    def eventLoop(self, events):
        # This grew as I added more functionality, and at this point really ought to be a lookup with keys -> actions
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
                    if self.winner == -1:
                        self.makeMove(self.currentlySelected, self.currentTurn)
                    else:
                        self.running = False
                elif event.key == keybinds["Swap_View"]:
                    self.render3d = not self.render3d
                elif event.key == keybinds["Toggle_Cursor"]:
                    self.draw_selected = not self.draw_selected
                    self.objects = []
                elif self.render3d:
                    if event.key == keybinds["Reset_Camera"]:
                        self.camera.target = Position3d(0, 0, 0)
                        self.camera.orientation = Rotation3d(0, 0, 0)
                        self.set_default_view()
                    elif event.key == keybinds["Increase_Explosion"]:
                        self.explosion += 0.2
                        self.objects = []
                    elif event.key == keybinds["Decrease_Explosion"]:
                        if self.explosion > 1:
                            self.explosion -= 0.2
                        if self.explosion < 1.2:
                            self.explosion = 1
                        self.objects = []
                    elif event.key == keybinds["Toggle_Focus"]:
                        self.focus_centre = not self.focus_centre
                        self.objects = []
                    elif event.key == keybinds["Toggle_Transparent_Cubes"]:
                        self.solid_cubes = not self.solid_cubes
                        self.objects = []
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    if self.render3d:
                        self.camera.move((0, 0), -0.5)
                    else:
                        self.zoom2d = max(3, self.zoom2d - 1)
                elif event.button == 5:
                    if self.render3d:
                        self.camera.move((0, 0), 0.5)
                    else:
                        self.zoom2d = min(self.zoom2d + 1, self.y)
        if self.render3d:
            if pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]:
                if self.lastDrag is None:
                    self.lastDrag = pygame.mouse.get_pos()
                else:
                    newDrag = pygame.mouse.get_pos()
                    diff = (self.lastDrag[0] - newDrag[0], self.lastDrag[1] - newDrag[1])
                    self.lastDrag = newDrag

                    if pygame.mouse.get_pressed()[0]:
                        # LMB rotates
                        diff = (diff[0] / windowX * 360, diff[1] / windowY * 360)
                        self.camera.move(diff, 0)
                    else:
                        # RMB pans
                        diff = (diff[0] / windowX * 4, diff[1] / windowY * -4)
                        self.camera.target += self.camera.xaxis * diff[0] + self.camera.yaxis * diff[1]
                        self.camera.apply_zoom_and_orientation()
            else:
                self.lastDrag = None
            keys = pygame.key.get_pressed()
            elapsed = self.camera.clock.get_time() / 1000
            diff = [0, 0]
            sens = 90 * elapsed
            if keys[keybinds["Rotate_Up"]]:
                diff[1] -= sens
            if keys[keybinds["Rotate_Down"]]:
                diff[1] += sens
            if keys[keybinds["Rotate_Left"]]:
                diff[0] -= sens
            if keys[keybinds["Rotate_Right"]]:
                diff[0] += sens
            if diff[0] != 0 or diff[1] != 0:
                self.camera.move(diff, 0)

            diff = [0, 0, 0]
            sens = 4 * elapsed
            if keys[keybinds["Cam_Up"]]:
                diff[1] += sens
            if keys[keybinds["Cam_Down"]]:
                diff[1] -= sens
            if keys[keybinds["Cam_Left"]]:
                diff[0] -= sens
            if keys[keybinds["Cam_Right"]]:
                diff[0] += sens
            if keys[keybinds["Cam_Forward"]]:
                diff[2] += sens
            if keys[keybinds["Cam_Backward"]]:
                diff[2] -= sens
            if diff[0] != 0 or diff[1] != 0 or diff[2] != 0:
                self.camera.target += self.camera.xaxis * diff[0] + self.camera.yaxis * diff[1] + self.camera.zaxis * diff[2]
                self.camera.apply_zoom_and_orientation()

    def translateMove(self, direction):
        """Converts direction from camera's orientation to global directions."""
        angle = math.pi / 2
        vector = directions[direction] + Vector3d(0, 0, 0)
        rotation = self.camera.orientation
        rotation /= angle
        vector.rotateX(round(rotation.x) * angle)
        vector.rotateY(round(rotation.y) * angle)
        vector.rotateZ(round(rotation.z) * angle)
        vector.x = round(vector.x)
        vector.y = round(vector.y)
        vector.z = round(vector.z)
        return reverseDictLookup(directions, vector)

    def moveSelection(self, direction):
        """Moves currently selected position in direction requested, from camera's orientation if in 3d."""
        if self.render3d:
            direction = self.translateMove(direction)
        old = self.currentlySelected.clone()

        if direction == "Forward":
            if self.currentlySelected.z < self.z - 1:
                self.currentlySelected.z += 1
            elif self.wrapping:
                self.currentlySelected.z = 0
        elif direction == "Backward":
            if self.currentlySelected.z > 0:
                self.currentlySelected.z -= 1
            elif self.wrapping:
                self.currentlySelected.z = self.z - 1
        elif direction == "Right":
            if self.currentlySelected.x < self.x - 1:
                self.currentlySelected.x += 1
            elif self.wrapping:
                self.currentlySelected.x = 0
        elif direction == "Left":
            if self.currentlySelected.x > 0:
                self.currentlySelected.x -= 1
            elif self.wrapping:
                self.currentlySelected.x = self.x - 1
        elif direction == "Up":
            if self.currentlySelected.y < self.y - 1:
                self.currentlySelected.y += 1
            elif self.wrapping:
                self.currentlySelected.y = 0
        elif direction == "Down":
            if self.currentlySelected.y > 0:
                self.currentlySelected.y -= 1
            elif self.wrapping:
                self.currentlySelected.y = self.y - 1

        if self.wrapping or old != self.currentlySelected:
            self.objects = []

    def getLayer(self, y):
        """Returns a slice of the 3d grid at level y, or None if y is out of bounds."""
        if y < 0 or y >= self.y:
            return None

        temp = self.generate2dGrid(self.x, self.z)
        for x in range(self.x):
            for z in range(self.z):
                temp[x][z] = self.grid[x][y][z]

        return temp

    def printGrid(self):
        """Prints the grid in 2d slices from lowest y to highest. Used for debugging."""
        for y in range(self.y):
            for z in range(self.z):
                for x in range(self.x):
                    print(self.grid[x][y][z], end="")
                print()
            print()
            print()

    def render(self, width, height):
        """Renders the current game-state to a canvas of dimensions width x height."""
        if self.render3d:
            return self.renderIn3d(width, height)
        else:
            return self.renderSideBySide(width, height)

    def draw_bg(self, canvas):
        """Fills canvas with tint of current player's colour."""
        bg = [255, 255, 255]
        if self.running and self.winner == -1:
            for i in range(3):
                bg[i] *= 0.95
                bg[i] += self.players[self.currentTurn].colour[i] * 0.05
                bg[i] = round(bg[i])
        canvas.fill(tuple(bg))

    def invertColour(self, colour):
        """Inverts given colour, currently unused."""
        newColour = []
        for i in range(len(colour)):
            newColour.append(255 - colour[i])
        return newColour

    def renderSideBySide(self, width, height):
        """Renders the game state as adjacent 2d slices to a canvas of dimensions width x height"""
        # determines which grids to render, keeping the currently selected grid in the middle unless that would result
        # in empty space.
        min_range = self.currentlySelected.y - math.floor(self.zoom2d / 2)
        max_range = self.currentlySelected.y + math.ceil(self.zoom2d / 2)
        if not self.wrapping:
            if min_range < 0:
                max_range -= min_range
                min_range = 0
            elif max_range > self.y:
                diff = self.y - max_range
                min_range += diff
                max_range += diff

        # grabs vertical slices
        grids = []
        for i in range(min_range, max_range):
            if i < 0 and self.wrapping:
                i += self.y
            elif i >= self.y and self.wrapping:
                i -= self.y
            grids.append(self.getLayer(i))

        canvas = pygame.Surface((width, height), pygame.SRCALPHA)
        self.draw_bg(canvas)

        # calculates what the largest the grid can be to fit {self.zoom2d} in view side by side.
        gridSize = min(width // self.zoom2d, height)
        # calculates gap at edges with the calculated size
        if gridSize == width // self.zoom2d:
            offset = (0, (height - gridSize) // 2)
        else:
            offset = ((width - gridSize * self.zoom2d) // 2, 0)

        # calculates what width the gridlines should be
        line_width = max(2, gridSize // 80)

        # calculates what size the markers should be
        markerSize = min(gridSize // self.x, gridSize // self.z) - 2 * line_width
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

            # calculates left and bottom boundaries of the ith grid
            gridLeft = gridOffset[0] + (gridSize + gridOffset[0]) * i + offset[0] + (2 * line_width)
            gridBottom = gridSize - gridOffset[1] - markerSize - (2 * line_width) + offset[1]

            for x in range(len(grid)):
                for y in range(len(grid[0])):
                    player = grid[x][y]

                    # boundary of 2d position
                    left = gridLeft + x * (markerSize + line_width)
                    top = gridBottom - y * (markerSize + line_width)
                    # if someone has played at (x, y), draw a square
                    if player != -1:
                        colour = self.players[player].colour
                        # if (x, y) is the currently selected space, draw a border to indicate
                        if self.draw_selected and (x, y) == (self.currentlySelected.x, self.currentlySelected.z) and i + min_range == self.currentlySelected.y:
                            pygame.draw.rect(canvas, self.players[self.currentTurn].colour, pygame.Rect(left, top, markerSize, markerSize))
                            pygame.draw.rect(canvas, colour,
                                             pygame.Rect(left + line_width * 4, top + line_width * 4, markerSize - line_width * 8,
                                                         markerSize - line_width * 8))
                        else:
                            pygame.draw.rect(canvas, colour, pygame.Rect(left, top, markerSize, markerSize))
                            # draw black square inside if part of winning line
                            if self.winner > -1 and Vector3d(x, i + min_range, y) in self.winningLine:
                                pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(left + markerSize // 4, top + markerSize // 4, markerSize // 2, markerSize // 2))
                    # if square hasn't been played at but is selected, draw border
                    elif self.draw_selected and (x, y) == (self.currentlySelected.x, self.currentlySelected.z) and i + min_range == self.currentlySelected.y:
                        pygame.draw.rect(canvas, self.players[self.currentTurn].colour,
                                         pygame.Rect(left, top, markerSize, markerSize))
                        pygame.draw.rect(canvas, (255, 255, 255),
                                         pygame.Rect(left + line_width * 4, top + line_width * 4,
                                                     markerSize - line_width * 8,
                                                     markerSize - line_width * 8))

            # draw gridlines
            top = gridBottom - (self.z - 1) * (markerSize + line_width)
            for x in range(1, len(grid)):
                left = gridLeft + x * (markerSize + line_width) - line_width
                pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(left, top, line_width, (markerSize + line_width) * self.z - line_width))

            for y in range(0, len(grid[0]) - 1):
                top = gridBottom - y * (markerSize + line_width) - line_width
                pygame.draw.rect(canvas, (0, 0, 0), pygame.Rect(gridLeft, top, (markerSize + line_width) * self.x - line_width, line_width))

        return canvas

    def renderIn3d(self, width, height):
        """Renders the game state as a 3d grid to a canvas of dimensions width x height"""
        def get_edge(x, y, z):
            return Position3d(x - 0.5, y - 0.5, z - 0.5) - centre

        # will attempt to lower details if performance drops too low, mainly lowering the number of objects to draw
        # for the gridlines. Chosen thresholds shouldn't cause too much flickering.
        if self.lod < 3:
            if self.lod == 2 and self.camera.clock.get_fps() < 15:
                self.lod += 1
                self.objects = []
            elif self.lod < 2 and 0 < self.camera.clock.get_fps() < 30:
                self.lod += 1
                self.objects = []
        if self.lod > 0:
            if self.lod == 3 and self.camera.clock.get_fps() > 140:
                self.lod -= 1
                self.objects = []
            elif self.lod < 3 and self.camera.clock.get_fps() > 70:
                self.lod -= 1
                self.objects = []

        canvas = pygame.Surface((width, height))
        self.draw_bg(canvas)

        # determines origin point
        if self.focus_centre or self.wrapping:
            x, y, z = (self.x - 1) / 2, (self.y - 1) / 2, (self.z - 1) / 2
        else:
            x, y, z = self.currentlySelected.x, self.currentlySelected.y, self.currentlySelected.z
        centre = Position3d(x, y * self.explosion, z)

        # cache objects, since only need to regenerate if gamestate, LoD or viewing options change.
        if not self.objects:
            rotation = Rotation3d(0, 0, 0)
            for x in range(self.x):
                for y in range(self.y):
                    for z in range(self.z):
                        index = self.grid[x][y][z]
                        indexSelected = Position3d(x, y, z) == self.currentlySelected and self.draw_selected
                        if index == -1 and not indexSelected:
                            continue

                        # calculates position to draw index at
                        if self.wrapping:
                            y1 = (y - self.currentlySelected.y + self.y // 2) % self.y
                            if self.focus_centre:
                                x1 = x
                                z1 = z
                            else:
                                x1 = (x - self.currentlySelected.x + self.x // 2) % self.x
                                z1 = (z - self.currentlySelected.z + self.z // 2) % self.z
                            position = Position3d(x1, y1 * self.explosion, z1) - centre
                        else:
                            position = Position3d(x, y * self.explosion, z) - centre

                        size = Vector3d(0.5, 0.5, 0.5)
                        if self.solid_cubes:
                            outline_width = 0.02
                        else:
                            outline_width = 0
                        outline_colour = (0, 0, 0)
                        colour = self.players[index].colour

                        if self.winner > -1 and Vector3d(x, y, z) in self.winningLine:
                            # if part of winning line, draw as opaque cube of winner's colour with thick black outline
                            outline_width = 0.15
                            size = Vector3d(0.4, 0.4, 0.4)
                            colour = (0, 0, 0)
                            outline_colour = self.players[self.winner].colour
                        elif indexSelected:
                            # if selected and empty, draw as colour cube with black outline
                            if index == -1:
                                colour = self.players[self.currentTurn].colour
                            else:
                                # if occupied, draw outline and colour depending on opaque rendering scheme
                                outline_colour = self.players[self.currentTurn].colour
                                if outline_width == 0:
                                    outline_colour, colour = colour, outline_colour
                            outline_width = 0.1
                        if outline_width > 0:
                            self.objects.append(Cuboid(position, size, rotation, colour, outline_width, outline_colour))
                        else:
                            self.objects.append(WireframeCuboid(position, size, rotation, colour, 45))

            colour = (0, 0, 0)
            thickness = 0.05
            yrange = [y * self.explosion for y in range(0, self.y)]

            # this could probably be refactored to look neater, but might not be worth the computational effort.
            # LoD Levels:
            #   0: Full cuboids, each segment rendered individually
            #   1: Two 2d faces making a + shape, each segment rendered individually.
            #       Looks very similar except when viewed length-wise, and reduced number of faces by factor of 2.
            #       Doesn't increase performance by much as also doubles object count, usually skipped to LoD 2
            #   2: One single face, each segment rendered individually
            #   3: One single face for an entire line
            #       Can cause weird artifacts near edges, especially with larger grids. Massive performance boost.

            # Possibly room for another level between 2 and 3, with one cuboid for entire line?
            # N.B. only vertical lines are drawn when using an exploded view.
            for x in range(1, self.x):
                for y in yrange[1:]:
                    if self.explosion == 1:
                        if self.lod < 3:
                            for z2 in range(0, self.z):
                                if self.lod == 0:
                                    position = get_edge(x, y, z2 + 0.5)
                                    size = Vector3d(thickness, thickness, 1)
                                    self.objects.append(Cuboid(position, size, rotation, colour))
                                else:
                                    p1 = get_edge(x, y, z2)
                                    p2 = get_edge(x, y, z2 + 1)
                                    self.objects.append(Line(p1, p2, thickness, Position3d(0, 1, 0), (0, 0, 0)))
                                    if self.lod == 1:
                                        self.objects.append(Line(p1, p2, thickness, Position3d(1, 0, 0), (0, 0, 0)))
                        else:
                            p1 = get_edge(x, y, 0)
                            p2 = get_edge(x, y, self.z)
                            self.objects.append(Line(p1, p2, thickness, Position3d(0, 1, 0), (0, 0, 0)))
                        for z in range(1, self.z):
                            if self.lod < 3:
                                for x2 in range(0, self.x):
                                    if self.lod == 0:
                                        position = get_edge(x2 + 0.5, y, z)
                                        size = Vector3d(1, thickness, thickness)
                                        self.objects.append(Cuboid(position, size, rotation, colour))
                                    else:
                                        p1 = get_edge(x2, y, z)
                                        p2 = get_edge(x2 + 1, y, z)
                                        self.objects.append(Line(p1, p2, thickness, Position3d(0, 1, 0), (0, 0, 0)))
                                        if self.lod == 1:
                                            self.objects.append(Line(p1, p2, thickness, Position3d(0, 0, 1), (0, 0, 0)))
                            else:
                                p1 = get_edge(0, y, z)
                                p2 = get_edge(self.x, y, z)
                                self.objects.append(Line(p1, p2, thickness, Position3d(0, 1, 0), (0, 0, 0)))
                for z in range(1, self.z):
                    if self.lod < 3 or self.explosion != 0:
                        for y2 in yrange:
                            if self.lod == 0:
                                position = get_edge(x, y2 + 0.5, z)
                                size = Vector3d(thickness, 1, thickness)
                                self.objects.append(Cuboid(position, size, rotation, colour))#
                            else:
                                p1 = get_edge(x, y2, z)
                                p2 = get_edge(x, y2 + 1, z)
                                self.objects.append(Line(p1, p2, thickness, Position3d(1, 0, 0), (0, 0, 0)))
                                if self.lod == 1:
                                    self.objects.append(Line(p1, p2, thickness, Position3d(0, 0, 1), (0, 0, 0)))
                    else:
                        p1 = get_edge(x, 0, z)
                        p2 = get_edge(x, self.y, z)
                        self.objects.append(Line(p1, p2, thickness, Position3d(1, 0, 0), (0, 0, 0)))

        # Draw the scene
        self.camera.render(canvas, self.objects, width, height)
        return canvas

    def start(self):
        self.currentlySelected = Position3d(0, 0, 0)
        self.running = True
        self.generatePlayerColours()
        self.objects = []


def applyResize(width, height):
    """Horrible function which resizes UI elements when window resized"""
    global windowX
    global windowY
    global screen
    global marginX
    global marginY
    margin = min(width // 6, height // 6)
    for button in buttons:
        button.rescale(max(width // 3, margin) / marginX, margin / marginY)
    for label in labels:
        label.rescale(max(width // 3, margin) / marginX, margin / marginY)
    windowX = math.ceil(width)
    windowY = math.ceil(height)
    marginX = max(width // 3, margin)
    marginY = margin
    for label in labels:
        label.scale(2 * marginX // 3, marginY // 3)
    screen = pygame.display.set_mode((windowX, windowY), pygame.RESIZABLE, 32)


borderX = 100
borderY = 20
fps_font = pygame.font.SysFont("Arial", 36, bold=True)

# default values
show_fps = False
x = 3
y = 3
z = 3
explosion = 1
numPlayers = 2
wrapping = False
players = [Player(), Player()]

while True:
    marginX = windowX // 3
    marginY = windowY // 6

    bWidth = marginX // 6
    bHeight = marginY // 3
    bHMargin = marginY // 6
    bWMargin = marginX // 12

    # button constants
    absYs = [bHMargin * (i + 1) + bHeight * 3 * (i) for i in range(5)]
    vals = [x, y, z, numPlayers, explosion]
    mins = [1, 1, 1, 2, 1]
    steps = [1, 1, 1, 1, 0.2]

    # generate buttons
    buttons = [IntegerButtons(colours["text"], colours["button"], colours["triButton"], bWidth, bHeight, bWMargin,
                              absYs[i], minValue=mins[i], value=vals[i], step=steps[i]) for i in range(5)]
    wrapping_button = Button("Wrapping: "+str(wrapping), colours["text"], colours["triButton"], bWidth*4, bHeight*2, marginX, windowY -bHeight*2-bHMargin)
    buttons.append(wrapping_button)

    # generate button labels
    text = ["Width", "Height", "Depth", "Players", "Explosion"]
    labels = [Text(text[i], colours["text"], absX=bWMargin * 2 + bWidth, absY=absYs[i]+bHeight) for i in range(5)]
    for label in labels:
        label.scale(2 * marginX // 3, bHeight)

    game = Match(x, y, z, explosion, players, wrapping, True)

    # event loop while in settings menu
    while not game.running:
        screen.fill((255, 255, 255))

        # draw buttons
        mousePos = pygame.mouse.get_pos()
        for button in buttons:
            button.checkHighlight(mousePos[0], mousePos[1])
            screen.blit(button.image, (button.absX, button.absY))
        for label in labels:
            screen.blit(label.image, (label.absX, label.absY))

        # draw game preview
        screen.blit(game.render(windowX - marginX, windowY - marginY), (marginX, 0))
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(marginX, 0, windowX - marginX, windowY - marginY), 3)

        game.camera.clock.tick()
        if show_fps:
            fps = str(int(game.camera.clock.get_fps()))+" / "+str(game.lod)
            fps_t = fps_font.render(fps, True, pygame.Color("RED"))
            screen.blit(fps_t, (0, 0))

        pygame.display.flip()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                applyResize(event.w, event.h)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i in range(len(buttons)):
                    if buttons[i].checkClick(event.button):
                        if i == 0:
                            x = buttons[i].value
                        elif i == 1:
                            y = buttons[i].value
                        elif i == 2:
                            z = buttons[i].value
                        elif i == 3:
                            numPlayers = buttons[i].value
                            players = [Player() for i in range(numPlayers)]
                        elif i == 4:
                            explosion = buttons[i].value
                        elif i == 5:
                            wrapping = not wrapping
                            wrapping_button.text.changeText("Wrapping: "+str(wrapping))
                            wrapping_button.draw()
                        game = Match(x, y, z, explosion, players, wrapping, True)
                        break
            elif event.type == pygame.KEYDOWN:
                if event.key == keybinds["Place"]:
                    game.start()
                elif event.key == keybinds["Toggle_FPS"]:
                    show_fps = not show_fps
            elif event.type == pygame.QUIT:
                exit()

    while game.running:
        screen.blit(game.render(windowX, windowY), (0, 0))
        game.camera.clock.tick()

        if show_fps:
            fps = str(int(game.camera.clock.get_fps()))+" / "+str(game.lod)
            fps_t = fps_font.render(fps, True, pygame.Color("RED"))
            screen.blit(fps_t, (0, 0))

        pygame.display.flip()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                applyResize(event.w, event.h)
            elif event.type == pygame.KEYDOWN and event.key == keybinds["Toggle_FPS"]:
                show_fps = not show_fps
            elif event.type == pygame.QUIT:
                exit()

        game.eventLoop(events)
