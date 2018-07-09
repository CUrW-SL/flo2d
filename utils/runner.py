import threading

from glob import glob
from os import path
from shutil import copy
from subprocess import Popen

from .general import create_dir


def run_flo2d_model(run_path):
    thread = threading.Thread(target=_run_flo2d_model, args=(run_path,))
    thread.daemon = True  # Daemonize thread
    thread.start()


def _run_flo2d_model(run_path):
    # run flo2d model
    run_model_path = path.join(run_path, 'model')
    popen_flo2d = Popen(path.join(run_model_path, 'FLOPRO.exe'), cwd=run_model_path)

    # wait for flo2d run completes
    popen_flo2d.communicate()

    # create output directory
    run_output_path = path.join(run_path, 'output')
    create_dir(run_output_path)

    # copy the results to output directory
    out_file_list = glob(path.join(run_model_path, '*.OUT'))
    dat_file_list = glob(path.join(run_model_path, '*.DAT'))

    for out_file in out_file_list:
        copy(out_file, run_output_path)

    for dat_file in dat_file_list:
        copy(dat_file, run_output_path)
