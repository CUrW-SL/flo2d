import json

from datetime import datetime
from distutils.dir_util import remove_tree
from os import path, makedirs

from constants import INIT_DATE_TIME_FORMAT


def create_dir(dir_path):
    try:
        if path.exists(dir_path):
            remove_tree(dir_path)
        makedirs(dir_path)
    except OSError:
        print('Error: Creating directory. ' + dir_path)
        raise


def get_run_date_times(run_path):
    run_config_path = path.join(run_path, 'input', 'run-config.json')
    with open(run_config_path, 'r') as F:
        run_config = json.load(F)
    base_dt = datetime.strptime(run_config['base-date-time'], INIT_DATE_TIME_FORMAT)
    run_dt = datetime.strptime(run_config['run-date-time'], INIT_DATE_TIME_FORMAT)
    return base_dt, run_dt