from os import path
from distutils.dir_util import copy_tree

from .general import create_dir


def prepare_flo2d_run(run_path, model_template_path,flo2d_lib_path):
    # create a directory for the model run.
    model_path = path.join(run_path, 'model')
    create_dir(model_path)

    # copy flo2d library files to model run directory.
    copy_tree(flo2d_lib_path, model_path)

    # copy model template to model run directory.
    copy_tree(model_template_path, model_path)

    # copy the model input files to model run directory
    copy_tree(path.join(run_path, 'input'), model_path)
