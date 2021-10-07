import requests
import json
import pprint
import ifcopenshell
# from ifcopenshell.mvd import mvd
import ifcopenshell.util.element
import itertools
import sys
import os 
import time
import numpy as np
from Levenshtein import distance
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from helper import database

base_url = "https://bs-dd-api-prototype.azurewebsites.net/api/"

simple_type_python_mapping = {
        # @todo should include unicode for Python2
        "string": str,
        "integer": int,
        "real": float,
        "number": float,
        "Boolean": bool,
        "logical": bool,  # still not implemented in IfcOpenShell
        "binary": str,  # maps to a str of "0" and "1"
    }

def pack_classification(classification_props):
    return classification_props['propertySet'], classification_props['name'], classification_props['dataType'], classification_props['predefinedValue']

def pack_mvd(mvd_output):
    return list(mvd_output.values())[0], list(mvd_output.values())[1], list(mvd_output.values())[3].wrappedValue

def get_domain_fuzzy(domains, domain_ref, tolerance=50):
    #todo: check for case also
    idx = 0
    for i in range(len(domains)):
        #todo: Handle no match at all case
        #print(domains[i]['name'],fuzz.partial_ratio(domains[idx]['name'], domain_ref) ,fuzz.partial_ratio(domains[i]['name'], domain_ref) )
        if fuzz.partial_ratio(domains[i]['name'], domain_ref) > fuzz.partial_ratio(domains[idx]['name'], domain_ref):
            idx = i
    if fuzz.partial_ratio(domains[idx]['name'], domain_ref) > tolerance:
        return domains[idx]
    else:
        return 'The domain has not been found in the bSDD.'

def get_domains():
    url = "https://bs-dd-api-prototype.azurewebsites.net/api/Domain/v2"
    r = requests.get(url)
    return json.loads(r.text) 


def get_classifications(domain_uri):
    return json.loads(requests.get(base_url + "SearchListOpen/v2/", params={'DomainNamespaceUri': domain_uri}).text)
    

def get_classification(domain_ref, item_ref):
    domain_found = 0
    classification = 0
    for domain in get_domains():
        if domain['name'] == domain_ref:
            domain_uri = domain['namespaceUri']
            params = {'DomainNamespaceUri': domain_uri}
            list_of_classifications = json.loads(requests.get(base_url + "SearchListOpen/v2/", params=params).text)

            if list_of_classifications["numberOfClassificationsFound"] > 0:
                found_ref = 0
                for c in list_of_classifications['domains'][0]['classifications']:
                    # example_classification = [0]
                    ref = c['namespaceUri'].split("/")[-1]
                
                    if ref == item_ref:
                        found_ref = 1
                        return c
                    # else:
                    #     print('errr', ref, '  ', item_ref)
                    
                if found_ref == 0:
                    #print('No classification matched with the reference code provided' , '(',item_ref,')')
                    return 'No classification matched with the reference code provided.'

            else:
                #print('No classification found for the domain ', domain_ref)
                return 'No classification found for this domain.'
        
    if domain_found == 0:
        #print(domain_ref)
        print("The domain", domain_ref,"has not been found in the bSDD.")
        return 'This domain has not been found in the bSDD.'
   
def get_classification_object(uri):
    url = "https://bs-dd-api-prototype.azurewebsites.net/api/Classification/v3"
    base_url = "https://bs-dd-api-prototype.azurewebsites.net/api/"

    r = requests.get(url, {'namespaceUri':uri})
    return json.loads(r.text) 


def control_values(requirements, data):
    print(data)
    print(requirements)


