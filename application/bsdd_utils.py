import database
import json
import functools
import collections

from collections import defaultdict
from urllib.parse import urlparse

import ifcopenshell
import ifcopenshell.template

import checks.check_bsdd_v2

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

def get_processed_bsdd_table(bsdd_results, session, schema):
    """
    The function returns data for the 'bsdd data' table in a file metrics report. 
    More specifically,it returns a list of dictionaries containing the classifications (ifc instances, in this case) 
    and their valid/invalid counts.
    """
    bsdd_instances = [bsdd_table(result, session, schema) for result in bsdd_results]
    bsdd_data = defaultdict(lambda: {'valid': 0, 'invalid': 0, 'domain_source': 'classification not found'})

    for item in bsdd_instances:
        classification = item['classification']
        validity = item['validity']
        bsdd_data[classification][validity] += 1

    bsdd_data = [{**{'classification': k}, **v} for k, v in bsdd_data.items()]
    return bsdd_data

def bsdd_table(bsdd_result, session, schema):
    inst = get_inst(session, bsdd_result['instance_id'])
    observed_type = inst.ifc_type
    domain_source = bsdd_result['bsdd_classification_uri']

    if all(bsdd_result[key] == 1 for key in ['val_ifc_type', 'val_property_set', 'val_property_name', 'val_property_type', 'val_property_value']):
        validity = 'valid'
    else:
        validity = 'invalid'

    return {'classification': observed_type, 'validity': validity, 'domain_source': domain_source}

def get_inst(session, instance_id):
    return session.query(database.ifc_instance).filter(database.ifc_instance.id == instance_id).all()[0]

def get_classification_name(bsdd_results):
    default = 'name not found'
    names = list(filter(lambda x: x != default, [r['classification_name'] for r in bsdd_results]))
    return {item: names.count(item) for item in names} if names else default


def domain_sources(bsdd_results):
    uri = 'bsdd_classification_uri'
    domain_sources = [
        checks.check_bsdd_v2.get_domain(result[uri]).json()[0]['namespaceUri'] if result[uri] != 'classification not found'
        else result[uri]
        for result in bsdd_results
    ]
    sources = [source for source in domain_sources if source != 'classification not found']
    return collections.Counter(sources) if sources else 'classification not found'


def bsdd_report_quantity(bsdd_results, item):
    return sum(bool(bsdd_result.get(item)) for bsdd_result in bsdd_results)
