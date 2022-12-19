import json
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
import re
import sys

from math import floor
from time import sleep, time

from datetime import datetime
from threading import Thread
from types import NoneType

from Button import *
from config import *
from constants import *
from FileManager import *
from pygame.locals import *


should_exit = False

cpu = None
memory = None
_processes = None
release = ""
longest_user = 0
process_offset = 0
selected_pid = None
start_process = 0
follow_mode = False
fetching = False
current_tab = INITIAL_TAB


# print(CONFIG["UPDATE_DISPLAY_EVERY_X_SECONDS"], 1 / CONFIG["UPDATE_DISPLAY_EVERY_X_SECONDS"])


def fetchMemory():
    def translate(str):
        z = re.match(
            ".+?([0-9]+)\s+?([0-9]+)\s*([0-9]+)\s*([0-9]*)?\s*([0-9]*)?\s*([0-9]*)?",
            str,
        )
        if z:
            groups = z.groups()
            return {
                "total": int(groups[0] or "0"),
                "used": int(groups[1] or "0"),
                "free": int(groups[2] or "0"),
                "percentage": int(groups[1] or "0") / int(groups[0] or "0"),
                "shared": int(groups[3] or "0"),
                "cache": int(groups[4] or "0"),
                "available": int(groups[5] or "0"),
            }

    global memory, should_exit
    # while not should_exit:
    mem = os.popen("free -k").readlines()
    memory = (translate(mem[1]), translate(mem[2]))


def fetchProcesses():
    def translate(str):
        z = re.match(
            "^(\S+?)\s+([0-9]+?)\s+([0-9]{1,3}\.[0-9]{1,3})\s+([0-9]{1,3}\.[0-9]{1,3})\s+([0-9]+?)\s+?([0-9]+?)\s+?(\S+?)\s+(\S+?)\s+?(\S+?)\s+?(\S+?)\s+?(.+?)$",
            str,
        )
        if z:
            groups = z.groups()
            return {
                "user": groups[0],
                "pid": groups[1],
                "cpu": float(groups[2]),
                "mem": float(groups[3]),
                "command": groups[10],
            }

    global _processes, should_exit
    # while not should_exit:
    p = os.popen("ps aux").readlines()
    del p[0]
    _processes = list(map(translate, p))
    _longest_user = 0
    for p in _processes:
        if type(p) is dict and len(p["user"]) > _longest_user:
            _longest_user = len(p["user"])
    global longest_user
    longest_user = _longest_user


def fetchCPU():
    global cpu, should_exit
    # while not should_exit:
    cpu = (
        100.0 - float(os.popen("echo $(vmstat 1 2|tail -1|awk '{print $15}')").read())
    ) / 100.0


def runFetchThreads():
    global should_exit, fetching
    fetching = True
    while not should_exit:
        if CONFIG["ONLY_FETCH_ON_TASK_MANAGER"] and current_tab != "task":
            break

        threads = (
            Thread(target=fetchMemory),
            Thread(target=fetchProcesses),
            Thread(target=fetchCPU),
        )
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        if CONFIG["LOGGING"]:
            sortedCpu = _processes[0:3]
            sortedCpu.sort(key=sortByCPU, reverse=True)
            sortedMem = _processes[0:3]
            sortedMem.sort(key=sortByMem, reverse=True)

            j = json.dumps(
                {
                    "memory": memory,
                    "cpu": cpu,
                    "processesByCPU": sortedCpu,
                    "processesByMemory": sortedMem,
                    "time": time() * 1000,
                }
            )
            with open("log.json", "a") as logger:
                logger.write("\n" + j)

        if CONFIG["UPDATE_FETCHER_EVERY_X_SECONDS"] > 0:
            sleep(CONFIG["UPDATE_FETCHER_EVERY_X_SECONDS"])

    fetching = False


def sortByCPU(p):
    return p.get("cpu") if type(p) is dict else 0


def sortByMem(p):
    return p.get("mem") if type(p) is dict else 0


def sortByPID(p):
    return int(p.get("pid")) if type(p) is dict else 0


def setProcessOffset(value):
    global process_offset
    process_offset = value


