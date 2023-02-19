
##################################################################################
#                                                                                #
# Copyright (c) 2020 AECgeeks                                                    #
#                                                                                #
# Permission is hereby granted, free of charge, to any person obtaining a copy   #
# of this software and associated documentation files (the "Software"), to deal  #
# in the Software without restriction, including without limitation the rights   #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell      #
# copies of the Software, and to permit persons to whom the Software is          #
# furnished to do so, subject to the following conditions:                       #
#                                                                                #
# The above copyright notice and this permission notice shall be included in all #
# copies or substantial portions of the Software.                                #
#                                                                                #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR     #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,       #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE    #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER         #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE  #
# SOFTWARE.                                                                      #
#                                                                                #
##################################################################################

from __future__ import print_function


import os
import json
import ast

import threading
from functools import wraps

from collections import namedtuple

from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, request, session, send_file, render_template, abort, jsonify, redirect, url_for, make_response
from flask_cors import CORS

from flasgger import Swagger, validate

import requests
from requests_oauthlib import OAuth2Session
from authlib.jose import jwt

import utils
import bsdd_utils
import database
import worker
import pr_manager


application = Flask(__name__)


DEVELOPMENT = os.environ.get(
    'environment', 'production').lower() == 'development'

if not DEVELOPMENT:
    assert os.getenv("DEV_EMAIL")
    assert os.getenv("ADMIN_EMAIL")
    assert os.getenv("CONTACT_EMAIL")

VALIDATION = 1
VIEWER = 0

if not DEVELOPMENT and os.path.exists("/version"):
    PIPELINE_POSTFIX = "." + open("/version").read().strip()
else:
    PIPELINE_POSTFIX = ""


if not DEVELOPMENT:
    # In some setups this proved to be necessary for url_for() to pick up HTTPS
    application.wsgi_app = ProxyFix(application.wsgi_app, x_proto=1)

CORS(application)
application.config['SWAGGER'] = {
    'title': os.environ.get('APP_NAME', 'ifc-pipeline request API'),
    'openapi': '3.0.2',
    "specs": [
        {
            "version": "0.1",
            "title": os.environ.get('APP_NAME', 'ifc-pipeline request API'),
            "description": os.environ.get('APP_NAME', 'ifc-pipeline request API'),
            "endpoint": "spec",
            "route": "/apispec",
        },
    ]
}
swagger = Swagger(application)

NO_REDIS = os.environ.get('NO_REDIS', '0').lower() in {'1', 'true'}

if not DEVELOPMENT and not NO_REDIS:
    from redis import Redis
    from rq import Queue

    q = Queue(connection=Redis(host=os.environ.get(
        "REDIS_HOST", "localhost")), default_timeout=3600)


if not DEVELOPMENT:
    application.config['SESSION_TYPE'] = 'filesystem'
    application.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    # LOGIN
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    # Credentials you get from registering a new application
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    authorization_base_url = 'https://authentication.buildingsmart.org/buildingsmartservices.onmicrosoft.com/b2c_1a_signupsignin_c/oauth2/v2.0/authorize'
    token_url = 'https://authentication.buildingsmart.org/buildingSMARTservices.onmicrosoft.com/b2c_1a_signupsignin_c/oauth2/v2.0/token'
    redirect_uri = f'https://{os.environ["SERVER_NAME"]}/callback'


def login_required(f):
    @wraps(f)
    def decorated_function(**kwargs):
        if not DEVELOPMENT:
            if not "oauth_token" in session.keys() or 'user_data' not in session:
                # before redirect, capture the commit id
                session['commit_id'] = kwargs.get('commit_id')
                abort(403)
            with database.Session() as db_session:
                user = db_session.query(database.user).filter(database.user.id == session['user_data']["sub"]).all()
                if len(user) == 0:
                    abort(403)
            user_data = session['user_data']
        else:
            user_data = {
                    'sub': 'development-id',
                    'email': 'test@example.org',
                    'family_name': 'User',
                    'given_name': 'Test',
                    'name': 'Test User',
                }
            with database.Session() as db_session:
                user = db_session.query(database.user).filter(database.user.id == 'development-id').all()
                if len(user) == 0:
                    db_session.add(database.user(str(user_data["sub"]),
                                                str(user_data.get('email', '')),
                                                str(user_data.get('family_name', '')),
                                                str(user_data.get('given_name', '')),
                                                str(user_data.get('name', ''))))
                    db_session.commit()


        return f(user_data=user_data, **kwargs)
    return decorated_function


