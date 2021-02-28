import requests
import json
import pprint
import ifcopenshell
from ifcopenshell.mvd import mvd
import itertools
import sys
import os 

from anytree import Node, RenderTree


ifc_fn = sys.argv[1]
ifc_file = ifcopenshell.open(ifc_fn)

mvd_fn= os.path.join(os.path.dirname(__file__), "ifcopenshell/mvd/mvd_examples/officials/ReferenceView_V1-2.mvdxml")

def get_xset_rule(mvd_fn, ifc_type, pset_or_qset):
    mvd_concept_roots = ifcopenshell.mvd.concept_root.parse(mvd_fn)
    for concept_root in mvd_concept_roots:
        if concept_root.entity == ifc_type:
            for c in concept_root.concepts():
                if c.name == pset_or_qset:
                    for r in c.template().rules:
                        # print("  ", r.attribute)
                        if r.attribute == "IsDefinedBy":
                            return r

def get_ifc_types(file):
    return {e.is_a() for e in file.by_type("IfcBuildingElement")}

def create_tree(rulepoint, parent_node=None):
    #Function to create a tree of the Rules of the ConceptTemplates
    if parent_node:
        racine = Node(rulepoint,id=rulepoint.attribute, parent=parent_node)
    else:
        racine = Node(rulepoint, id=rulepoint.attribute)

    for node in rulepoint.nodes:

        create_tree(node, racine)
    return racine

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
mytree = create_tree(rule_tree) # Create the tree (call the function)
# print(RenderTree(mytree).by_attr('id'))

types = get_ifc_types(ifc_file)

built_request = 'https://bs-dd-api-prototype.azurewebsites.net/api/Classification/v2?namespaceUri=http%3A%2F%2Fidentifier.buildingsmart.org%2Furi%2Fbuildingsmart%2Fifc-4.3%2Fclass%2F'
ifc_bsdd = {}

log_to_construct = {}

for t in types:
    print(t)
    log_to_construct[t] = {}
    # t = "IfcDoor"
    r = requests.get(built_request+ t.lower())
    # ifc_bsdd[t] = json.loads(r.text)
    classification_result = json.loads(r.text) #r.json

    rule_tree = get_xset_rule(mvd_fn, t, pset)
    # print(rule_tree)
    
    if 'classificationProperties' in classification_result.keys():
        packed_properties = [pack_classification(p) for p in classification_result['classificationProperties'] if not p['propertySet'].startswith("Qto")]
        checking = {el:"Not present" for el in packed_properties}
        # if not len(mvd.extract_data(rule_tree, ifc_file.by_type(t)[0])) == 1 and val =='empty data structure':
        for instance in ifc_file.by_type(t):
            print("    ", instance.GlobalId)
            log_to_construct[t][instance.GlobalId] = []
            if len(mvd.extract_data(rule_tree, ifc_file.by_type(t)[0])) > 1:
                packed_output = [pack_mvd(d) for d in mvd.extract_data(rule_tree, ifc_file.by_type(t)[0])]
                to_compare = [packed_output, packed_properties]

                for element in itertools.product(*to_compare):
                    match = element[0][0] == element[1][0] and element[0][1] == element[1][1]
                    if match:
                        if isinstance(element[0][2],simple_type_python_mapping[element[1][2]]):
                            # print(element[1], 'Property validated')
                            checking[element[1]] = element[0]
                        else:
                            
                            checking[element[1]] = 'wrong type'
                    else:
                        passed = 0
                        

                for ck,cv in checking.items():
                    print("          ", ck, cv)
                    log_to_construct[t][instance.GlobalId].append((ck, cv,))
                
                else:
                    passed = 0
            
   

jsonout = os.path.join(os.path.dirname(__file__), "logs/ltest.txt")
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


