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
from pathlib import Path

import datetime

from collections import defaultdict, namedtuple
from redis.client import parse_client_list
from sqlalchemy.ext import declarative

from werkzeug import datastructures
from flask_dropzone import Dropzone

from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, request, session, send_file, render_template, abort, jsonify, redirect, url_for, make_response
from flask_cors import CORS
from flask_basicauth import BasicAuth

from flasgger import Swagger

import requests
from requests_oauthlib import OAuth2Session
from authlib.jose import jwt

from . import utils
from . import database
from . import worker
# import utils
# import worker
# import database

application = Flask(__name__)
dropzone = Dropzone(application)

# application.config['DROPZONE_UPLOAD_MULTIPLE'] = True
# application.config['DROPZONE_PARALLEL_UPLOADS'] = 3

# Trying to fix the secret key issue
application.config['SESSION_TYPE'] = 'filesystem'
application.config['SECRET_KEY'] = 'O5vB0ishUSFmXhyOGGk0zZJgcXhVnc2M6dZLHXzBoxo'

DEVELOPMENT = os.environ.get('environment', 'production').lower() == 'development'

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

if not DEVELOPMENT:
    from redis import Redis
    from rq import Queue

    q = Queue(connection=Redis(host=os.environ.get("REDIS_HOST", "localhost")), default_timeout=3600)


# application.config['BASIC_AUTH_USERNAME'] = 'admin'
# application.config['BASIC_AUTH_PASSWORD'] = 'bim'
# application.config['BASIC_AUTH_FORCE'] = True
# basic_auth = BasicAuth(application)



if not DEVELOPMENT:
    # LOGIN
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    # Credentials you get from registering a new application
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    authorization_base_url = 'https://buildingsmartservices.b2clogin.com/buildingsmartservices.onmicrosoft.com/b2c_1a_signupsignin_c/oauth2/v2.0/authorize'
    token_url = 'https://buildingSMARTservices.b2clogin.com/buildingSMARTservices.onmicrosoft.com/b2c_1a_signupsignin_c/oauth2/v2.0/token'

    redirect_uri = 'https://validate-bsi-staging.aecgeeks.com/callback'


@application.route("/")
def index():
    if not DEVELOPMENT:
        return redirect(url_for('login')) 
    else:

        
        with open('decoded.json') as json_file:
            decoded = json.load(json_file)

        session = database.Session()
        user = session.query(database.user).filter(database.user.id == decoded["aud"]).all()
        if len(user) == 0:
            session.add(database.user(str(decoded["aud"]), str(decoded["email"]), str(decoded["family_name"]),str(decoded["given_name"]),str(decoded["name"])))
            session.commit()
            session.close()
        else:
            print(user)
        #todo: query database to send information JSON



        return render_template('index.html', decoded=decoded) 
        
@application.route('/login', methods=['GET'])
def login():
    bs = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=["openid profile","https://buildingSMARTservices.onmicrosoft.com/api/read"])
    authorization_url, state = bs.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return redirect(authorization_url)
    
@application.route("/callback")
def callback():
    bs = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri=redirect_uri, scope=["openid profile","https://buildingSMARTservices.onmicrosoft.com/api/read"])
    t = bs.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url, response_type="token")
    BS_DISCOVERY_URL = (
    "https://buildingSMARTservices.b2clogin.com/buildingSMARTservices.onmicrosoft.com/b2c_1a_signupsignin_c/v2.0/.well-known/openid-configuration"
    )

    session['oauth_token'] = t
    
    # Get claims thanks to openid
    discovery_response = requests.get(BS_DISCOVERY_URL).json()
    key = requests.get(discovery_response['jwks_uri']).content.decode("utf-8")
    id_token = t['id_token']

    decoded = jwt.decode(id_token, key=key)
    
    db_session = database.Session()
    user = db_session.query(database.user).filter(database.user.id == decoded["aud"]).all()
    if len(user) == 0:
        db_session.add(database.user(str(decoded["aud"]), str(decoded["email"]), str(decoded["family_name"]),str(decoded["given_name"]),str(decoded["name"])))
        db_session.commit()
        db_session.close()
    else:
        print(user)
        #todo: query database to send information JSON

    return render_template('index.html', decoded=decoded)
    #return redirect(url_for('menu'))



