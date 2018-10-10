import json

from shutil import make_archive
from distutils.dir_util import copy_tree
from os import path

from .general import create_dir, get_run_date_times
from .asci_extractor import extract_water_level_grid


def prepare_flo2d_run(run_path, model_template_path, flo2d_lib_path):
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

    # Check whether output.zip is already created.
    if path.exists(output_zip_abs_path):
        return output_zip

    # Check whether the output is ready. If ready, archive and return the .zip, otherwise return None.
    output_dir = path.join(run_path, 'output')
    if path.exists(output_dir):
        make_archive(path.join(run_path, output_base), 'zip', output_dir)
        return output_zip

    return None


def prepare_flo2d_waterlevel_grid_asci(run_path, grid_size):
    asci_grid_zip = 'asci_grid.zip'
    # Check whether asci_grid.zip is already created, if so just return the asci_grid_zip
    if path.exists(path.join(run_path, asci_grid_zip)):
        return asci_grid_zip

    asci_grid_dir = path.join(run_path, 'asci_grid')
    create_dir(asci_grid_dir)

    base_dt, run_dt = get_run_date_times(run_path)
    extract_water_level_grid(run_path, grid_size, base_dt, run_dt, asci_grid_dir)

    make_archive(asci_grid_dir, 'zip', asci_grid_dir)
    return asci_grid_zip


def prepare_flo2d_run_config(input_path, run_name, base_dt, run_dt):
    run_config = {
        'run-name': run_name,
        'base-date-time': base_dt,
        'run-date-time': run_dt
    }
    json_file = json.dumps(run_config)
    with open(path.join(input_path, 'run-config.json'), 'w+') as F:
        F.write(json_file)
        F.close()