def with_sandbox(orig):
    @wraps(orig)
    def inner(commit_id=None, **kwargs):
        pr_title = None
        if commit_id:
            args = pr_manager.is_authorized_commit_id(commit_id)
            if not args:
                abort(404)
            repo, sha, number, title = args
            pr_title = f'#{number} {title}'
        return orig(commit_id=commit_id, pr_title=pr_title, **kwargs)
    return inner


@application.route("/sandbox/<commit_id>/")
@application.route("/api/")
@login_required
@with_sandbox
def index(user_data, pr_title=None, commit_id=None):
    if DEVELOPMENT:
        with database.Session() as db_session:
            user = db_session.query(database.user).filter(database.user.id == user_data["sub"]).all()
            if len(user) == 0:
                db_session.add(database.user(str(user_data["sub"]),
                                            str(user_data.get('email', '')),
                                            str(user_data.get('family_name', '')),
                                            str(user_data.get('given_name', '')),
                                            str(user_data.get('name', ''))))
                db_session.commit()

    return render_template('index.html', commit_id=commit_id, pr_title=pr_title, user_data=user_data, username=f"{user_data.get('given_name', '')} {user_data.get('family_name', '')}")


# @todo still requires sandbox parameters
@application.route('/api/login', methods=['GET'])
def login():
    bs = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=[
                       "openid profile", "https://buildingSMARTservices.onmicrosoft.com/api/read"])
    authorization_url, state = bs.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return jsonify({"redirect":authorization_url})

@application.route('/api/sandbox/me/<commit_id>', methods=['GET'])
@application.route('/api/me', methods=['GET'])
@with_sandbox
def me(pr_title=None, commit_id=None):
    if not DEVELOPMENT:
        if not "oauth_token" in session.keys():   
            bs = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=[
                            "openid profile", "https://buildingSMARTservices.onmicrosoft.com/api/read"])
            authorization_url, state = bs.authorization_url(authorization_base_url)
            session['oauth_state'] = state
            return jsonify({"redirect":authorization_url})
        else:
            return jsonify({"user_data":session["user_data"], "sandbox_info":{"pr_title":pr_title, "commit_id":commit_id}})
    else:
        return jsonify(
                    {"user_data":
                        {'sub': 'development-id',
                            'email': 'test@example.org',
                            'family_name': 'User',
                            'given_name': 'Test',
                            'name': 'Test User'},
                    "sandbox_info":{"pr_title":pr_title, "commit_id":commit_id}
                })
   
@application.route("/callback/")
def callback():
    bs = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri=redirect_uri, scope=[
                       "openid profile", "https://buildingSMARTservices.onmicrosoft.com/api/read"])
    try:
        t = bs.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url, response_type="token")
    except:
        return redirect(url_for('login'))
        
    BS_DISCOVERY_URL = (
        "https://authentication.buildingsmart.org/buildingSMARTservices.onmicrosoft.com/b2c_1a_signupsignin_c/v2.0/.well-known/openid-configuration"
    )

    session['oauth_token'] = t

    # Get claims thanks to openid
    discovery_response = requests.get(BS_DISCOVERY_URL).json()
    key = requests.get(discovery_response['jwks_uri']).content.decode("utf-8")
    id_token = t['id_token']


    user_data = jwt.decode(id_token, key=key)
    session['user_data'] = user_data

    with database.Session() as db_session:
        user = db_session.query(database.user).filter(database.user.id == user_data["sub"]).all()
        if len(user) == 0:
            db_session.add(database.user(str(user_data["sub"]),
                                        str(user_data.get('email', '')),
                                        str(user_data.get('family_name', '')),
                                        str(user_data.get('given_name', '')),
                                        str(user_data.get('name', ''))))
            db_session.commit()

    if cid := session.get('commit_id'):
        # Restore and then discard the commit_id stored before
        # redirecting to /login
        del session['commit_id']
        return redirect("/") #todo: also add the commit ID
    else:
        return redirect("/")


@application.route("/api/logout")
def logout():
    if DEVELOPMENT:
        return redirect(url_for('index'))
    else:
        session.clear()  # Wipe out the user and the token cache from the session 
        # Also need to log out from the Microsoft Identity platform
        return jsonify({"redirect":f"https://authentication.buildingsmart.org/buildingSMARTservices.onmicrosoft.com/b2c_1a_signupsignin_c/oauth2/v2.0/logout?post_logout_redirect_uri=https://{os.environ['SERVER_NAME']}/"})

