from os import path, makedirs
from distutils.dir_util import remove_tree


def create_dir(dir_path):
    try:
        if path.exists(dir_path):
            remove_tree(dir_path)
        makedirs(dir_path)
    except OSError:
        print('Error: Creating directory. ' + dir_path)
        raise
