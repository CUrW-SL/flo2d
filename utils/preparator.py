from shutil import make_archive
from distutils.dir_util import copy_tree
from os import path

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


def prepare_flo2d_output(run_path):
    output_base = 'output'
    output_zip = output_base + '.zip'
    output_zip_abs_path = path.join(run_path, output_zip)

    # check whether output.zip is already created.
    if path.exists(output_zip_abs_path):
        return output_zip

    # check whether the output is ready.
    output_dir = path.join(run_path, 'output')
    if path.exists(output_dir):
        make_archive(path.join(run_path, output_base), 'zip', output_dir)
        return output_zip

    return None
