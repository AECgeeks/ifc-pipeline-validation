import requests
import json
import pprint
import ifcopenshell
from ifcopenshell.mvd import mvd
import itertools
import sys
import os 
import time
from Levenshtein import distance
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

base_url = "https://bs-dd-api-prototype.azurewebsites.net/api/"

def pack_classification(classification_props):
    return classification_props['propertySet'], classification_props['name'], classification_props['dataType'], classification_props['predefinedValue']

def pack_mvd(mvd_output):
    return list(mvd_output.values())[0], list(mvd_output.values())[1], list(mvd_output.values())[3].wrappedValue


def get_xset_rule(mvd_fn, pset_or_qset):
    concept_root = list(ifcopenshell.mvd.concept_root.parse(mvd_fn))[0]
    for c in concept_root.concepts():
        if c.name == pset_or_qset:
            for r in c.template().rules:
                # print(r)
                if r.attribute == "IsDefinedBy":
                    return r

def get_domain_fuzzy(domains, domain_ref):
    idx = 0
    for i in range(len(domains)):
        if fuzz.partial_ratio(domains[i]['name'], domain_ref) > fuzz.partial_ratio(domains[idx]['name'], domain_ref):
            idx = i

    return domains[idx]

def get_domains():
    url = "https://bs-dd-api-prototype.azurewebsites.net/api/Domain/v2"
    r = requests.get(url)
    return json.loads(r.text) 


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
                    print('No classification matched with the reference code provided' , '(',item_ref,')')
                    return 'No classification matched with the reference code provided.'

            else:
                print('No classification found for the domain ', domain_ref)
                return 'No classification found for this domain.'
        
    if domain_found == 0:
        print(domain_ref)
        print("The domain", domain_ref,"has not been found in the bSDD.")
        return 'This domain has not been found in the bSDD.'

        
def get_classification_object(uri):
    url = "https://bs-dd-api-prototype.azurewebsites.net/api/Classification/v2"
    base_url = "https://bs-dd-api-prototype.azurewebsites.net/api/"

    r = requests.get(url, {'namespaceUri':uri})
    return json.loads(r.text) 
    

def validate_consistency(ifc_file):
    rel_associate_classifications = ifc_file.by_type("IfcRelAssociatesClassification")
    log_to_construct = {}

    for rel in rel_associate_classifications:
        classification_reference = rel.RelatingClassification
        classification_reference_code = classification_reference.ItemReference
        classification_reference_name = classification_reference.Name
        classification = classification_reference.ReferencedSource
        classification_name = classification.Name
        
        # String matching as between bsdd and IFC name
        classification_name2 = get_domain_fuzzy(get_domains(), classification_name)
        log_to_construct[classification_reference_name +"-"+classification_reference_code] = {}
        bsdd_response = get_classification(classification_name2['name'], str(classification_reference_code))

        if not isinstance(bsdd_response, str):
            bsdd_response = get_classification_object(bsdd_response['namespaceUri'])
            
            if 'classificationProperties' in bsdd_response.keys():
                classification_properties = bsdd_response['classificationProperties']
                packed_properties = [pack_classification(p) for p in bsdd_response['classificationProperties']]

                for e in rel.RelatedObjects:
                    log_to_construct[rel.RelatingClassification.Name +"-"+classification_reference_code][e.GlobalId] = []
                    packed_output = [pack_mvd(d) for d in mvd.extract_data(rule_tree, e)]

                    to_compare = [packed_output, packed_properties]
                    match = 0
                    for mvd_data, bsdd_data in itertools.product(*to_compare):
                        match = mvd_data[0] == bsdd_data[0] and mvd_data[1] == bsdd_data[1]

                        if match:
                            if isinstance(mvd_data[2],simple_type_python_mapping[bsdd_data[2]]):
                                compval = bsdd_data[3]

                                if bsdd_data[3] == 'TRUE':
                                    compval = True

                                elif bsdd_data[3] == 'FALSE':
                                    compval = False
                                
                                if mvd_data[2] == compval:
                                    log_to_construct[rel.RelatingClassification.Name +"-"+classification_reference_code][e.GlobalId].append((mvd_data, bsdd_data,  'PASSED',))

                                elif isinstance(compval,str):
                                    if not len(compval):
                                    
                                        log_to_construct[rel.RelatingClassification.Name +"-"+classification_reference_code][e.GlobalId].append((mvd_data, bsdd_data,  'PASSED BUT ABSENT VALUE IN BSDD',)) 
                                else:
                                
                                    log_to_construct[rel.RelatingClassification.Name +"-"+classification_reference_code][e.GlobalId].append((mvd_data, bsdd_data,  'FAILED',)) 
                            else:
                            
                                log_to_construct[rel.RelatingClassification.Name +"-"+classification_reference_code][e.GlobalId].append((mvd_data, bsdd_data,  'FAILED - WRONG TYPE USED',)) 

                    if len(log_to_construct[rel.RelatingClassification.Name +"-"+classification_reference_code][e.GlobalId]) == 0 :
                    
                        log_to_construct[rel.RelatingClassification.Name +"-"+classification_reference_code][e.GlobalId] = [packed_properties,"NO WATCH WITH"]


    detailed_results_path = os.path.join(os.getcwd(), "dresult_bsdd.json")

    with open(detailed_results_path, 'w', encoding='utf-8') as f:
        json.dump(log_to_construct, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    start_time = time.time()

    mvd_fn= os.path.join(os.path.dirname(__file__), "ifcopenshell/mvd/mvd_examples/xset.mvdxml")
    rule_tree = get_xset_rule(mvd_fn, "pset")

    simple_type_python_mapping = {
        # @todo should include unicode for Python2
        "string": str,
        "integer": int,
        "real": float,
        "number": float,
        "boolean": bool,
        "logical": bool,  # still not implemented in IfcOpenShell
        "binary": str,  # maps to a str of "0" and "1"
    }


    ifc_fn = sys.argv[1]
    ifc_file = ifcopenshell.open(ifc_fn)

    validate_consistency(ifc_file)
    print("--- %s seconds ---" % (time.time() - start_time))

    results_path = os.path.join(os.getcwd(), "result_bsdd.json")

    # if passed == 1:
    #     bsdd_result = {'mvd':'v'}
    # elif passed == 0:
    #     bsdd_result = {'mvd':'i'}

    bsdd_result = {'mvd':'i'}

    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(bsdd_result, f, ensure_ascii=False, indent=4)
    









