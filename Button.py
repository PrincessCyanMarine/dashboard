import pygame


class Button:
    def __init__(this, x, y, width, height, fun_and_args, useEvent=False):
        this.pos = this.x, this.y = x, y
        this.size = this.width, this.height = width, height
        this.fun, this.args = fun_and_args
        this.rect = pygame.Rect(x, y, width, height)
        this.useEvent = useEvent
        if not this.args:
            this.args = []

    def handleClick(this, event):
        if this.rect.collidepoint(event.pos):
            if this.useEvent:
                this.fun(*this.args, event)
            else:
                this.fun(*this.args)
            return True
        return False

    def draw(this, color):
        s = pygame.Surface(this.size, pygame.SRCALPHA)
        s.fill(color)
        pygame.display.get_surface().blit(s, this.pos)


def createButton(x, y, w, h, fun, args=None, useEvent=False, color=None, priority=False):
    button = Button(x, y, w, h, (fun, args), useEvent)
    if priority:
        global buttons
        buttons = [button] + buttons
    else:
        buttons.append(button)
    if color:
        button.draw(color)


def getButtons():
    return buttons


buttons = []


def clearButtons():
    global buttons
    buttons = []


toggledButtons = []


def addToggledButton(fun):
    toggledButtons.append(fun)


def tickToggleButtons():
    if not pygame.mouse.get_pressed()[0]:
        releaseToggleButtons()
    if pygame.mouse.get_focused():
        for fun in toggledButtons:
            fun[0]()


def clearToggleButtons():
    global toggledButtons
    toggledButtons = []


def releaseToggleButtons():
    for fun in toggledButtons:
        if len(fun) > 1:
            fun[1]()
    clearToggleButtons()


def handleButtons(event):
    for button in buttons:
        if button.handleClick(event):
            break