def validate_consistency(ifc_file, validation_task_id):

    # import pdb; pdb.set_trace()
    validation_task_id = int(validation_task_id)

    # DB handling
    # session = database.Session()
    # validation_task = session.query(database.bsdd_validation_task).all()[0]
    # validation_task = session.query(database.bsdd_validation_task).filter(database.bsdd_validation_task.id == validation_task_id).all()[0]
    
    # session = database.Session()
    # bsdd_result = database.bsdd_result(validation_task_id)
    # session.add(bsdd_result)
    # session.commit()
    # session.close()


    rel_associate_classifications = ifc_file.by_type("IfcRelAssociatesClassification")
    log_to_construct = {}
    

    prog = 0

    n = len(rel_associate_classifications)

    if n:
        rnd_array = np.random.multinomial(100, np.ones(n)/n, size=1)[0]

        for idx, rel in enumerate(rel_associate_classifications):
            #import pdb; pdb.set_trace()
            sys.stdout.write(rnd_array[idx] * ".")
            sys.stdout.flush()
            #import pdb; pdb.set_trace()
            classification_reference = rel.RelatingClassification

            if ifc_file.schema == "IFC2X3":
                classification_reference_code = classification_reference.ItemReference
            else:
                classification_reference_code = classification_reference.Identification

            classification_reference_name = classification_reference.Name # Same

           
            classification = classification_reference.ReferencedSource #Same
                 # String matching between bsdd and IFC name
            if classification:
                classification_name = classification.Name
                domain_name = get_domain_fuzzy(get_domains(), classification_name)
            else:
            # todo: Handle the case NoneType' object has no attribute 'Name'
                domain_name = "no classification associated to the reference in the file"
                classification_name = "no classification associated to the reference in the file"
                
            
            if isinstance(domain_name, str):
                log_to_construct[classification_name] = domain_name
            else:   
                if domain_name['name'] not in log_to_construct.keys():
                    log_to_construct[domain_name['name']] = {}
        
                log_to_construct[domain_name['name']][classification_reference_name +"-"+classification_reference_code] = {}

                json_shortcut = log_to_construct[domain_name['name']][classification_reference_name +"-"+classification_reference_code]

                bsdd_response = get_classification(domain_name['name'], str(classification_reference_code))

                if not isinstance(bsdd_response, str):
                    bsdd_response = get_classification_object(bsdd_response['namespaceUri'])
                    
                    if 'classificationProperties' in bsdd_response.keys():
                        json_shortcut['requirements'] = {}
                        json_shortcut['types'] = []
                        json_shortcut['values'] = {}

                        json_shortcut['requirements'] = bsdd_response['classificationProperties']
                        json_shortcut['types'] = bsdd_response['relatedIfcEntityNames']
                        
                    
                        for e in rel.RelatedObjects:
                            #print(json_shortcut)
                            #Save in DB
                            session = database.Session()

                            bsdd_validation_task = session.query(database.bsdd_validation_task).filter(database.bsdd_validation_task.id == validation_task_id).all()[0]

                            instance = database.ifc_instance(e.GlobalId, e.is_a(), bsdd_validation_task.validated_file,)
                            session.add(instance)
                            session.flush()
                            instance_id = instance.id
                            session.commit()
                            session.close()



                            for p in json_shortcut['requirements']:

                                #import pdb; pdb.set_trace()
                                session = database.Session()

                                # bsdd_result = session.query(database.bsdd_result).filter(database.bsdd_result.id == bsdd_result_id).all()[0]
                                # bsdd_result.bsDD_classification_uri = bsdd_response['namespaceUri']
                                # bsdd_result.bsDD_property_uri = p['propertyNamespaceUri']
                                # bsdd_result.bsDD_property_constraint = str(p)
                                # session.commit()
                                # session.close()

                                bsdd_result = database.bsdd_result(validation_task_id, instance_id,bsdd_response['namespaceUri'],p['propertyNamespaceUri'],str(p) )
                                session.add(bsdd_result)
                                session.flush()
                                bsdd_result_id = bsdd_result.id
                            
                                session.commit()
                                session.close()
                         

                                if not e.GlobalId in  json_shortcut['values'].keys():
                                    json_shortcut['values'][e.GlobalId] = []

                                checking = {}
                                logging = {}

                                
                                # bSDD specifications
                                if 'name' in p.keys():
                                    pname_spec = p['name']
                                    checking["pname"] = 0
                                    logging["pname"] = 0
                                if 'propertySet' in p.keys():   
                                    pset_spec = p['propertySet']
                                    checking["pset"] = 0
                                    logging["pset"] = 0
                                if 'dataType' in p.keys():   
                                    ptype_spec = p['dataType']
                                    checking["ptype"] = 0
                                    logging["ptype"] = 0
                                if 'predefinedValue':
                                    pvalue_spec =  p['predefinedValue']
                                    checking["pvalue"] = 0
                                    logging["pvalue"] = 0
                                    if pvalue_spec == 'TRUE':
                                        pvalue_spec = True
                                    if pvalue_spec == 'FALSE':
                                        pvalue_spec = False

                                if pset_spec:
                                    props = ifcopenshell.util.element.get_psets(e)
                                    pset_instance = props.get(pset_spec)
                                   
                                    if pset_instance:
                                        checking["pset"] = 1
                                        logging["pset"] = pset_spec

                                        if pname_spec in pset_instance.keys():
                                            pvalue_instance = pset_instance.get(pname_spec) 
                                            checking["pname"] = 1
                                            logging["pname"] = pname_spec
                                            if pvalue_instance is not None:
                                               
                                                if pvalue_instance == pvalue_spec:
                                                    checking["pvalue"] = 1
                                                    logging["pvalue"] = pvalue_spec
                                                    
                                                else:
                                                    checking["pvalue"] = 0
                                                    logging["pvalue"] = "incorrect predefined value of %s instead of %s"%(pvalue_instance, pvalue_spec)
                                                
    
                                                if isinstance(pvalue_instance,simple_type_python_mapping[ptype_spec]):   
                                                    checking["ptype"] = 1
                                                    logging["ptype"] = ptype_spec
                                                else:
                                                    #import pdb; pdb.set_trace()
                                                    checking["ptype"] = 0
                                                    logging["ptype"] = "incorrect type of %s instead of %s"%(str(type(pvalue_instance)), ptype_spec)

                                        else:
                                            checking["pname"] = 0
                                            logging["pname"] = "property %s not found in property set"%(pname_spec)
                                            
                                
                                else:
                                    checking["pset"] = 0
                                    logging["pset"] = "no pset specified in bSDD classification"





                                di = {"checking":checking, "logging":logging, "failing":round(1 - sum(checking.values())/len(checking.keys()),2)}
                                
                                session = database.Session()
                                bsdd_result = session.query(database.bsdd_result).filter(database.bsdd_result.id == bsdd_result_id).all()[0]
                                bsdd_result.ifc_property_name = di['logging']['pname']
                                bsdd_result.ifc_property_set = di['logging']['pset']
                                bsdd_result.ifc_property_type = di['logging']['ptype']
                                bsdd_result.ifc_property_value = di['logging']['pvalue']
                                session.commit()
                                session.close()

                                #print(di)

                                json_shortcut['values'][e.GlobalId].append(di)

    else:
        log_to_construct["status"] = "No classification detected in the file."


    detailed_results_path = os.path.join(os.getcwd(), "dresult_bsdd.json")

    with open(detailed_results_path, 'w', encoding='utf-8') as f:
        json.dump(log_to_construct, f, ensure_ascii=False, indent=4)
        

if __name__ == "__main__":
    start_time = time.time()

    # mvd_fn= os.path.join(os.path.dirname(__file__), "ifcopenshell/mvd/mvd_examples/xset.mvdxml")
    # rule_tree = get_xset_rule(mvd_fn, "pset")

    

    ifc_fn = sys.argv[1]
    ifc_file = ifcopenshell.open(ifc_fn)
    
    if sys.argv[2]:
        validation_task_id = sys.argv[2]

    validate_consistency(ifc_file, validation_task_id)
    # print("--- %s seconds ---" % (time.time() - start_time))

    results_path = os.path.join(os.getcwd(), "result_bsdd.json")

    # if passed == 1:
    #     bsdd_result = {'mvd':'v'}
    # elif passed == 0:
    #     bsdd_result = {'mvd':'i'}

    bsdd_result = {'mvd':'i'}

    try:
        config_path = os.path.join(os.getcwd(), "config.json")
        with open(config_path) as json_file:
            config = json.load(json_file)

            config["results"]["bsddlog"] = "v"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    
    except:
        pass

    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(bsdd_result, f, ensure_ascii=False, indent=4)
    









