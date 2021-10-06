import sys, os
import json
import ifcopenshell


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.inspection import inspect
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import relationship
import os

ifc_fn = sys.argv[1]
ifc_file = ifcopenshell.open(ifc_fn)

try:
    #ifc_file.header.file_description.description[0].split(" ", 1)[1]
    detected_mvd = ifc_file.header.file_description.description[0].split(" ", 1)[1]
    detected_mvd = detected_mvd[1:]
    detected_mvd = detected_mvd[:-1]
    detected_mvd = detected_mvd.split(",")
except:
    detected_mvd = "no MVD detected"

try:
    authoring_app = ifc_file.by_type("IfcApplication")[0].ApplicationFullName
except:
    authoring_app = 'no authoring app detected'

file_info = {
    'size':str(round(os.path.getsize(sys.argv[1])*10**-6)) + "MB",
    'schema':ifc_file.schema,
    'app': authoring_app,
    'mvd': detected_mvd
    }

# Register info to DB
db_path = sys.argv[2]
sys.path.append(db_path)
import database

session = database.Session()
model = session.query(database.model).filter(database.model.code == ifc_fn[:-4]).all()[0]
model.size = file_info['size']
model.schema = file_info['schema']
model.app = file_info['app']
session.commit()
session.close()

results_path = os.path.join(os.getcwd(), "info.json")

with open(results_path, 'w', encoding='utf-8') as f:
    json.dump(file_info, f, ensure_ascii=False, indent=4)