def process_upload(filewriter, callback_url=None):

    id = utils.generate_id()
    d = utils.storage_dir_for_id(id)
    os.makedirs(d)

    filewriter(os.path.join(d, id+".ifc"))

    session = database.Session()
    session.add(database.model(id, 'test'))
    session.commit()
    session.close()

    if DEVELOPMENT or NO_REDIS:

        t = threading.Thread(target=lambda: worker.process(id, callback_url))
        t.start()

    else:
        q.enqueue(worker.process, id, callback_url)

    return id


def process_upload_multiple(files, callback_url=None):
    id = utils.generate_id()
    d = utils.storage_dir_for_id(id)
    os.makedirs(d)

    file_id = 0
    session = database.Session()
    m = database.model(id, '')
    session.add(m)

    for file in files:
        fn = file.filename
        def filewriter(fn): return file.save(fn)
        filewriter(os.path.join(d, id+"_"+str(file_id)+".ifc"))
        file_id += 1
        m.files.append(database.file(id, ''))

    session.commit()
    session.close()

    if DEVELOPMENT or NO_REDIS:
        t = threading.Thread(target=lambda: worker.process(id, callback_url))

        t.start()
    else:
        q.enqueue(worker.process, id, callback_url)

    return id


def process_upload_validation(files, validation_config, user_id, commit_id=None, callback_url=None):

    ids = []
    filenames = []

    with database.Session() as session:
        for file in files:
            id = utils.generate_id()
            d = utils.storage_dir_for_id(id)
            fn = file.filename
            
            filenames.append(fn)
            ids.append(id)
            
            os.makedirs(d)
            file.save(os.path.join(d, id+".ifc"))
            session.add(database.model(id, fn, user_id, commit_id))
        session.commit()
   
        if not DEVELOPMENT:
            user = session.query(database.user).filter(database.user.id == user_id).all()[0]
            msg = f"{len(filenames)} file(s) were uploaded by user {user.name} ({user.email}): {(', ').join(filenames)}"
            utils.send_message(msg, [os.getenv("CONTACT_EMAIL")])

    if DEVELOPMENT or NO_REDIS:
        for id in ids:
            t = threading.Thread(target=lambda: worker.process(
                id, validation_config, commit_id=commit_id, callback_url=callback_url))
            t.start()
    else:
        for id in ids:
            q.enqueue(worker.process, id, validation_config, commit_id=commit_id, callback_url=callback_url)

    return ids


@application.route('/reprocess/<id>', methods=['POST'])
@login_required
def reprocess(user_data, id):
    ids = []

    with database.Session() as session:
        model = session.query(database.model).filter(database.model.code == code).all()[0]

        if model.user_id != user_data["sub"]:
            abort(403)

    if DEVELOPMENT:
        for id in ids:
            t = threading.Thread(target=lambda: worker.process(
                id, validation_config, callback_url))
            t.start()
    else:
        for id in ids:
            q.enqueue(worker.process, id, validation_config, callback_url)

    return ids

@application.route('/api/sandbox/<commit_id>', methods=['POST'])
@application.route('/api/', methods=['POST'])
@with_sandbox
@login_required
def put_main(user_data, pr_title, commit_id=None):
    if commit_id and not pr_manager.is_authorized_commit_id(commit_id):
        abort(404)

    ids = []
    files = []
    user_id = user_data["sub"]

    for key, f in request.files.items():
        if key.startswith('file'):
            file = f
            files.append(file)

    with open('config.json', 'r') as config_file:
        validation_config=json.loads(config_file.read())

    if VALIDATION:
        ids = process_upload_validation(files, validation_config, user_id, commit_id)
        if commit_id:
            arg = {'commit_id': commit_id}
        else:
            arg = {}
        
        if commit_id:
            url = f"/sandbox/dashboard/{commit_id}"
        else:
            url = "/dashboard"

    elif VIEWER:
        ids = process_upload_multiple(files)
        url = url_for('check_viewer', id="".join(ids))

    if request.accept_mimetypes.accept_json:
        return jsonify({"url": url})


@application.route('/p/<id>', methods=['GET'])
def check_viewer(id):
    if not utils.validate_id(id):
        abort(404)
    return render_template('progress.html', id=id)


