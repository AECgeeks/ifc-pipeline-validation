import requests
import json
import pprint
import ifcopenshell
from ifcopenshell.mvd import mvd
import itertools
import sys
import os 


ifc_fn = sys.argv[1]
ifc_file = ifcopenshell.open(ifc_fn)

mvd_fn= os.path.join(os.path.dirname(__file__), "ifcopenshell/mvd/mvd_examples/officials/ReferenceView_V1-2.mvdxml")

def get_xset_rule(mvd_fn, ifc_type, pset_or_qset):
    mvd_concept_roots = ifcopenshell.mvd.concept_root.parse(mvd_fn)
    for concept_root in mvd_concept_roots:
        if concept_root.entity == "IfcWall": #Modify mvdxml parsing to rather loop through CT
            for c in concept_root.concepts():
                if c.name == pset_or_qset:
                    for r in c.template().rules:
                        # print("  ", r.attribute)
                        if r.attribute == "IsDefinedBy":
                            return r

def get_ifc_types(file):
    return {e.is_a() for e in file.by_type("IfcBuildingElement")}



def pack_classification(classification_props):
    return classification_props['propertySet'], classification_props['name'], classification_props['dataType'] 

def pack_mvd(mvd_output):
    return list(mvd_output.values())[0], list(mvd_output.values())[1], list(mvd_output.values())[3].wrappedValue

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

score_calculation = {}

passed = 1

pset = 'Property Sets for Objects'
qset = 'Quantity Sets'

rule_tree = get_xset_rule(mvd_fn, 'IfcWall', pset)

types = get_ifc_types(ifc_file)

built_request = 'https://bs-dd-api-prototype.azurewebsites.net/api/Classification/v2?namespaceUri=http%3A%2F%2Fidentifier.buildingsmart.org%2Furi%2Fbuildingsmart%2Fifc-4.3%2Fclass%2F'
ifc_bsdd = {}

log_to_construct = {}

for t in types:
    if t == "IfcWallStandardCase":
        t = "IfcWall"

    log_to_construct[t] = {}
    r = requests.get(built_request+ t.lower())
    classification_result = json.loads(r.text) 
    rule_tree = get_xset_rule(mvd_fn, t, pset)
    
    if 'classificationProperties' in classification_result.keys():
        packed_properties = [pack_classification(p) for p in classification_result['classificationProperties'] if not p['propertySet'].startswith("Qto")]
        checking = {el:"Not present" for el in packed_properties}

        for instance in ifc_file.by_type(t):
            print("    ", instance.GlobalId)
            log_to_construct[t][instance.GlobalId] = []
            if len(mvd.extract_data(rule_tree, ifc_file.by_type(t)[0])) > 1:
                packed_output = [pack_mvd(d) for d in mvd.extract_data(rule_tree, ifc_file.by_type(t)[0])]
                to_compare = [packed_output, packed_properties]
                
                for mvd_data, bsdd_data in itertools.product(*to_compare):
                    match = mvd_data[0] == bsdd_data[0] and mvd_data[1] == bsdd_data[1]
                    if match:
                        if isinstance(mvd_data[2],simple_type_python_mapping[bsdd_data[2]]):
                            checking[bsdd_data] = mvd_data
                        else:
                            checking[bsdd_data] = 'wrong type'
                    else:
                        passed = 0

                for ck,cv in checking.items():
                    print("          ", ck, cv)
                    log_to_construct[t][instance.GlobalId].append((ck, cv,))
                
          
            else:
                passed = 0




jsonout = os.path.join(os.getcwd(), "dresult_bsdd.json")

with open(jsonout, 'w', encoding='utf-8') as f:
    json.dump(log_to_construct, f, ensure_ascii=False, indent=4)


jsonresultout = os.path.join(os.getcwd(), "result_bsdd.json")

if passed == 1:
    bsdd_result = {'bsdd':'v'}
elif passed == 0:
    bsdd_result = {'bsdd':'i'}


with open(jsonresultout, 'w', encoding='utf-8') as f:
    json.dump(bsdd_result, f, ensure_ascii=False, indent=4)


