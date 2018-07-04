from datetime import datetime
from flask import Flask, request
from flask_json import FlaskJSON, JsonError, json_response
from flask_uploads import UploadSet, configure_uploads
from os import path

app = Flask(__name__)
json = FlaskJSON()

# Flask-Uploads configs
app.config['UPLOADS_DEFAULT_DEST'] = 'FLO2D'
app.config['UPLOADED_FILES_ALLOW'] = 'DAT'

# upload set creation
model_250m = UploadSet('model250m', extensions='DAT')

configure_uploads(app, model_250m)
json.init_app(app)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/FLO2D/250m/init-run', methods=['POST'])
def init_250m_run():
    req_args = request.args.to_dict()
    # check whether run-name is specified and valid.
    if 'run-name' not in req_args.keys() or not req_args['run-name']:
        raise JsonError(status_=400, description='run-name is not specified')

    run_name = req_args['run-name']
    today = datetime.today().strftime('%Y-%m-%d')
    input_dir = path.join(today, run_name, 'input')
    # check whether the given run-name is already taken for today.
    if path.exists(path.join(app.root_path, 'FLO2D', 'model250m', input_dir)):
        raise JsonError(status_=400, description='run-name: %s is already taken for today: %s' % (run_name, today))

    req_files = request.files
    if 'inflow' in req_files and 'outflow' in req_files and 'raincell' in req_files:
        model_250m.save(req_files['inflow'], folder=input_dir, name='INFLOW.DAT')
        model_250m.save(req_files['outflow'], folder=input_dir, name='OUTFLOW.DAT')
        model_250m.save(req_files['raincell'], folder=input_dir, name='RAINCELL.DAT')
        task_id = 'FLO2D:model250m:%s:%s' % (today, run_name)
        return json_response(status_=200, task_id=task_id, description='successfully saved files')


if __name__ == '__main__':
    app.run()
