import os.path
from os import PathLike


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