def changeSortingMode(mode):
    setProcessOffset(0)

    def toggle(a, b):
        global active_sorting
        if active_sorting == a:
            active_sorting = b
        else:
            active_sorting = a

    match mode:
        case "cpu":
            toggle(SORTING_METHODS.CPU_DESCENDING, SORTING_METHODS.CPU_ASCENDING)
        case "mem":
            toggle(SORTING_METHODS.MEM_DESCENDING, SORTING_METHODS.MEM_ASCENDING)
        case "pid":
            toggle(SORTING_METHODS.PID_ASCENDING, SORTING_METHODS.PID_DESCENDING)


def getSortingProcesses():
    global active_sorting
    match active_sorting:
        case SORTING_METHODS.CPU_ASCENDING:
            return (sortByCPU, False)
        case SORTING_METHODS.CPU_DESCENDING:
            return (sortByCPU, True)
        case SORTING_METHODS.MEM_ASCENDING:
            return (sortByMem, False)
        case SORTING_METHODS.MEM_DESCENDING:
            return (sortByMem, True)
        case SORTING_METHODS.PID_ASCENDING:
            return (sortByPID, False)
        case SORTING_METHODS.PID_DESCENDING:
            return (sortByPID, True)
        # case SORTING_METHODS._ASCENDING: return (sortBy, False)
        # case SORTING_METHODS._DESCENDING: return (sortBy, True)


def replaceString(str, char, index):
    return str[0:index] + char + str[index + 1 : len(str)]


def handleKeys():
    wait_for = 0
    while not should_exit:
        global process_offset, selected_pid, _processes
        processes = _processes
        keys = pygame.key.get_pressed()
        if keys[K_UP]:
            process_offset -= 1
            if process_offset < 0:
                process_offset = 0
                # process_offset = len(processes) - 1
            selected_pid = (
                processes[process_offset]["pid"]
                if not type(processes[process_offset]) is NoneType
                else None
            )
            wait_for = 100
        elif keys[K_DOWN]:
            process_offset += 1
            if process_offset >= len(processes):
                process_offset = len(processes) - 1
            #     process_offset = 0
            selected_pid = (
                processes[process_offset]["pid"]
                if not type(processes[process_offset]) is NoneType
                else None
            )
            wait_for = 100
        while wait_for > 0:
            wait_for -= 1
            sleep(0.001)


def getProcessesHeader():
    header = ("   CPU%     MEM%   " + "USER".ljust(longest_user) + "  COMMAND ").ljust(
        int(SCREEN_WIDTH / TEXT_WIDTH) - 7
    ) + "PID"
    if active_sorting == SORTING_METHODS.CPU_ASCENDING:
        return replaceString(header, "▲", 1)
    elif active_sorting == SORTING_METHODS.CPU_DESCENDING:
        return replaceString(header, "▼", 1)
    elif active_sorting == SORTING_METHODS.MEM_ASCENDING:
        return replaceString(header, "▲", 10)
    elif active_sorting == SORTING_METHODS.MEM_DESCENDING:
        return replaceString(header, "▼", 10)
    elif active_sorting == SORTING_METHODS.PID_ASCENDING:
        return replaceString(header, "▲", len(header) - 5)
    elif active_sorting == SORTING_METHODS.PID_DESCENDING:
        return replaceString(header, "▼", len(header) - 5)


def kill():
    global _processes, selected_pid, follow_mode, process_offset
    processes = _processes
    selected = None
    if follow_mode:
        selected = selected_pid
    else:
        selected = (
            processes[process_offset]["pid"]
            if not type(processes[process_offset]) is NoneType
            else None
        )
    if not selected:
        return

    os.popen("kill -9 " + str(selected))


def selectProcess(i, pid, event):
    global follow_mode, selected_pid, process_offset
    pressed = event.button

    if pressed == 3 or pressed == 2:
        follow_mode = True
        selected_pid = pid
    elif pressed == 1:
        follow_mode = False
        process_offset = i

    if pressed == 2:
        kill()
        follow_mode = False
        process_offset = i


def changePage(page):
    global process_offset, start_process, selected_pid
    process_offset = start_process = page
    selected_pid = None


def pageDown():
    changePage(
        min(len(_processes) if _processes else 0, start_process + max_processes - 1)
    )


def pageUp():
    changePage(max(0, start_process - max_processes))