def process_upload(filewriter, callback_url=None):
    
    id = utils.generate_id()
    d = utils.storage_dir_for_id(id)
    os.makedirs(d)
    
    filewriter(os.path.join(d, id+".ifc"))
    
    session = database.Session()
    session.add(database.model(id, 'test'))
    session.commit()
    session.close()
    
    if DEVELOPMENT:
        
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
        filewriter = lambda fn: file.save(fn)
        filewriter(os.path.join(d, id+"_"+str(file_id)+".ifc"))
        file_id += 1
        m.files.append(database.file(id, ''))
    
    session.commit()
    session.close()
    
    if DEVELOPMENT:
        t = threading.Thread(target=lambda: worker.process(id, callback_url))
        t.start()        
    else:
        q.enqueue(worker.process, id, callback_url)

    return id


def process_upload_validation(files,validation_config,user_id, callback_url=None):
    
    ids = []
    for file in files:
        fn = file.filename
        filewriter = lambda fn: file.save(fn)
        id = utils.generate_id()
        ids.append(id)
        d = utils.storage_dir_for_id(id)
        os.makedirs(d)
        filewriter(os.path.join(d, id+".ifc"))
        session = database.Session()
        session.add(database.model(id, fn, user_id))

        session.commit()
        session.close()
    
    if DEVELOPMENT:
        for id in ids:
            t = threading.Thread(target=lambda: worker.process(id, validation_config, callback_url))
            t.start()
    else:
        for id in ids:
            q.enqueue(worker.process, id, validation_config, callback_url)

    
    return ids


def process_upload_validation_ids(files,validation_config, ids_spec, callback_url=None):
    
    ids = []
    for file in files:
        fn = file.filename
        filewriter = lambda fn: file.save(fn)
        id = utils.generate_id()
        ids.append(id)
        d = utils.storage_dir_for_id(id)
        os.makedirs(d)
        filewriter(os.path.join(d, id+".ifc"))
        session = database.Session()
        session.add(database.model(id, fn))
        session.commit()
        session.close()
    
    if DEVELOPMENT:
        for id in ids:
            t = threading.Thread(target=lambda: worker.process(id, validation_config, ids_spec,callback_url ))
            t.start()
    else:
        for id in ids:
            q.enqueue(worker.process, id, validation_config, ids_spec,callback_url)

    
    return ids


def upload_ids(files,validation_config, callback_url=None):
    
    ids = []
    for file in files:
        fn = file.filename
        filewriter = lambda fn: file.save(fn)
        id = utils.generate_id()
        ids.append(id)
        d = utils.storage_dir_for_id(id)
        os.makedirs(d)
        filewriter(os.path.join(d, id+".xml"))
        session = database.Session()
        session.add(database.model(id, fn))
        session.commit()
        session.close()
    
    # if DEVELOPMENT:
    #     for id in ids:
    #         t = threading.Thread(target=lambda: worker.process(id, validation_config, callback_url))
    #         t.start()
    # else:
    #     for id in ids:
    #         q.enqueue(worker.process, id, validation_config, callback_url)

    return ids

def process_ids(files,validation_config, callback_url=None):
    ids = []
    for file in files:
        fn = file.filename
        filewriter = lambda fn: file.save(fn)
        id = utils.generate_id()
        ids.append(id)
        d = utils.storage_dir_for_id(id)
        os.makedirs(d)
        filewriter(os.path.join(d, id+".xml"))
        session = database.Session()
        session.add(database.model(id, fn))
        session.commit()
        session.close()

    # if DEVELOPMENT:
    #     for id in ids:
    #         t = threading.Thread(target=lambda: worker.process(id, validation_config, callback_url))
    #         t.start()
    # else:
    #     for id in ids:
    #         q.enqueue(worker.process, id, validation_config, callback_url)

    return ids

