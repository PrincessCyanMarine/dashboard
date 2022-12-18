from os import popen
from os.path import *
import re

from constants import USER_PATH
from types import NoneType


class File:
    def __init__(this, _isDir, size, lastModified, name, dir):
        this._isDir = _isDir
        this.size = size
        this.lastModified = lastModified
        this.name = name
        this.dir = dir

    def isDir(this):
        return this._isDir

    def getFullPath(this):
        return this.dir + "/" + this.name


current_path = USER_PATH

file_explorer_offset = 0
file_lines = 0

path_history = [current_path]
path_position = 0


def getFileExplorerOffset():
    return file_explorer_offset


def setFileExplorerOffset(value):
    global file_explorer_offset
    file_explorer_offset = value


def addFileLine():
    setFileLines(file_lines + 1)


def setFileLines(value):
    global file_lines
    file_lines = value


def getFileLines():
    return file_lines


def cd(path, historyIgnore=False):
    global current_path, path_position
    current_path = abspath(normpath(join(current_path, path)))
    if not historyIgnore:
        if path_position != 0:
            global path_history
            path_history = path_history[0 : getTruePathPosition() + 1]
            path_position = 0

        path_history.append(current_path)

    setFileExplorerOffset(0)


def filePathBack():
    global path_position
    if path_position >= len(path_history) - 1:
        return

    path_position += 1
    cd(path_history[getTruePathPosition()], True)


def getTruePathPosition():
    return len(path_history) - path_position - 1


def getCurrentFolder():
    if current_path == USER_PATH:
        return "~"
    return basename(current_path)


def filePathFowards():
    global path_position
    if path_position <= 0:
        return

    path_position -= 1
    cd(path_history[getTruePathPosition()], True)


def ls():
    def translate(file):
        match = re.match(
            "^([d-])(\S+?)\s+?([0-9]+?)\s+?(\S+?)\s+?(\S+?)\s+?([0-9]+?)\s+?(\S+?\s+?[0-9]+?\s+?[0-9]+?\:[0-9]+?)\s+?(.+)$",
            file,
        )
        # print(file[0 : len(file) - 1])
        # print(match)
        # print("")

        if not match:
            return None

        groups = match.groups()
        res = File(groups[0] == "d", int(groups[5]), groups[6], groups[7], current_path)
        return res

    lines = popen('ls "' + current_path + '" -la').readlines()
    if len(lines) > 0:
        del lines[0]
    return sorted(
        sorted(
            list(filter(lambda x: type(x) is not NoneType, (map(translate, lines)))),
            key=lambda file: file.name,
        ),
        key=lambda file: 1 if file.isDir() else 0,
        reverse=True,
    )


selectedFiles = []


def clearSelectedFiles():
    global selectedFiles
    selectedFiles = []


def getSelectedFilesAsString():
    return " ".join(map(lambda file: '"' + file.getFullPath() + '"', selectedFiles))


def copySelectedFiles():
    popen("cp " + getSelectedFilesAsString() + ' "' + current_path + '"' + " -rbf")
    clearSelectedFiles()


def moveSelectedFiles():
    popen("mv " + getSelectedFilesAsString() + ' "' + current_path + '"' + " -bf")
    clearSelectedFiles()


def deleteSelectedFiles():
    popen("gio trash " + getSelectedFilesAsString() + " -f")
    clearSelectedFiles()


def getFileSelectedPos(file):
    for i in range(0, len(selectedFiles)):
        testing = selectedFiles[i]
        if (
            testing.isDir() == file.isDir()
            and testing.name == file.name
            and testing.dir == file.dir
        ):
            return i
    return -1


def selectFile(file):
    if file.name == "." or file.name == "..":
        return
    pos = getFileSelectedPos(file)
    if pos != -1:
        del selectedFiles[pos]
    else:
        selectedFiles.append(file)
    # printSelectedFiles()


def getSelectedFiles():
    return selectedFiles


def printSelectedFiles():
    print()
    for file in selectedFiles:
        s = file.dir + "/" + file.name
        if file.isDir():
            s += "/"
        print(s)


def openFile(file, event):
    if event.button == 1:
        if file.isDir():
            cd(file.name)
        else:
            path_name = abspath(normpath(join(current_path, file.name)))
            popen("xdg-open " + path_name + " || " + path_name)
    elif event.button == 3:
        selectFile(file)