def move(processes, off):
    global process_offset, selected_pid
    process_offset = min(len(processes) - 1, max(0, process_offset + off))
    selected_pid = (
        processes[process_offset]["pid"]
        if not type(processes[process_offset]) is NoneType
        else None
    )


def moveUp(processes):
    move(processes, -1)


def moveDown(processes):
    move(processes, 1)


def tabChange(tab):
    global current_tab
    current_tab = tab


def drawTabs(tabs):
    footer_start = DRAWING_AREA_BOTTOM
    fill(0, footer_start, SCREEN_WIDTH, FOOTER_SIZE - TEXT_HEIGHT, COLORS["TOP_BAR"])
    x = 0
    for tab in tabs:
        if len(tab) < 3 or tab[2]:
            createButton(
                x,
                footer_start,
                TEXT_WIDTH * (len(tab[1]) + 4),
                TEXT_HEIGHT * 3,
                tabChange,
                (tab[0],),
                False,
                COLORS["BACKGROUND"]
                if current_tab == tab[0]
                else COLORS["FOOTER_BUTTONS"],
            )
            write(tab[1], x + TEXT_WIDTH * 2, footer_start + TEXT_HEIGHT)
            x += (len(tab[1]) + 5) * TEXT_WIDTH


def fill(left, top, width, height, color, surface=None):
    if surface == None:
        surface = pygame.display.get_surface()
    pygame.draw.rect(surface, color, (left, top, width, height))


def write(text, x, y, surface=None):
    if surface == None:
        surface = screen
    TEXT_FONT.render_to(surface, (x, y), text, COLORS["TEXT"])
    return x + (len(text) * TEXT_WIDTH)


def writeRight(text, y, scroll=False, surface=None):
    x = SCREEN_WIDTH - len(text) * TEXT_WIDTH - TEXT_WIDTH
    if scroll:
        x -= TEXT_WIDTH * 2
    write(text, x, y)


def writeCenteredHorizontal(text, y, surface=None):
    w = SCREEN_WIDTH if surface == None else surface.get_width()
    write(text, (w / 2) - ((len(text) * TEXT_WIDTH) / 2), y, surface)


def writeCentered(text, surface=None):
    w = SCREEN_WIDTH if surface == None else surface.get_width()
    h = SCREEN_HEIGHT if surface == None else surface.get_height()
    write(
        text,
        (w / 2) - ((len(text) * TEXT_WIDTH) / 2),
        (h / 2) - (TEXT_HEIGHT / 2),
        surface,
    )


def getBarColor(percentage):
    if percentage < 0.35:
        return COLORS["GREEN"]
    elif percentage < 0.75:
        return COLORS["YELLOW"]
    else:
        return COLORS["RED"]


def writeMem(mem, txt, y):
    def form(n):
        return " %.2f" % (n / 1.049e6)

    if not mem:
        mem = {"percentage": -1, "used": 0, "total": 0}

    writePercentage(
        mem["percentage"],
        txt + form(mem["used"]) + "/" + form(mem["total"]),
        y,
    )


def writePercentage(percentage, text, y):
    global SCREEN_WIDTH
    percentage_text = (
        "%0.2f" % (percentage * 100) + "%" if percentage >= 0 else "??.??%"
    ).rjust(7)

    if CONFIG["PERCENTAGE_BEFORE_BAR"]:
        text = text + "    " + percentage_text
    else:
        writeRight(percentage_text, y)

    start_pos = (len(text) + 3) * TEXT_WIDTH
    bar_size = SCREEN_WIDTH - start_pos - TEXT_WIDTH
    if not CONFIG["PERCENTAGE_BEFORE_BAR"]:
        bar_size -= 10 * TEXT_WIDTH
    write(text, 10, y)
    fill(start_pos, y, bar_size, TEXT_HEIGHT, COLORS["GREY"])
    fill(start_pos, y, bar_size * percentage, TEXT_HEIGHT, getBarColor(percentage))


