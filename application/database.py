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

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.inspection import inspect
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import relationship
import os
from sqlalchemy.pool import StaticPool

DEVELOPMENT = os.environ.get('environment', 'production').lower() == 'development'

if DEVELOPMENT:
    file_path = os.path.dirname(__file__)+  "/ifc-pipeline.db"
    engine = create_engine('sqlite:///'+file_path, connect_args={'check_same_thread': False})
else:
    engine = create_engine('postgresql://postgres:postgres@%s:5432/bimsurfer2' % os.environ.get('POSTGRES_HOST', 'localhost'))
  
Session = sessionmaker(bind=engine)

Base = declarative_base()


class Serializable(object):
    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}


class user(Base, Serializable):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    email = Column(String)
    family_name = Column(String)
    given_name = Column(String)
    name = Column(String)
    # files = relationship("file") 
    models = relationship("model") 

    def __init__(self, id, email, family_name, given_name, name):
        self.id = id
        self.email = email
        self.family_name = family_name
        self.given_name = given_name
        self.name = name
        

class model(Base, Serializable):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True)
    code = Column(String)
    filename = Column(String)
    #files = relationship("file")
    user_id = Column(String, ForeignKey('users.id'))

    progress = Column(Integer, default=-1)
    date = Column(DateTime, server_default=func.now())

    license = Column(String, default="private")
    hours = Column(String)
    details = Column(String)

    number_of_geometries = Column(Integer)
    number_of_properties = Column(Integer)

    authoring_application = Column(String)
    schema = Column(String)
    size = Column(String)
    mvd = Column(String)

    instances = relationship("ifc_instance")


    # state_syntax = Column(String, default="n")
    # state_schema = Column(String, default="n")
    # state_mvd = Column(String, default="n")
    # state_bsdd = Column(String, default="n")
    # state_ids = Column(String, default="n")


    def __init__(self, code, filename, user_id):
        self.code = code
        self.filename = filename
        self.user_id = user_id


class file(Base, Serializable):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    code = Column(String)
    filename = Column(String)
 
    #model_id = Column(Integer, ForeignKey('models.id'))
    # user_id = Column(String, ForeignKey('users.id'))

    # progress = Column(Integer, default=-1)
    # date = Column(DateTime, server_default=func.now())
    # authoring_application = Column(String)
    # schema = Column(String)
    # production_hours = Column(String)
    # license = Column(String)
    # number_of_geometries = Column(String)
    # number_of_properties = Column(String)
    
    # size = Column(String)
    # app = Column(String)
    # mvd = Column(String)
    

    def __init__(self, code, filename):
        self.code = code
        self.filename = filename


class bsdd_validation_task(Base, Serializable):
    __tablename__ = 'bSDD_validation_tasks'

    id = Column(Integer, primary_key=True)
    validated_file = Column(Integer, ForeignKey('models.id'))
    validation_start_time = Column(DateTime)
    validation_end_time = Column(DateTime)

    results = relationship("bsdd_result")

    def __init__(self, validated_file):
        self.validated_file = validated_file
        #self.file_id = Column(Integer, ForeignKey('files.id'))



    
class ifc_instance(Base, Serializable):
    __tablename__ = 'instances'

    id = Column(Integer, primary_key=True)
    global_id = Column(String)
    file = Column(Integer, ForeignKey('models.id'))
    ifc_type = Column(String)
    bsdd_results = relationship("bsdd_result")
    
    def __init__(self, global_id, ifc_type, file):
        self.global_id = global_id
        self.ifc_type = ifc_type
        self.file = file


       
class bsdd_result(Base, Serializable):
    __tablename__ = 'bSDD_results'

    id = Column(Integer, primary_key=True)
    task_id = Column(String, ForeignKey('bSDD_validation_tasks.id'))
    instance_id = Column(Integer, ForeignKey('instances.id'))
    bsDD_classification_uri = Column(String)
    bsDD_property_uri = Column(String)
    bsDD_property_constraint = Column(String)
    ifc_property_id = Column(String)
    ifc_property_set = Column(String)
    ifc_property_type = Column(String)
    ifc_property_value = Column(String)

    

    def __init__(self, task_id,instance_id ):
        self.task_id = task_id
        self.instance_id = instance_id

       


        
def initialize():
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)


if __name__ == "__main__" or DEVELOPMENT:
    initialize()
