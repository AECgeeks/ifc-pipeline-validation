import requests
import json
import pprint
import ifcopenshell
from ifcopenshell.mvd import mvd

import ast

from anytree import Node, RenderTree

ifc_fn = "./ifc-python-parser/files/AC20-Institute-Var-2.ifc"
#ifc_fn = "./ifc-python-parser/files/test_file.ifc"

ifc_file = ifcopenshell.open(ifc_fn)

mvd_fn = "./ifcopenshell/mvd/mvd_examples/officials/ReferenceView_V1-2.mvdxml"

def get_xset_rule(mvd_fn, ifc_type, pset_or_qset):
    mvd_concept_roots = ifcopenshell.mvd.concept_root.parse(mvd_fn)
    for concept_root in mvd_concept_roots:
        if concept_root.entity == ifc_type :
            for c in concept_root.concepts():
                print('concept name ', c.name)
  
                if c.name == pset_or_qset:
                    print("ct name", c.template().name)
                    print("ct dir", dir(c.template()))
                    print(c.concept_node)
                    print(c.rules())
                    print(c.template().rules)
                    for r in c.template().rules:
                        print("  ", r.attribute)
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


pset = 'Property Sets for Objects'
qset = 'Quantity Sets'


rule_tree = get_xset_rule(mvd_fn, 'IfcWall', qset)
mytree = create_tree(rule_tree) # Create the tree (call the function)
print(RenderTree(mytree).by_attr('id'))


types = get_ifc_types(ifc_file)

built_request = 'https://bs-dd-api-prototype.azurewebsites.net/api/Classification/v2?namespaceUri=http%3A%2F%2Fidentifier.buildingsmart.org%2Furi%2Fbuildingsmart%2Fifc-4.3%2Fclass%2F'
ifc_bsdd = {}

for t in types:
    if t == 'IfcWallStandardCase':
        t = "IfcWall"
        
        r = requests.get(built_request+ t.lower())
        # ifc_bsdd[t] = json.loads(r.text)
        classification_result = json.loads(r.text)


        rule_tree = get_xset_rule(mvd_fn, t, qset)
        print(rule_tree)
        for result in mvd.extract_data(rule_tree, ifc_file.by_type(t)[0]):
        # print(result)
            for k,v in result.items():
                print(k, v)
            print()
            
        
        if len(classification_result['classificationProperties']):
            for prop in classification_result['classificationProperties']:
                print(prop['propertySet'])
                print(prop['name'])
                print(prop['dataType'])
               
      



