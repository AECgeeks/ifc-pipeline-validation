import database
import json
import functools

def get_hierarchical_bsdd(id):
    with database.Session() as session:
        @functools.lru_cache(maxsize=128)
        def get_inst(instance_id):
            return session.query(database.ifc_instance).filter(database.ifc_instance.id == instance_id).all()[0]

        model = session.query(database.model).filter(
            database.model.code == id).all()[0]
        
        bsdd_task = [task for task in model.tasks if task.task_type == "bsdd_validation_task"][0]
        hierarchical_bsdd_results = {}
        if model.status_bsdd != 'n':
            for bsdd_result in bsdd_task.results:
                
                bsdd_result = bsdd_result.serialize()
             
                if bsdd_result["instance_id"]:
                    inst = get_inst(bsdd_result["instance_id"])
                    bsdd_result['global_id'], bsdd_result['ifc_type'] = inst.global_id, inst.ifc_type

                if bsdd_result["bsdd_property_constraint"]:
                    # Quick fix to handle the case with no constraint
                    try:
                        bsdd_result["bsdd_property_constraint"] = json.loads(
                            bsdd_result["bsdd_property_constraint"])
                    except:
                        bsdd_result["bsdd_property_constraint"] = 0
                else:
                    bsdd_result["bsdd_property_constraint"] = 0

                if bsdd_result["domain_file"] not in hierarchical_bsdd_results.keys():
                    hierarchical_bsdd_results[bsdd_result["domain_file"]]= {}

                if bsdd_result["classification_file"] not in hierarchical_bsdd_results[bsdd_result["domain_file"]].keys():
                    hierarchical_bsdd_results[bsdd_result["domain_file"]][bsdd_result["classification_file"]] = []

                hierarchical_bsdd_results[bsdd_result["domain_file"]][bsdd_result["classification_file"]].append(bsdd_result)
    
    return hierarchical_bsdd_results     


import database
import json
import functools

from collections import defaultdict
from urllib.parse import urlparse

import ifcopenshell
import ifcopenshell.template

import utils

def get_hierarchical_bsdd(id):
    with database.Session() as session:
        @functools.lru_cache(maxsize=128)
        def get_inst(instance_id):
            return session.query(database.ifc_instance).filter(database.ifc_instance.id == instance_id).all()[0]

        model = session.query(database.model).filter(
            database.model.code == id).all()[0]
        
        bsdd_task = [task for task in model.tasks if task.task_type == "bsdd_validation_task"][0]
        hierarchical_bsdd_results = {}
        if model.status_bsdd != 'n':
            for bsdd_result in bsdd_task.results:
                
                bsdd_result = bsdd_result.serialize()
             
                if bsdd_result["instance_id"]:
                    inst = get_inst(bsdd_result["instance_id"])
                    bsdd_result['global_id'], bsdd_result['ifc_type'] = inst.global_id, inst.ifc_type

                if bsdd_result["bsdd_property_constraint"]:
                    # Quick fix to handle the case with no constraint
                    try:
                        bsdd_result["bsdd_property_constraint"] = json.loads(
                            bsdd_result["bsdd_property_constraint"])
                    except:
                        bsdd_result["bsdd_property_constraint"] = 0
                else:
                    bsdd_result["bsdd_property_constraint"] = 0

                if bsdd_result["domain_file"] not in hierarchical_bsdd_results.keys():
                    hierarchical_bsdd_results[bsdd_result["domain_file"]]= {}

                if bsdd_result["classification_file"] not in hierarchical_bsdd_results[bsdd_result["domain_file"]].keys():
                    hierarchical_bsdd_results[bsdd_result["domain_file"]][bsdd_result["classification_file"]] = []

                hierarchical_bsdd_results[bsdd_result["domain_file"]][bsdd_result["classification_file"]].append(bsdd_result)
    
    return hierarchical_bsdd_results     

def bsdd_data_processing(bsdd_task, bsdd_results, session):
    bsdd_instances = [bsdd_table(result.serialize(), session) for result in bsdd_task.results]
    bsdd_data = defaultdict(lambda: {'valid': 0, 'invalid': 0, 'source': get_domain(bsdd_results)})

    for item in bsdd_instances:
        classification = item['classification']
        validity = item['validity']
        bsdd_data[classification][validity] += 1

    bsdd_data = [{**{'classification': k}, **v} for k, v in bsdd_data.items()]
    return bsdd_data

def bsdd_table(bsdd_result, session):
    inst = get_inst(session, bsdd_result['instance_id'])
    observed_type = inst.ifc_type
    required_type = bsdd_result['bsdd_type_constraint']
    validity = "valid" if utils.do_try(lambda: ifcopenshell.template.create(schema_identifier="IFC4X3").create_entity(observed_type).is_a(required_type), 'invalid') else 'invalid'
    return {'classification': observed_type, 'validity': validity}

def get_inst(session, instance_id):
    return session.query(database.ifc_instance).filter(database.ifc_instance.id == instance_id).all()[0]

def get_domain(bsdd_results):
    domain_file = 'domain_file'
    uri = 'bsdd_classification_uri'
    domain_sources = []
    default = 'classification not found'
    for result in bsdd_results:
        bsdd_uri = result[uri]
        if bsdd_uri == default:
            domain_sources.append(bsdd_uri)
        else:
            parse = urlparse(bsdd_uri)
            parsed_domain_file = ''.join(char for char in result[domain_file] if char.isalnum()).lower()
            domain_part = [part for part in parse.path.split('/') if parsed_domain_file in part][0]
            url = parse.scheme + '/' + parse.netloc + '/' + 'uri' + '/' + domain_part + '/'
            domain_sources.append(url)
    sources = list(filter(lambda x: x != default, domain_sources))
    return sources[0] if sources else default

def bsdd_report_quantity(bsdd_task, item):
    return sum(bool(bsdd_result.serialize().get(item)) for bsdd_result in bsdd_task.results)