def drawScrollBar(pos, max_value, y=None, height=None, fun=None):
    if y == None:
        y = DRAWING_AREA_TOP - HALF_TEXT_HEIGHT
    if height == None:
        height = DRAWING_AREA_SIZE + HALF_TEXT_HEIGHT
    x = SCREEN_WIDTH - TEXT_WIDTH
    fill(
        x,
        y,
        TEXT_WIDTH,
        height,
        COLORS["SCROLL_BACKGROUND"],
    )
    thumb_size = height / (max_value + 1)
    fill(
        x,
        y + pos * thumb_size,
        TEXT_WIDTH,
        thumb_size,
        COLORS["SCROLL_THUMB"],
    )
    if fun != None:

        def calc():
            relative_clicked_pos = max(0, min(pygame.mouse.get_pos()[1] - y, height))
            fun(floor((relative_clicked_pos / height) * (max_value + 1)))

        def onClicked():
            addToggledButton([calc])

        createButton(x, y, TEXT_WIDTH, height, onClicked, None, False, None, True)


# main
for i in range(0, len(sys.argv)):
    arg = sys.argv[i]
    next_arg = sys.argv[i + 1] if i < len(sys.argv) - 1 else None
    if arg == "-h":
        print()
        print("-b x: Fetches info every x seconds")
        print("-f x: Updates display every x seconds")
        print("-fps x: Sets the fps to x (Same as -f 1/x)")
        print("-p: Writes percentages before their bars")
        print("-t x: Sets window title to x")
        print("-l: Activates logging")
        print("-d: Debug mode")
        print()
        should_exit = True
        sys.exit()
    elif arg == "-b":
        if next_arg:
            CONFIG["UPDATE_FETCHER_EVERY_X_SECONDS"] = float(next_arg)
    elif arg == "-f":
        if next_arg:
            CONFIG["UPDATE_DISPLAY_EVERY_X_SECONDS"] = float(next_arg)
    elif arg == "-fps":
        if next_arg:
            CONFIG["UPDATE_DISPLAY_EVERY_X_SECONDS"] = 1 / float(next_arg)
    elif arg == "-p":
        CONFIG["PERCENTAGE_BEFORE_BAR"] = True
    elif arg == "-t":
        if next_arg:
            CONFIG["TITLE"] = next_arg
    elif arg == "-l":
        CONFIG["LOGGING"] = True
    elif arg == "-d":
        CONFIG["DEBUG"] = True

match = re.search('PRETTY_NAME="(.+?)"', os.popen("cat /etc/os-release").read())
if match:
    release = match.groups()[0] + " " + os.popen("uname -p").read()
    release = release[0 : len(release) - 1]

pygame.init()
pygame.font.init()
TEXT_FONT = pygame.freetype.Font("assets/fonts/DejaVuSansMono.ttf", TEXT_HEIGHT)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), RESIZABLE)
pygame.display.set_caption(CONFIG["TITLE"])

Icon = pygame.image.load("assets/images/icon.png")
pygame.display.set_icon(Icon)

active_sorting = SORTING_METHODS.CPU_DESCENDING

