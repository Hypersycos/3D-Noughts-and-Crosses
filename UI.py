import random

import pygame
import pygame.gfxdraw

colours = {"text": (255, 255, 255), "button": (100, 150, 200, 180), "textbox": (50, 50, 50, 180)}


class Button:
    def __init__(self, text, textcolour, colour, width, height, absX, absY, font='Comic Sans MS'):
        self.text = Text(text, textcolour, font)
        self.text.scale(width, height)
        try:
            colour[3] == 0
        except:
            colour = (colour[0], colour[1], colour[2], 255)
        self.colour = colour
        self.renderColour = colour
        self.width = width
        self.height = height
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.absX = absX
        self.absY = absY
        self.draw()

    def rescale(self, xScale, yScale):
        self.width = self.width * xScale
        self.height = self.height * yScale
        self.absX = self.absX * xScale
        self.absY = self.absY * yScale
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.text.scale(self.width, self.height)
        self.draw()

    def draw(self):
        self.image.fill(self.renderColour)
        w, h = self.text.font.size(self.text.text)
        w, h = (self.width - w) // 2, (self.height - h) // 2
        self.image.blit(self.text.image, (w, h))

    def checkHighlight(self, mouseX, mouseY):
        h = .75
        if mouseX > self.absX and mouseX < self.absX + self.width and mouseY > self.absY and mouseY < self.absY + self.height:
            if self.renderColour == self.colour:
                self.renderColour = (self.colour[0] * h, self.colour[1] * h, self.colour[2] * h, self.colour[3])
                self.draw()
        else:
            if not self.renderColour == self.colour:
                self.renderColour = self.colour
                self.draw()

    def checkClick(self, button_type):
        return self.renderColour != self.colour


class IntegerButtons:
    def __init__(self, textColour, boxColour, buttonColour, buttonWidth, buttonHeight, absX, absY, isVertical=True,
                 maxValue=None, minValue=1, value=3, step=1):
        self.textColour = textColour
        self.boxColour = boxColour
        self.buttonColour = buttonColour
        self.buttonWidth = buttonWidth
        self.buttonHeight = buttonHeight
        self.absX = absX
        self.absY = absY
        self.isVertical = isVertical
        self.maxValue = maxValue
        self.minValue = minValue
        self.value = value
        self.step = step
        self.intValue = round(self.value / self.step)
        self.setup()

    def setup(self):
        if self.isVertical:
            margin = int(self.buttonHeight * 0.1)
            self.image = pygame.Surface((self.buttonWidth, self.buttonHeight * 3 + margin * 2), pygame.SRCALPHA)
            self.buttons = [TriangleButton(self.buttonColour, self.buttonWidth, self.buttonHeight, 0, 0),
                            TextBox(self.textColour, self.boxColour, self.buttonWidth, self.buttonHeight, 0,
                                    margin + self.buttonHeight, str(self.value)),
                            TriangleButton(self.buttonColour, self.buttonWidth, self.buttonHeight, 0,
                                           2 * (margin + self.buttonHeight), "down")]
        else:
            margin = int(self.buttonWidth * 0.1)
            self.image = pygame.Surface((self.buttonWidth * 3 + margin * 2, self.buttonHeight), pygame.SRCALPHA)
            self.buttons = [TriangleButton(self.buttonColour, self.buttonWidth, self.buttonHeight, 0, 0, "left"),
                            TextBox(self.textColour, self.boxColour, self.buttonWidth, self.buttonHeight,
                                    margin + self.buttonWidth, 0, str(self.value)),
                            TriangleButton(self.buttonColour, self.buttonWidth, self.buttonHeight,
                                           2 * (margin + self.buttonWidth), 0, "right")]

        self.draw()

    def draw(self):
        self.image.fill((0, 0, 0, 0))
        for button in self.buttons:
            self.image.blit(button.image, (button.absX, button.absY))

    def rescale(self, xScale, yScale):
        self.buttonWidth *= xScale
        self.buttonHeight *= yScale
        self.absX = self.absX * xScale
        self.absY = self.absY * yScale
        self.setup()

    def checkHighlight(self, mouseX, mouseY):
        relX, relY = mouseX - self.absX, mouseY - self.absY
        for button in self.buttons:
            button.checkHighlight(relX, relY)
        self.draw()

    def update(self):
        self.value = self.step * self.intValue
        if self.value < self.minValue:
            self.value = self.minValue
        elif self.maxValue is not None and self.value > self.maxValue:
            self.value = self.maxValue
        self.intValue = round(self.value / self.step)
        precision = 1
        step = self.step
        while step % 1 != 0:
            precision *= 10
            step *= 10
        if precision == 1:
            self.buttons[1].text.text = str(self.value)
        else:
            self.buttons[1].text.text = str(round(self.value*precision)/precision)
        self.buttons[1].text.scale(self.buttons[1].width, self.buttons[1].height)
        self.buttons[1].draw()
        self.draw()

    def checkClick(self, button_type):
        if button_type == 1:
            for button in self.buttons[0::2]:
                if button.renderColour != button.colour:
                    if button == self.buttons[0]:
                        self.intValue += 1
                    else:
                        self.intValue -= 1
                    self.update()
                    return True
        elif 4 <= button_type <= 5:
            for button in self.buttons:
                if button.renderColour != button.colour:
                    if button_type == 4:
                        self.intValue += 1
                    else:
                        self.intValue -= 1
                    self.update()
                    return True

        return False