@application.route('/sandbox/<commit_id>/dashboard', methods=['GET'])
@application.route('/api/dashboard', methods=['GET'])
@login_required
@with_sandbox
def dashboard(user_data, pr_title, commit_id=None):
    user_id = user_data['sub']
    # Retrieve user data
    with database.Session() as session:
        if str(user_data["email"]) in [os.getenv("ADMIN_EMAIL"), os.getenv("DEV_EMAIL")]:
            saved_models = session.query(database.model).filter(database.model.deleted!=1).all()
        else:
            saved_models = session.query(database.model).filter(database.model.user_id == user_id, database.model.deleted!=1).all()
        saved_models.sort(key=lambda m: m.date, reverse=True)
        saved_models = [model.serialize() for model in saved_models]

    return render_template('dashboard.html',
                           commit_id=commit_id,
                           pr_title=pr_title,
                           saved_models=saved_models,
                           username=f"{user_data.get('given_name', '')} {user_data.get('family_name', '')}"
                           )

@application.route('/sandbox/<commit_id>/models', methods=['GET'])
@application.route('/api/models', methods=['GET'])
@login_required
@with_sandbox
def models(user_data, pr_title, commit_id=None):
    user_id = user_data['sub']
    # Retrieve user data
    with database.Session() as session:
        if str(user_data["email"]) in [os.getenv("ADMIN_EMAIL"), os.getenv("DEV_EMAIL")]:
            saved_models = session.query(database.model).filter(database.model.deleted!=1).all()
        else:
            saved_models = session.query(database.model).filter(database.model.user_id == user_id, database.model.deleted!=1).all()
        saved_models.sort(key=lambda m: m.date, reverse=True)
        saved_models = [model.serialize() for model in saved_models]
    return jsonify({"models":saved_models})

@application.route('/sandbox/<commit_id>/models_paginated/<start>/<end>', methods=['GET'])
@application.route('/api/models_paginated/<start>/<end>', methods=['GET'])
@login_required
@with_sandbox
def models_paginated(user_data, start, end, pr_title, commit_id=None):
    user_id = user_data['sub']
    # Retrieve user data
    with database.Session() as session:
        if str(user_data["email"]) in [os.getenv("ADMIN_EMAIL"), os.getenv("DEV_EMAIL")]:
            saved_models = [m.serialize() for m in session.query(database.model).filter(database.model.deleted!=1).order_by(database.model.date.desc()).slice(int(start),int(end)).all()]
            count = session.query(database.model).filter(database.model.deleted!=1).count()
        else:
            saved_models = [m.serialize() for m in session.query(database.model).filter(database.model.user_id==user_id).filter(database.model.deleted!=1).order_by(database.model.date.desc()).slice(int(start),int(end)).all()]
            count = session.query(database.model).filter(database.model.user_id==user_id).filter(database.model.deleted!=1).count()
    return jsonify({"models":saved_models, "count":count})
  
@application.route('/valprog/<id>', methods=['GET'])
@login_required
def get_validation_progress(user_data, id):
    if not utils.validate_id(id):
        abort(404)

    all_ids = utils.unconcatenate_ids(id)

    model_progresses = []
    file_info = []
    with database.Session() as session:
        for i in all_ids:
            model = session.query(database.model).filter(database.model.code == i).all()[0]
            
            if model.user_id != user_data["sub"]:
                abort(404)

            file_info.append({"number_of_geometries": model.number_of_geometries,
                            "number_of_properties": model.number_of_properties})

            model_progresses.append(model.progress)

    return jsonify({"progress": model_progresses, "filename": model.filename, "file_info": file_info})


@application.route('/update_info/<code>', methods=['POST'])
@login_required
def update_info(user_data, code):
    try:  
        with database.Session() as session:
            model = session.query(database.model).filter(database.model.code == code).all()[0]

            if model.user_id != user_data["sub"]:
                abort(403)

            original_license = model.license
            data = request.get_data()
            user_data_data = json.loads(data)

            property = user_data_data["type"]
            setattr(model, property, user_data_data["val"])

            user = session.query(database.user).filter(database.user.id == model.user_id).all()[0]

            if user_data_data["type"] == "license":
                utils.send_message(f"User {user.name} ({user.email}) changed license of its file {model.filename} from {original_license} to {model.license}", [os.getenv("CONTACT_EMAIL")])
            session.commit()
        return jsonify( {"progress": data.decode("utf-8")})
    except:
        return jsonify( {"progress": "an error happened"})

