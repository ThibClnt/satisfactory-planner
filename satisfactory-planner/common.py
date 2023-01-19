import os.path
from os import PathLike


class AppState:
    IDLE = 0
    BUILD = 1

    def __init__(self, state: int = 0):
        self.__state = state

    def set(self, state: int):
        self.__state = state

    def get(self) -> int:
        return self.__state


def get_path(relative_path: str | PathLike[bytes]) -> str:
    """
    :param relative_path: Relative path from root directory to a file
    :type relative_path str | PathLike[bytes]
    :return: Absolute path to the file
    :rtype: str
    """
    dir_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.join(dir_path, "../")
    return os.path.join(root_path, relative_path)


def trim(value, start, end):
    return min(max(value, start), end)
