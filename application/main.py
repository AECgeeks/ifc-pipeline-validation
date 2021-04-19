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
import threading
from pathlib import Path

from collections import defaultdict, namedtuple
from flask_dropzone import Dropzone

from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, request, send_file, render_template, abort, jsonify, redirect, url_for, make_response
from flask_cors import CORS
from flask_basicauth import BasicAuth

from flasgger import Swagger

import utils
import worker
import database

application = Flask(__name__)
dropzone = Dropzone(application)

# application.config['DROPZONE_UPLOAD_MULTIPLE'] = True
# application.config['DROPZONE_PARALLEL_UPLOADS'] = 3

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


application.config['BASIC_AUTH_USERNAME'] = 'admin'
application.config['BASIC_AUTH_PASSWORD'] = 'bim'
application.config['BASIC_AUTH_FORCE'] = True
basic_auth = BasicAuth(application)

@application.route('/', methods=['GET'])
def get_main():
    return render_template('index.html')
    #return send_file("bsddlog.json", mimetype='text/plain')


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


def process_upload_validation(files,validation_config, callback_url=None):
    print("MAIddddddddddddddddddddddddddddddN", threading.current_thread().__class__.__name__)
    # assert threading.current_thread() is threading.main_thread()
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
            t = threading.Thread(target=lambda: worker.process(id, validation_config, callback_url))
            t.start()
    else:
        for id in ids:
            q.enqueue(worker.process, id, validation_config, callback_url)

    
    return ids


@application.route('/', methods=['POST'])
def put_main():
 
    ids = []
    files = []

    # import pdb;pdb.set_trace()

    for key, f in request.files.items():
        if key.startswith('file'):
            file = f
            files.append(file)    

    validation_config = request.form.to_dict()

    if VALIDATION:
        ids = process_upload_validation(files, validation_config)
    elif VIEWER:
        ids = process_upload_multiple(files)

    idstr = ""
    for i in ids:
        idstr += i

    if VALIDATION:
        url = url_for('validate_files', id=idstr) 
    
    elif VIEWER:
        url = url_for('check_viewer', id=idstr) 

    if request.accept_mimetypes.accept_json:
        return jsonify({"url":url})
    else:
        return redirect(url)




@application.route('/idschecking', methods=['GET'])
def ids_front():
    return "IFC input for IDS validation"



@application.route('/p/<id>', methods=['GET'])
def check_viewer(id):
    if not utils.validate_id(id):
        abort(404)
    return render_template('progress.html', id=id)    
    


@application.route('/val/<id>', methods=['GET'])
def validate_files(id):
    # if not utils.validate_id(id):
    #     abort(404)
    n_files = int(len(id)/32)
    all_ids = []
    b = 0
    i = 1
    a = 32
    for d in range(n_files):
        token = id[b:a]
        all_ids.append(token)
        b = a
        i+= 1
        a = 32*i
        
    filenames = []

    for i in all_ids:
        session = database.Session()
        model = session.query(database.model).filter(database.model.code == i).all()[0]
        filenames.append(model.filename)
        session.close()

    return render_template('validation.html', id=id, n_files=n_files, filenames=filenames)     
    
    
@application.route('/valprog/<id>', methods=['GET'])
def get_validation_progress(id):
    if not utils.validate_id(id):
        abort(404)
    
    n_ids = int(len(id)/32)

    count = 0
    all_ids = []
    b = 0
    i = 1
    a = 32
    for d in range(n_ids):
        token = id[b:a]
        all_ids.append(token)
        # count += 1
        b = a
        i+=1
        a = 32*i
        
    model_progresses = []

    for i in all_ids:
        session = database.Session()
        model = session.query(database.model).filter(database.model.code == i).all()[0]
        model_progresses.append(model.progress)
        session.close()

    return jsonify({"progress": model_progresses,"filename":model.filename})


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
    # d = utils.storage_dir_for_id(id)
    # input_files = [name for name in os.listdir(d) if os.path.isfile(os.path.join(d, name))]
    print("i", i)
    print("ids", ids)
    n_ids = int(len(ids)/32)

    all_ids = []
    b = 0
    j = 1
    a = 32
    for d in range(n_ids):
        token = ids[b:a]
        all_ids.append(token)
        # count += 1
        b = a
        j+=1
        a = 32*j
        

  
    # result_logs = {  
    #     'syntaxlog' : os.path.join(utils.storage_dir_for_id(all_ids[int(i)]), "result_syntax.json"),
    #     'schemalog': os.path.join(utils.storage_dir_for_id(all_ids[int(i)]), "result_schema.json"),
    #     'mvdlog' : os.path.join(utils.storage_dir_for_id(all_ids[int(i)]), "result_mvd.json"),
    #     'bsddlog' : os.path.join(utils.storage_dir_for_id(all_ids[int(i)]), "result_bsdd.json")

    # }


    # for k, v in result_logs.items():
    #     with open(v) as json_file:
    #         data = json.load(json_file)
    #         result_logs[k] = list(data.values())[0]
    
    
    # return jsonify({"schema": "v", "mvd":"w", "bsdd":"v"})
    return jsonify({'bsddlog': "i",'mvdlog': "i", 'schemalog': "v",'syntaxlog': "v"})
    # return jsonify(result_logs)


@application.route('/report/<id>/<ids>/<fn>')
def view_report(id,ids,fn):
    n_ids = int(len(ids)/32)

    all_ids = []
    b = 0
    j = 1
    a = 32
    for d in range(n_ids):
        token = ids[b:a]
        all_ids.append(token)
        # count += 1
        b = a
        j+=1
        a = 32*j
    

    f = os.path.join(utils.storage_dir_for_id(all_ids[int(id)]), "info.json")
    bsdd_json = os.path.join(utils.storage_dir_for_id(all_ids[int(id)]), "dresult_bsdd.json")


    with open(f) as json_file:
        info = json.load(json_file)

    with open(bsdd_json) as json_file:
        bsdd_result = json.load(json_file)

    return render_template('new_report.html', info=info, fn=fn, bsdd_result=bsdd_result)



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