class TriangleButton(Button):
    def __init__(self, colour, width, height, absX, absY, direction="up"):
        try:
            colour[3] == 0
        except:
            colour = (colour[0], colour[1], colour[2], 255)
        self.colour = colour
        self.renderColour = colour
        self.width = width
        self.height = height
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.absX = absX
        self.absY = absY
        self.direction = direction
        self.draw()

    def rescale(self, xScale, yScale):
        self.width = self.width * xScale
        self.height = self.height * yScale
        self.absX = self.absX * xScale
        self.absY = self.absY * yScale
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.draw()

    def draw(self):
        self.image.fill((0, 0, 0, 0))
        if self.direction == "up":
            coords = [(0, self.height), (self.width, self.height), (self.width // 2, 0)]
        elif self.direction == "down":
            coords = [(0, 0), (self.width, 0), (self.width // 2, self.height)]
        elif self.direction == "left":
            coords = [(self.width, 0), (self.width, self.height), (0, self.height // 2)]
        else:
            coords = [(0, 0), (0, self.height), (self.width, self.height // 2)]
        pygame.gfxdraw.aapolygon(self.image, coords, self.renderColour)
        pygame.draw.polygon(self.image, self.renderColour, coords)


class Text:
    def __init__(self, text, colour, fontName='Comic Sans MS', absX=0, absY=0):
        self.fontName = fontName
        self.text = text
        self.colour = colour
        self.textSize = 12
        self.absX = absX
        self.absY = absY
        self.Font()
        self.render()

    def getDimensions(self):
        return self.font.size(self.text)

    def pos(self, x, y):
        self.absX = x
        self.absY = y

    def rescale(self, xScale, yScale):
        self.absX = self.absX * xScale
        self.absY = self.absY * yScale
        self.render()

    def scale(self, width, height):
        i = 1
        j = 0
        w = 0
        h = 0
        while w < width and h < height:
            j = i
            i += i
            self.font = pygame.font.SysFont(self.fontName, i)
            w, h = self.font.size(self.text)
        while i - j > 1:
            self.font = pygame.font.SysFont(self.fontName, (i + j) // 2)
            w, h = self.font.size(self.text)
            if w > width or h > height:
                i = (i + j) // 2
            else:
                j = (i + j) // 2
        self.textSize = j
        self.Font()
        self.render()

    def Font(self):
        self.font = pygame.font.SysFont(self.fontName, self.textSize)

    def setFontName(self, fontName):
        self.fontName = fontName
        self.Font()
        self.render()

    def setFontSize(self, size):
        self.textSize = size
        self.Font()
        self.render()

    def setFont(self, fontName, size):
        self.fontName = fontName
        self.size = size
        self.Font()
        self.render()

    def render(self):
        self.image = self.font.render(self.text, True, self.colour)

    def changeText(self, text):
        self.text = text
        self.render()

    def recolour(self, colour):
        self.colour = colour
        self.render()


class TextBox(Button):
    def __init__(self, textcolour, colour, width, height, absX, absY, text="", validCharacters='0123456789',
                 charLimit=0, font='Comic Sans MS'):
        super().__init__(text, textcolour, colour, width, height, absX, absY, font)
        self.charLimit = charLimit
        self.validCharacters = list(validCharacters)
        self.selected = False
        h = 0.75
        s = 1.25
        self.highlightColour = (
        min(self.colour[0] * h, 255), min(self.colour[1] * h, 255), min(self.colour[2] * h, 255),
        min(self.colour[3], 255))
        self.selectColour = (self.colour[0] * s, self.colour[1] * s, self.colour[2] * s, self.colour[3])

    def click(self):
        if self.selected:
            self.selected = False
        else:
            self.selected = True
        return self.selected

    def checkHighlight(self, mouseX, mouseY):
        if mouseX > self.absX and mouseX < self.absX + self.width and mouseY > self.absY and mouseY < self.absY + self.height:
            if self.renderColour in [self.colour, self.selectColour]:
                self.renderColour = self.highlightColour
                self.draw()
        else:
            if self.selected:
                self.renderColour = self.selectColour
            else:
                self.renderColour = self.colour
            self.draw()

    def typing(self, typed):
        if typed == "back":
            self.text.text = self.text.text[:-1]
        else:
            if (typed.lower() in self.validCharacters or self.validCharacters == []) and (
                    len(self.text.text) < self.charLimit or self.charLimit == 0):
                self.text.text = self.text.text + typed
        self.text.scale(self.width, self.height)
        self.draw()
