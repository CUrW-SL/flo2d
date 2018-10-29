import json

from datetime import datetime, timedelta
from flask import Flask, request, send_from_directory, jsonify
from flask_negotiate import consumes, produces
from flask_json import FlaskJSON, JsonError, json_response
from flask_uploads import UploadSet, configure_uploads
from os import path

from constants import INIT_DATE_TIME_FORMAT
from config import UPLOADS_DEFAULT_DEST, FLO2D_LIBS_DIR, MODEL_TEMPLATE_DIR, MODEL_NAME, MODEL_RESOLUTION
from utils import is_valid_run_name, is_valid_init_dt, parse_run_id, prepare_flo2d_run, run_flo2d_model, \
    prepare_flo2d_output, extract_channel_water_levels, extract_flood_plane_water_levels, extract_water_discharge, \
    prepare_flo2d_waterlevel_grid_asci, prepare_flo2d_run_config, is_output_ready

app = Flask(__name__)
flask_json = FlaskJSON()

# Flask-Uploads configs
app.config['UPLOADS_DEFAULT_DEST'] = path.join(UPLOADS_DEFAULT_DEST, 'FLO2D')
app.config['UPLOADED_FILES_ALLOW'] = 'DAT'

# upload set creation
model_store = UploadSet(MODEL_NAME, extensions='DAT')

configure_uploads(app, model_store)
flask_json.init_app(app)


@app.route('/')
def hello_world():
    return 'Welcome to FLO2D Server!'


@app.route('/FLO2D/init-run', methods=['POST'])
def init_run():
    req_args = request.args.to_dict()
    # Check whether run-name is specified and valid.
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified.')
    run_name = req_args['run-name']
    if not is_valid_run_name(run_name):
        raise JsonError(status_=400, description='run-name cannot contain spaces or colons.')
    # Valid base-dt must be specified at the initialization phase
    if 'base-dt' not in req_args.keys() or not req_args['base-dt']:
        raise JsonError(status_=400, description='base-dt is not specified.')
    base_dt = req_args['base-dt']
    if not is_valid_init_dt(base_dt):
        raise JsonError(status_=400, description='Given base-dt is not in the correct format: %s'
                                                 % INIT_DATE_TIME_FORMAT)
    # Valid run-dt must be specified at the initialization phase
    if 'run-dt' not in req_args.keys() or not req_args['run-dt']:
        raise JsonError(status_=400, description='run-dt is not specified.')
    run_dt = req_args['run-dt']
    if not is_valid_init_dt(run_dt):
        raise JsonError(status_=400, description='Given run-dt is not in the correct format: %s'
                                                 % INIT_DATE_TIME_FORMAT)

    today = datetime.today().strftime('%Y-%m-%d')
    input_dir_rel_path = path.join(today, run_name, 'input')
    # Check whether the given run-name is already taken for today.
    input_dir_abs_path = path.join(UPLOADS_DEFAULT_DEST, 'FLO2D', MODEL_NAME, input_dir_rel_path)
    if path.exists(input_dir_abs_path):
        raise JsonError(status_=400, description='run-name: %s is already taken for today: %s.' % (run_name, today))

    req_files = request.files
    if 'inflow' in req_files and 'outflow' in req_files and 'raincell' in req_files:
        model_store.save(req_files['inflow'], folder=input_dir_rel_path, name='INFLOW.DAT')
        model_store.save(req_files['outflow'], folder=input_dir_rel_path, name='OUTFLOW.DAT')
        model_store.save(req_files['raincell'], folder=input_dir_rel_path, name='RAINCELL.DAT')
    else:
        raise JsonError(status_=400, description='Missing required input files. Required inflow, outflow, raincell.')

    # Save run configurations.
    prepare_flo2d_run_config(input_dir_abs_path, run_name, base_dt, run_dt)

    run_id = 'FLO2D:%s:%s:%s' % (MODEL_NAME, today, run_name)  # TODO save run_id in a DB with the status
    return json_response(status_=200, run_id=run_id, description='Successfully saved files.')


@app.route('/FLO2D/start-run', methods=['GET', 'POST'])
def start_run():
    req_args = request.args.to_dict()
    # check whether run_id is specified and valid.
    if 'run-id' not in req_args.keys() or not req_args['run-id']:
        raise JsonError(status_=400, description='run-id is not specified')

    run_id = req_args['run-id']
    try:
        rel_run_path = parse_run_id(run_id)
    except:
        raise JsonError(status_=400, description='Error in the given run-id: %s' % run_id)
    run_path = path.join(UPLOADS_DEFAULT_DEST, rel_run_path)

    prepare_flo2d_run(run_path, MODEL_TEMPLATE_DIR, FLO2D_LIBS_DIR)
    run_flo2d_model(run_path)
    # TODO update the run_id in the DB with the status
    return json_response(status_=200, run_id=run_id, run_status='Started',
                         description='Successfully started model run. This will take a while to complete.')


