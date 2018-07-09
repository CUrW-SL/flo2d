from datetime import datetime
from flask import Flask, request
from flask_json import FlaskJSON, JsonError, json_response
from flask_uploads import UploadSet, configure_uploads
from os import path

from utils import is_valid_run_name, parse_run_id, prepare_flo2d_run, run_flo2d_model
from config import UPLOADS_DEFAULT_DEST, MODEL_250M_TEMPLATE_DIR, FLO2D_LIBS_DIR

app = Flask(__name__)
json = FlaskJSON()

# Flask-Uploads configs
app.config['UPLOADS_DEFAULT_DEST'] = path.join(UPLOADS_DEFAULT_DEST, 'FLO2D')
app.config['UPLOADED_FILES_ALLOW'] = 'DAT'

# upload set creation
model_250m = UploadSet('model250m', extensions='DAT')

configure_uploads(app, model_250m)
json.init_app(app)


@app.route('/')
def hello_world():
    return 'Welcome to FLO2D Server!'


@app.route('/FLO2D/250m/init-run', methods=['POST'])
def init_250m_run():
    req_args = request.args.to_dict()
    # check whether run-name is specified and valid.
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified.')
    run_name = req_args['run-name']
    if not is_valid_run_name(run_name):
        raise JsonError(status_=400, description='run-name cannot contain spaces or colons.')

    today = datetime.today().strftime('%Y-%m-%d')
    input_dir = path.join(today, run_name, 'input')
    # check whether the given run-name is already taken for today.
    if path.exists(path.join(UPLOADS_DEFAULT_DEST, 'FLO2D', 'model250m', input_dir)):
        raise JsonError(status_=400, description='run-name: %s is already taken for today: %s.' % (run_name, today))

    req_files = request.files
    if 'inflow' in req_files and 'outflow' in req_files and 'raincell' in req_files:
        model_250m.save(req_files['inflow'], folder=input_dir, name='INFLOW.DAT')
        model_250m.save(req_files['outflow'], folder=input_dir, name='OUTFLOW.DAT')
        model_250m.save(req_files['raincell'], folder=input_dir, name='RAINCELL.DAT')
        run_id = 'FLO2D:model250m:%s:%s' % (today, run_name)  # TODO save run_id in a DB with the status
        return json_response(status_=200, run_id=run_id, description='Successfully saved files.')


@app.route('/FLO2D/250m/start-run', methods=['GET', 'POST'])
def start_250m_run():
    req_args = request.args.to_dict()
    # check whether run_id is specified and valid.
    if 'run-id' not in req_args.keys() or not req_args['run-id']:
        raise JsonError(status_=400, description='run-id is not specified')

    run_id = req_args['run-id']
    rel_run_path = parse_run_id(run_id)
    run_path = path.join(UPLOADS_DEFAULT_DEST, rel_run_path)

    prepare_flo2d_run(run_path, MODEL_250M_TEMPLATE_DIR, FLO2D_LIBS_DIR)
    run_flo2d_model(run_path)
    return json_response(status_=200, run_id=run_id, run_status='Started',
                         description='Successfully started model run. This will take a while to complete.')


if __name__ == '__main__':
    app.run()