@application.route('/', methods=['POST'])
def put_main():
 
    ids = []
    files = []

    user_id = request.form.to_dict()["user"]

    extensions = set()

    for key, f in request.files.items():
        
        if key.startswith('file'):
            file = f
            files.append(file)    

            if file.filename.endswith('.xml'):
                extensions.add('xml')
            if file.filename.endswith('.ifc'):
                extensions.add('ifc')
           
    val_config = request.form.to_dict()
    val_results = {k + "log":'n' for (k,v) in val_config.items() if k != "user"}
    
    validation_config = {}
    validation_config["config"] = val_config
    del val_config["user"]
    validation_config["results"] = val_results

    # import pdb; pdb.set_trace()

    if VALIDATION:
        if 'xml' in extensions:
            ids = upload_ids(files, validation_config)
        else:
            ids = process_upload_validation(files, validation_config, user_id)

    elif VIEWER:
        ids = process_upload_multiple(files)

    idstr = ""
    for i in ids:
        idstr += i

    if VALIDATION:
        if 'xml' in extensions:
            url = url_for('ids_front', id=idstr)
        else:
            url = url_for('validate_files', id=idstr, user_id=user_id) 
    
    elif VIEWER:
        url = url_for('check_viewer', id=idstr) 

    if request.accept_mimetypes.accept_json:
        return jsonify({"url":url})
    # else:
    #     return redirect(url)



@application.route('/checkids/<test>', methods=['POST'])
def put_main2(test):
    ids = []
    files = []

    extensions = set()

    for key, f in request.files.items():
        if key.startswith('file'):
            file = f
            files.append(file)    
            if file.filename.endswith('.xml'):
                extensions.add('xml')
            if file.filename.endswith('.ifc'):
                extensions.add('ifc')
           
    val_config = request.form.to_dict()
    val_results = {k + "log":'n' for (k,v) in val_config.items()}
    
    validation_config = {}
    validation_config["config"] = val_config
    validation_config["results"] = val_results



    if VALIDATION:
        if 'xml' in extensions:
            ids = upload_ids_ids(files, validation_config, test)
        else:
            ids = process_upload_validation_ids(files, validation_config, test)

    elif VIEWER:
        ids = process_upload_multiple(files)

    idstr = ""
    for i in ids:
        idstr += i

    if VALIDATION:
        if 'xml' in extensions:
            url = url_for('ids_front', id=idstr)
        else:
            url = url_for('validate_files', id=idstr, user_id=request.form.to_dict()["user"]) 
    
    elif VIEWER:
        url = url_for('check_viewer', id=idstr) 

    if request.accept_mimetypes.accept_json:
        return jsonify({"url":url})


@application.route('/idschecking/<id>', methods=['GET', 'POST'])
def ids_front(id):

    if request.method == 'GET':
        all_ids = utils.unconcatenate_ids(id)
        n_files = int(len(id)/32)
            
        filenames = []

        for i in all_ids:
            session = database.Session()
            model = session.query(database.model).filter(database.model.code == i).all()[0]
            filenames.append(model.filename)
            session.close()

        return render_template('ids.html', id=id, filenames=filenames)

  
@application.route('/p/<id>', methods=['GET'])
def check_viewer(id):
    if not utils.validate_id(id):
        abort(404)
    return render_template('progress.html', id=id)    
    


@application.route('/val/<id>/<user_id>', methods=['GET'])
def validate_files(id, user_id):
    # if not utils.validate_id(id):
    #     abort(404)

    all_ids = utils.unconcatenate_ids(id)

    n_files = int(len(id)/32)
            
    filenames = []

    for i in all_ids:
        session = database.Session()
        model = session.query(database.model).filter(database.model.code == i).all()[0]
        filenames.append(model.filename)
        session.close()

    return render_template('validation.html', id=id, n_files=n_files, filenames=filenames, user_id =user_id )     
    
    
@application.route('/valprog/<id>', methods=['GET'])
def get_validation_progress(id):
    if not utils.validate_id(id):
        abort(404)

    all_ids = utils.unconcatenate_ids(id)
        
    model_progresses = []

    for i in all_ids:
        session = database.Session()
        model = session.query(database.model).filter(database.model.code == i).all()[0]
        model_progresses.append(model.progress)
        session.close()

    return jsonify({"progress": model_progresses,"filename":model.filename})