@application.route('/error/<code>/', methods=['GET'])
@login_required
def error(user_data, code): 
    return render_template('error.html',username=f"{user_data.get('given_name', '')} {user_data.get('family_name', '')}")
   
@application.route('/pp/<id>', methods=['GET'])
def get_progress(id):
    if not utils.validate_id(id):
        abort(404)
    session = database.Session()
    model = session.query(database.model).filter(
        database.model.code == id).all()[0]
    session.close()
    return jsonify({"progress": model.progress})


@application.route('/log/<id>.<ext>', methods=['GET'])
def get_log(id, ext):
    log_entry_type = namedtuple(
        'log_entry_type', ("level", "message", "instance", "product"))

    if ext not in {'html', 'json'}:
        abort(404)

    if not utils.validate_id(id):
        abort(404)
    logfn = os.path.join(utils.storage_dir_for_id(id), "log.json")
    if not os.path.exists(logfn):
        abort(404)

    if ext == 'html':
        log = []
        for ln in open(logfn):
            l = ln.strip()
            if l:
                log.append(json.loads(l, object_hook=lambda d: log_entry_type(
                    *(d.get(k, '') for k in log_entry_type._fields))))
        return render_template('log.html', id=id, log=log)
    else:
        return send_file(logfn, mimetype='text/plain')


@application.route('/v/<id>', methods=['GET'])
def get_viewer(id):
    if not utils.validate_id(id):
        abort(404)
    d = utils.storage_dir_for_id(id)

    ifc_files = [os.path.join(d, name) for name in os.listdir(d) if os.path.isfile(os.path.join(d, name)) and name.endswith('.ifc')]

    if len(ifc_files) == 0:
        abort(404)

    failedfn = os.path.join(utils.storage_dir_for_id(id), "failed")
    if os.path.exists(failedfn):
        return render_template('error.html', id=id)

    for ifc_fn in ifc_files:
        glbfn = ifc_fn.replace(".ifc", ".glb")
        if not os.path.exists(glbfn):
            abort(404)

    n_files = len(ifc_files) if "_" in ifc_files[0] else None

    return render_template(
        'viewer.html',
        id=id,
        n_files=n_files,
        postfix=PIPELINE_POSTFIX
    )


@application.route('/reslogs/<i>/<ids>')
@login_required
def log_results(user_data, i, ids):
    all_ids = utils.unconcatenate_ids(ids)
    with database.Session() as session:
        model = session.query(database.model).filter(
            database.model.code == all_ids[int(i)]).all()[0]

        if model.user_id != user_data["sub"]:
            abort(403)

        response = {"results": {}, "time": None}

        response["results"]["syntaxlog"] = model.status_syntax
        response["results"]["schemalog"] = model.status_schema
        response["results"]["mvdlog"] = model.status_mvd
        response["results"]["bsddlog"] = model.status_bsdd
        response["results"]["idslog"] = model.status_ids

        response["results"]["ialog"] = model.status_ia
        response["results"]["iplog"] = model.status_ip

        response["time"] = model.serialize()['date']

    return jsonify(response)


class Error:
    def __init__(self, domain, classification, validation_constraints, validation_results, file_values):
        self.domain = domain
        self.classification = classification
        self.validation_constraints = validation_constraints
        self.validation_results = validation_results
        self.file_values = file_values
        self.instances = []

    def __eq__(self, other):
        return (self.domain == other.domain) and \
               (self.classification == other.classification) and \
               (self.validation_constraints == other.validation_constraints) and \
               (self.validation_results == other.validation_results)




