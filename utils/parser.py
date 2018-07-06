from os import path


def parse_run_id(run_id):
    """
    Parse the given run_id and return the relative path to the resource location for the corresponding run.
    :param run_id: <class str> colon separated string of <FLO2D Base dir>:<model diir>:<day>:<run_name>
    :return: <class str> relative path to the resource location
    """
    if not run_id:
        raise ValueError('run_id should be a non empty string')
    dir_list = run_id.split(':')
    return path.join(*dir_list)