@application.route('/update_info/<ids>/<number>/<user_id>', methods=['POST'])
def register_info_input(ids, number, user_id):
    data =  request.get_data()
    decoded_data = ast.literal_eval(data.decode("utf-8"))
    i = decoded_data['n']
    # license = decoded_data['license']    
    all_ids = utils.unconcatenate_ids(ids)

    session = database.Session()
    model = session.query(database.model).filter(database.model.code == all_ids[i]).all()[0]
    
    #import pdb;pdb.set_trace()

    if decoded_data["type"] == "licenses":
        model.license = decoded_data['license']

    if decoded_data["type"] == "hours":
        model.hours = decoded_data['hours']

    if decoded_data["type"] == "details":
        model.details = decoded_data['details']

    session.commit()
    session.close()

    return jsonify({"progress":data.decode("utf-8")})
    


@application.route('/pp/<id>', methods=['GET'])
def get_progress(id):
    if not utils.validate_id(id):
        abort(404)
    session = database.Session()
    model = session.query(database.model).filter(database.model.code == id).all()[0]
    session.close()
    return jsonify({"progress": model.progress})


@application.route('/log/<id>.<ext>', methods=['GET'])
def get_log(id, ext):
    log_entry_type = namedtuple('log_entry_type', ("level", "message", "instance", "product"))
    
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
                log.append(json.loads(l, object_hook=lambda d: log_entry_type(*(d.get(k, '') for k in log_entry_type._fields))))
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
def log_results(i, ids):

    all_ids = utils.unconcatenate_ids(ids)

    # The results will be passed with the config file
    config_file = os.path.join(utils.storage_dir_for_id(all_ids[int(i)]), "config.json")
    with open(config_file) as json_file:
        config = json.load(json_file)


    time = datetime.datetime.now()
    time = time.strftime("%Y-%m-%d %H:%M:%S")
    config["time"] = time

    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
        

    #import pdb; pdb.set_trace()

    return jsonify(config)
    


@application.route('/report/<id>/<ids>/<fn>')
def view_report(id,ids,fn):

    all_ids = utils.unconcatenate_ids(ids)

    f = os.path.join(utils.storage_dir_for_id(all_ids[int(id)]), "info.json")
    with open(f) as json_file:
        info = json.load(json_file)

    

    config_file = os.path.join(utils.storage_dir_for_id(all_ids[int(id)]), "config.json")
    with open(config_file) as json_file:
        config = json.load(json_file)
    

    for cfg, val in config["config"].items():
        val = int(val)
    
        if cfg == 'syntax':
            if val:
                print("todo get the %s checking log" % (cfg))
            else:
                print("%s not validated" % (cfg)) 
        if cfg == 'schema':
            if val:
                print("todo get the %s checking log" % (cfg))
            else:
                print("%s not validated" % (cfg))

        if cfg == 'mvd':
            if val:
                print("todo get the %s checking log" % (cfg))
            else:
                print("%s not validated" % (cfg))
        
        if cfg == 'bsdd':
            if val:
                print("todo get the %s checking log" % (cfg))
                bsdd_json = os.path.join(utils.storage_dir_for_id(all_ids[int(id)]), "dresult_bsdd.json")  
                with open(bsdd_json) as json_file:
                    bsdd_result = json.load(json_file)
            
            else:
                print("%s not validated" % (cfg))
                bsdd_result = {'status': 0 }
        
        if cfg == 'ids':
            if val:
                print("todo get the %s checking log" % (cfg))
                ids_output = os.path.join(utils.storage_dir_for_id(all_ids[int(id)]), "ids.txt")
                with open(ids_output) as ids_file:
                    ids_result = ids_file.readlines()
                    ids_to_pass = []
                    for l in ids_result:
                        if "'" in l:
                            l = l.replace("'", '"')
                            l = l.replace("[classification_eval_todo]", "classification_eval_todo")
                            ids_to_pass.append(l)

                        else:
                            ids_to_pass.append(l)
            else:
                ids_to_pass = {'status':0}
                print("%s not validated" % (cfg))


                        
    #import pdb; pdb.set_trace()
    return render_template('new_report.html', info=info, fn=fn, bsdd_result=bsdd_result, ids_result = ids_to_pass, config=config)



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