processes = None
while not should_exit:
    tickToggleButtons()
    shouldDrawTabs = True

    if not fetching:
        Thread(target=runFetchThreads).start()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            should_exit = True
            sys.exit()
        elif event.type == pygame.VIDEORESIZE:
            SCREEN_WIDTH, SCREEN_HEIGHT = event.size

            DRAWING_AREA_BOTTOM = SCREEN_HEIGHT - FOOTER_SIZE + TEXT_HEIGHT
            DRAWING_AREA_SIZE = DRAWING_AREA_BOTTOM - DRAWING_AREA_TOP

            FITTING_TEXT_WIDTH, FITTING_TEXT_HEIGHT = int(
                SCREEN_WIDTH / TEXT_WIDTH
            ), int(SCREEN_HEIGHT / TEXT_HEIGHT)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            releaseToggleButtons()
            act = False
            for p in pygame.mouse.get_pressed():
                if p:
                    act = True
                    break
            if act:
                handleButtons(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            releaseToggleButtons()

        elif current_tab == "task":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    changeSortingMode("cpu")
                elif event.key == pygame.K_m:
                    changeSortingMode("mem")
                elif event.key == pygame.K_p:
                    changeSortingMode("pid")
                elif event.key == pygame.K_PAGEDOWN:
                    pageDown()
                elif event.key == pygame.K_PAGEUP:
                    pageUp()
                elif event.key == pygame.K_HOME:
                    process_offset = start_process = 0
                    selected_pid = None
                elif event.key == pygame.K_END:
                    process_offset = start_process = len(processes) - max_processes + 1
                    selected_pid = None
                elif event.key == pygame.K_f:
                    follow_mode = not follow_mode
                elif event.key == pygame.K_UP:
                    moveUp(processes)
                elif event.key == pygame.K_DOWN:
                    moveDown(processes)
                elif event.key == pygame.K_k:
                    kill()
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    moveUp(processes)
                elif event.y < 0:
                    moveDown(processes)
        elif current_tab == "file":
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    setFileExplorerOffset(max(0, getFileExplorerOffset() - 1))
                elif event.y < 0:
                    setFileExplorerOffset(
                        min(
                            getFileLines() * TEXT_HEIGHT * 4,
                            getFileExplorerOffset() + 1,
                        )
                    )
            elif event.type == pygame.KEYDOWN:
                if len(getSelectedFiles()) > 0:

                    if event.key == K_ESCAPE:
                        clearSelectedFiles()
                    elif event.key == K_DELETE:
                        deleteSelectedFiles()
                    elif event.key == K_x:
                        moveSelectedFiles()
                    elif event.key == K_c:
                        copySelectedFiles()

        if event.type == pygame.MOUSEBUTTONDOWN and current_tab == "file":
            if event.button == 6:
                filePathBack()
            elif event.button == 7:
                filePathFowards()

    setFileExplorerOffset(min(getFileLines(), max(0, getFileExplorerOffset())))

    screen.fill(COLORS["BACKGROUND"])
    fill(0, 0, SCREEN_WIDTH, TEXT_HEIGHT * 2, COLORS["TOP_BAR"])

    # if CONFIG["DEBUG"]:
    #     for button in buttons:
    #         s = pygame.Surface(button.size, pygame.SRCALPHA)  # per-pixel alpha
    #         s.fill(COLORS["REDISH_GREY"])  # notice the alpha value in the color
    #         screen.blit(s, button.pos)

    date = datetime.now()
    time_string = "%02d/%02d/%04d, %02d:%02d:%02d" % (
        date.day,
        date.month,
        date.year,
        date.hour,
        date.minute,
        date.second,
    )
    write(release, 10, HALF_TEXT_HEIGHT)
    writeRight(time_string, HALF_TEXT_HEIGHT)

    clearButtons()
    y = DRAWING_AREA_TOP
    if current_tab == "task":
        for line in (
            (writePercentage, (cpu or -1, "cpu")),
            (writeMem, (memory[0] if memory else None, "mem")),
            (writeMem, (memory[1] if memory else None, "swp")),
        ):
            line[0](*line[1], y)
            y += TEXT_HEIGHT + HALF_TEXT_HEIGHT

        processes = _processes
        if processes:
            processes_len = len(processes)

            if process_offset >= processes_len:
                process_offset = processes_len - 1
            if start_process > processes_len:
                start_process = processes_len - 1

            processes_header = getProcessesHeader()

            y += 10
            write(processes_header, 10, y)

            createButton(
                TEXT_WIDTH,
                y - HALF_TEXT_HEIGHT,
                8 * TEXT_WIDTH,
                TEXT_HEIGHT + HALF_TEXT_HEIGHT + QUARTER_TEXT_HEIGHT,
                changeSortingMode,
                ("cpu",),
            )

            createButton(
                10 * TEXT_WIDTH,
                y - HALF_TEXT_HEIGHT,
                8 * TEXT_WIDTH,
                TEXT_HEIGHT + HALF_TEXT_HEIGHT + QUARTER_TEXT_HEIGHT,
                changeSortingMode,
                ("mem",),
            )

            createButton(
                SCREEN_WIDTH - 7 * TEXT_WIDTH,
                y - HALF_TEXT_HEIGHT,
                7 * TEXT_WIDTH,
                TEXT_HEIGHT + HALF_TEXT_HEIGHT + QUARTER_TEXT_HEIGHT,
                changeSortingMode,
                ("pid",),
            )

            y += TEXT_HEIGHT + HALF_TEXT_HEIGHT
            scrollbar_start = y

            sorting = getSortingProcesses()
            processes.sort(key=sorting[0], reverse=sorting[1])

            if follow_mode:
                if not selected_pid:
                    selected_pid = (
                        processes[process_offset]["pid"]
                        if not type(processes[process_offset]) is NoneType
                        else None
                    )
                else:
                    for i in range(0, processes_len):
                        if type(processes[i]) is NoneType:
                            continue
                        if selected_pid == processes[i]["pid"]:
                            process_offset = i
                            break

                        if i == processes_len - 1:
                            selected_pid = None

            # for i in range(process_offset, processes_len):

            max_processes = round(
                (SCREEN_HEIGHT - y - FOOTER_SIZE) / (TEXT_HEIGHT + HALF_TEXT_HEIGHT)
            )

            if process_offset < start_process:
                start_process = process_offset
            elif process_offset > max_processes + start_process - 1:
                start_process = process_offset - max_processes + 1

            for i in range(
                max(0, start_process), min(max_processes + start_process, processes_len)
            ):
                if i > len(processes) or i < 0:
                    break
                process = processes[i]
                if type(process) is not dict:
                    continue
                if follow_mode:
                    if process["pid"] == selected_pid:
                        fill(
                            0,
                            y,
                            SCREEN_WIDTH,
                            TEXT_HEIGHT,
                            COLORS["BLUEISH_GREY"],
                        )
                elif i == process_offset:
                    fill(
                        0,
                        y,
                        SCREEN_WIDTH,
                        TEXT_HEIGHT,
                        COLORS["DARK_GREY"],
                    )
                createButton(
                    0,
                    y - QUARTER_TEXT_HEIGHT,
                    SCREEN_WIDTH,
                    TEXT_HEIGHT + HALF_TEXT_HEIGHT,
                    selectProcess,
                    (i, process["pid"]),
                    True,
                )
                write(("%04.2f" % process["cpu"] + "%").rjust(7), 10, y)
                write(("%04.2f" % process["mem"] + "%").rjust(7), 10 * TEXT_WIDTH, y)
                write(process["user"], 20 * TEXT_WIDTH, y)
                c_pos = 22 + longest_user
                c_len = FITTING_TEXT_WIDTH - (c_pos + len(process["pid"]) + 7)
                if len(process["command"]) > c_len:
                    command = process["command"][0 : c_len - 3] + "..."
                else:
                    command = process["command"]
                write(command, c_pos * TEXT_WIDTH, y)
                writeRight(process["pid"], y, True)
                y += TEXT_HEIGHT + HALF_TEXT_HEIGHT
                # if y + TEXT_HEIGHT >= SCREEN_HEIGHT:
                #     break
            #  drawScrollBar(
            #     process_offset / max_processes,
            #     (processes_len - 2) / max_processes,
            #     scrollbar_start,
            #     DRAWING_AREA_SIZE - scrollbar_start + DRAWING_AREA_TOP,
            #     lambda x: setProcessOffset(x * max_processes),
            # )
            drawScrollBar(
                process_offset,
                (processes_len - 2),
                scrollbar_start,
                DRAWING_AREA_SIZE - scrollbar_start + DRAWING_AREA_TOP,
                setProcessOffset,
            )
    elif current_tab == "file":
        files = ls()
        while len(files) == 0:
            cd("..")
            files = ls()

        setFileLines(0)
        x = TEXT_WIDTH
        y -= getFileExplorerOffset() * TEXT_HEIGHT * 4
        for file in files:
            size = w, h = TEXT_WIDTH * (len(file.name) + 2), TEXT_HEIGHT * 3

            if x + w >= SCREEN_WIDTH - TEXT_WIDTH * 2:
                y += TEXT_HEIGHT * 4
                x = TEXT_WIDTH
                addFileLine()

            if y >= DRAWING_AREA_TOP and y + h < DRAWING_AREA_BOTTOM:
                surface = pygame.Surface(size)
                if getFileSelectedPos(file) == -1:
                    if file.isDir():
                        surface.fill(COLORS["GRAPH_BACKGROUND"])
                    else:
                        surface.fill(COLORS["FOOTER_BUTTONS"])
                else:
                    if file.isDir():
                        surface.fill(COLORS["SELECTED_DIR"])
                    else:
                        surface.fill(COLORS["SELECTED_FILE"])

                createButton(x, y, w, h, openFile, (file,), True)
                write(file.name, TEXT_WIDTH, TEXT_HEIGHT, surface)
                screen.blit(surface, (x, y))
            x += TEXT_WIDTH * (3 + len(file.name))

        writeCenteredHorizontal(getCurrentFolder(), HALF_TEXT_HEIGHT)

        lenSelectedFiles = len(getSelectedFiles())

        if lenSelectedFiles > 0:
            shouldDrawTabs = False
            fill(
                0,
                DRAWING_AREA_BOTTOM,
                SCREEN_WIDTH,
                FOOTER_SIZE - TEXT_HEIGHT,
                COLORS["TOP_BAR"],
            )
            y = DRAWING_AREA_BOTTOM + TEXT_HEIGHT
            x = (
                write("Selected: " + str(lenSelectedFiles), TEXT_WIDTH, y)
                + TEXT_WIDTH * 3
            )

            def wt(text, x, fun):
                createButton(
                    x - TEXT_WIDTH,
                    DRAWING_AREA_BOTTOM + HALF_TEXT_HEIGHT,
                    TEXT_WIDTH * (len(text) + 2),
                    TEXT_HEIGHT * 2,
                    fun,
                    None,
                    False,
                    COLORS["BACKGROUND"],
                )
                return write(text, x, y) + TEXT_WIDTH * 3

            wt(
                "MOVE",
                wt("COPY", wt("DEL", x, deleteSelectedFiles), copySelectedFiles),
                moveSelectedFiles,
            )

            x_surface = pygame.Surface((TEXT_HEIGHT * 3, TEXT_HEIGHT * 3))
            x = SCREEN_WIDTH - TEXT_HEIGHT * 3
            createButton(
                x,
                DRAWING_AREA_BOTTOM,
                x_surface.get_width(),
                x_surface.get_height(),
                clearSelectedFiles,
            )
            x_surface.fill(COLORS["RED"])
            writeCentered("X", x_surface)
            screen.blit(x_surface, (x, DRAWING_AREA_BOTTOM))

        drawScrollBar(
            getFileExplorerOffset(), getFileLines(), None, None, setFileExplorerOffset
        )

    elif current_tab == "graph":
        top = TEXT_HEIGHT * 3
        left = TEXT_WIDTH
        w = SCREEN_WIDTH - 2 * TEXT_WIDTH
        h = SCREEN_HEIGHT - 4 * TEXT_HEIGHT - FOOTER_SIZE
        right = left + w
        bottom = top + h
        graph = pygame.Surface((w, h), pygame.SRCALPHA)
        graph.fill(COLORS["GRAPH_BACKGROUND"])
        # fill(left, top, w, h, COLORS["GRAPH_BACKGROUND"])
        # while y - TEXT_HEIGHT * 3 < h:
        # pygame.draw.line(screen, COLORS["TOP_BAR"], (x, y + TEXT_HEIGHT), (w + x, y + TEXT_HEIGHT))
        # y += TEXT_HEIGHT * 2
        with open("log.json", "r") as logged:
            # for line in logged.readlines():
            # json.loads(line)
            x = 0
            for log in list(map(json.loads, logged.readlines())):
                mem_percentage = log["memory"][0]["percentage"]
                cpu_percentage = log["cpu"]
                y = h - h * mem_percentage
                pygame.draw.circle(
                    graph, (*COLORS["GRAPH_LINE"]["MEMORY"], 255), (x, y), 1
                )
                fill(x, y, 1, h - y, (*COLORS["GRAPH_LINE"]["MEMORY"], 20), graph)
                y = h - h * cpu_percentage
                pygame.draw.circle(graph, (*COLORS["GRAPH_LINE"]["CPU"], 80), (x, y), 1)
                fill(x, y, 1, h - y, (*COLORS["GRAPH_LINE"]["CPU"], 20), graph)
                x += 1
        screen.blit(graph, (left, top))

    if shouldDrawTabs:
        drawTabs(
            (
                ("task", "Task Manager"),
                ("file", "File Manager"),
                ("graph", "Log graph", CONFIG["LOGGING"]),
            )
        )

    if CONFIG["DEBUG"]:
        for button in getButtons():
            button.draw(COLORS["REDISH_GREY"])

    pygame.display.update()
    if CONFIG["UPDATE_DISPLAY_EVERY_X_SECONDS"] > 0:
        sleep(CONFIG["UPDATE_DISPLAY_EVERY_X_SECONDS"])

should_exit = True
sys.exit()
