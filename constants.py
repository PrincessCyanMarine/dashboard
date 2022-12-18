from enum import Enum
from os import popen

COLORS = {
    "GREY": (100, 100, 100),
    "BLUEISH_GREY": (90, 120, 120),
    "REDISH_GREY": (120, 90, 90, 100),
    "DARK_GREY": (90, 90, 90),
    "GREEN": (148, 222, 51),
    "YELLOW": (222, 222, 51),
    "RED": (255, 36, 36),
    "BACKGROUND": (51, 51, 68),
    "TEXT": (250, 250, 250),
    "TOP_BAR": (34, 34, 51),
    "GRAPH_LINE": {
        "MEMORY": (51, 255, 51),
        "CPU": (255, 51, 51),
    },
    "FOOTER_BUTTONS": (20, 20, 30),
    # "GRAPH_BACKGROUND": (80, 80, 100),
    "GRAPH_BACKGROUND": (100, 100, 100),
    "SCROLL_BACKGROUND": (80, 80, 100),
    "SCROLL_THUMB": (40, 40, 70),
    "SELECTED_DIR": (100, 100, 150),
    "SELECTED_FILE": (20, 20, 60),
}

SORTING_METHODS = Enum(
    "SortingMethods",
    ["CPU_ASCENDING", "CPU_DESCENDING", "MEM_ASCENDING", "MEM_DESCENDING", "PID_ASCENDING", "PID_DESCENDING"],
)

USER_PATH = popen("echo /home/$USER").readline()
USER_PATH = USER_PATH[0 : len(USER_PATH) - 1]