@app.route('/FLO2D/get-output/output.zip', methods=['GET', 'POST'])
def get_output():
    req_args = request.args.to_dict()
    # check whether run_id is specified and valid.
    if 'run-id' not in req_args.keys() or not req_args['run-id']:
        raise JsonError(status_=400, description='run-id is not specified')

    run_id = req_args['run-id']
    try:
        rel_run_path = parse_run_id(run_id)
    except:
        raise JsonError(status_=400, description='Error in the given run-id: %s' % run_id)
    run_path = path.join(UPLOADS_DEFAULT_DEST, rel_run_path)

    # TODO check the DB for the status of run_id
    # TODO if status is not finished prepare error response saying so.
    if not is_output_ready(run_path):
        raise JsonError(status_=503, run_id=run_id, run_status='Running', description='output is not ready yet.')

    output_zip = prepare_flo2d_output(run_path)
    return send_from_directory(directory=run_path, filename=output_zip)


@app.route('/FLO2D/extract/water-level', methods=['POST'])
@consumes('application/json')
def extract_waterlevel():
    req_args = request.args.to_dict()
    # check whether run_id is specified and valid.
    if 'run-id' not in req_args.keys() or not req_args['run-id']:
        raise JsonError(status_=400, description='run-id is not specified')

    run_id = req_args['run-id']
    try:
        rel_run_path = parse_run_id(run_id)
    except:
        raise JsonError(status_=400, description='Error in the given run-id: %s' % run_id)
    run_path = path.join(UPLOADS_DEFAULT_DEST, rel_run_path)

    try:
        cell_map = request.get_json()
        channel_cell_map = cell_map['CHANNEL_CELL_MAP']
        flood_plane_cell_map = cell_map['FLOOD_PLANE_CELL_MAP'] if 'FLOOD_PLANE_CELL_MAP' in cell_map else None
    except:
        raise JsonError(status_=400, description='Invalid cell map!')

    # TODO check the DB for the status of run_id
    # TODO if status is not finished prepare error response saying so.
    if not is_output_ready(run_path):
        raise JsonError(status_=503, run_id=run_id, run_status='Running', description='output is not ready yet.')

    channel_tms = extract_channel_water_levels(run_path, channel_cell_map)
    flood_plane_tms = extract_flood_plane_water_levels(run_path, flood_plane_cell_map) \
        if flood_plane_cell_map is not None else {}
    return jsonify({'CHANNELS': channel_tms, 'FLOOD_PLANE': flood_plane_tms})


@app.route('/FLO2D/extract/water-discharge', methods=['POST'])
@consumes('application/json')
def extract_waterdischarge():
    req_args = request.args.to_dict()
    # check whether run_id is specified and valid.
    if 'run-id' not in req_args.keys() or not req_args['run-id']:
        raise JsonError(status_=400, description='run-id is not specified')

    run_id = req_args['run-id']
    try:
        rel_run_path = parse_run_id(run_id)
    except:
        raise JsonError(status_=400, description='Error in the given run-id: %s' % run_id)
    run_path = path.join(UPLOADS_DEFAULT_DEST, rel_run_path)

    try:
        cell_map = request.get_json()
        channel_cell_map = cell_map['CHANNEL_CELL_MAP']
    except:
        raise JsonError(status_=400, description='Invalid cell map!')

    # TODO check the DB for the status of run_id
    # TODO if status is not finished prepare error response saying so.
    if not is_output_ready(run_path):
        raise JsonError(status_=503, run_id=run_id, run_status='Running', description='output is not ready yet.')

    channel_tms = extract_water_discharge(run_path, channel_cell_map)
    return jsonify({'CHANNELS': channel_tms})


@app.route('/FLO2D/extract/water-level-grid.zip', methods=['GET', 'POST'])
def extract_waterlevelgrid():
    req_args = request.args.to_dict()
    # check whether run_id is specified and valid.
    if 'run-id' not in req_args.keys() or not req_args['run-id']:
        raise JsonError(status_=400, description='run-id is not specified')

    run_id = req_args['run-id']
    try:
        rel_run_path = parse_run_id(run_id)
    except:
        raise JsonError(status_=400, description='Error in the given run-id: %s' % run_id)
    run_path = path.join(UPLOADS_DEFAULT_DEST, rel_run_path)

    # TODO check the DB for the status of run_id
    # TODO if status is not finished prepare error response saying so.
    if not is_output_ready(run_path):
        raise JsonError(status_=503, run_id=run_id, run_status='Running', description='output is not ready yet.')

    asci_grid_zip = prepare_flo2d_waterlevel_grid_asci(run_path, MODEL_RESOLUTION)
    return send_from_directory(directory=run_path, filename=asci_grid_zip)


if __name__ == '__main__':
    app.run()