@application.route('/api/report2/<code>')
@login_required
def view_report2(user_data, code):
    with database.Session() as session:
        session = database.Session()

        model = session.query(database.model).filter(
            database.model.code == code).all()[0]

        if model.user_id != user_data["sub"]:
            abort(403)

        tasks = {t.task_type: t for t in model.tasks}

        results = { "syntax_result":0, "schema_result":0, "bsdd_results":{"tasks":0, "bsdd":0, "instances":0}}
  
        if model.status_syntax != 'n':
            results["syntax_result"] = tasks["syntax_validation_task"].results[0].serialize()

        if model.status_schema != 'n':
            results["schema_result"] = tasks["schema_validation_task"].results[0].serialize()
            if not results["schema_result"]['msg']:
                results["schema_result"]['msg'] = "Valid"
    
        hierarchical_bsdd_results = {}
        if model.status_bsdd != 'n':
            hierarchical_bsdd_results = bsdd_utils.get_hierarchical_bsdd(model.code)
            results["bsdd_results"]["bsdd"] = hierarchical_bsdd_results
            bsdd_validation_task = tasks["bsdd_validation_task"]
            results["bsdd_results"]["task"] = bsdd_validation_task.serialize()
            results["bsdd_results"]["instances"] = len(model.instances) > 0

        tasks = {task_type: t.serialize(full=True) if (task_type == "informal_propositions_task" or task_type == "implementer_agreements_task") else  t.serialize() for task_type, t in tasks.items()}

    return jsonify({
         "model":model.serialize(),
         "tasks":tasks,
         "results":results
    })


@application.route('/results/<id>')
@login_required
def results(user_data, id):
    with database.Session() as session:
        session = database.Session()

        model = session.query(database.model).filter(
            database.model.code == id).all()[0]

        if model.user_id != user_data["sub"]:
            abort(403)

        tasks = {t.task_type: t for t in model.tasks}

        results = { "syntax_result":0, "schema_result":0, "bsdd_results":{"tasks":0, "bsdd":0, "instances":0}}
  
        if model.status_syntax != 'n':
            results["syntax_result"] = tasks["syntax_validation_task"].results[0].serialize()

        if model.status_schema != 'n':
            results["schema_result"] = tasks["schema_validation_task"].results[0].serialize()
            if not results["schema_result"]['msg']:
                results["schema_result"]['msg'] = "Valid"
    
        hierarchical_bsdd_results = {}
        if model.status_bsdd != 'n':
            hierarchical_bsdd_results = bsdd_utils.get_hierarchical_bsdd(model.code)
            results["bsdd_results"]["bsdd"] = hierarchical_bsdd_results
            bsdd_validation_task = tasks["bsdd_validation_task"]
            results["bsdd_results"]["task"] = bsdd_validation_task
            results["bsdd_results"]["instances"] = len(model.instances) > 0
  
    return jsonify({"model":model,
                    "tasks":tasks,
                    "results":results,
                    "username":f"{user_data.get('given_name', '')} {user_data.get('family_name', '')}"})


@application.route('/api/download/<id>', methods=['GET'])
@login_required
def download_model(user_data, id):
    with database.Session() as session:
        session = database.Session()
        model = session.query(database.model).filter(database.model.id == id).all()[0]
        if model.user_id != user_data["sub"]:
            abort(403)
        code = model.code
    path = utils.storage_file_for_id(code, "ifc")

    return send_file(path, download_name=model.filename, as_attachment=True, conditional=True)

@application.route('/api/delete/<id>', methods=['POST'])
@login_required
def delete(user_data, id):
    ids = [int(i) for i in id.split('.')]
    with database.Session() as session:
        session = database.Session()
        models = session.query(database.model).filter(database.model.id.in_(ids)).all()
        if set(m.user_id for m in models) != {user_data["sub"]}:
            abort(403)
        for model in models:
            model.deleted = 1
        session.commit()
    return jsonify({"status":"success", "id":id})

@application.route('/m/<fn>', methods=['GET'])
def get_model(fn):
    """
    Get model component
    ---
    parameters:
        - in: path
          name: fn
          required: true
          schema:
              type: string
          description: Model id and part extension
          example: BSESzzACOXGTedPLzNiNklHZjdJAxTGT.glb
    """

    id, ext = fn.split('.', 1)

    if not utils.validate_id(id):
        abort(404)

    if ext not in {"xml", "svg", "glb", "unoptimized.glb"}:
        abort(404)

    path = utils.storage_file_for_id(id, ext)

    if not os.path.exists(path):
        abort(404)

    if os.path.exists(path + ".gz"):
        import mimetypes
        response = make_response(
            send_file(path + ".gz",
                      mimetype=mimetypes.guess_type(fn, strict=False)[0])
        )
        response.headers['Content-Encoding'] = 'gzip'
        return response
    else:
        return send_file(path)

"""
# Create a file called routes.py with the following
# example content to add application-specific routes

from main import application

@application.route('/test', methods=['GET'])
def test_hello_world():
    return 'Hello world'
"""
try:
    import routes
except ImportError as e:
    pass