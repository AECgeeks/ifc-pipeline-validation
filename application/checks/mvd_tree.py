import requests
import json
import pprint
import ifcopenshell
from ifcopenshell.mvd import mvd
import itertools
import sys
import os 

from anytree import Node, RenderTree


mvd_fn= os.path.join(os.path.dirname(__file__), "./ifcopenshell/mvd/mvd_examples/officials/ReferenceView_V1-2.mvdxml")

def create_tree(rulepoint, parent_node=None):
    #Function to create a tree of the Rules of the ConceptTemplates
    if parent_node:
        racine = Node(rulepoint,id=rulepoint.attribute, parent=parent_node)
    else:
        racine = Node(rulepoint, id=rulepoint.attribute)

    for node in rulepoint.nodes:
        create_tree(node, racine)
    return racine

def get_xset_rule(mvd_fn, ifc_type, pset_or_qset):
    rules = []
    mvd_concept_roots = ifcopenshell.mvd.concept_root.parse(mvd_fn)
    for concept_root in mvd_concept_roots:
        if concept_root.entity == ifc_type:
            for c in concept_root.concepts():
                if c.name == pset_or_qset:
                    for r in c.template().rules:
                        print("  ", r.attribute)
                        rules.append(r)
                        if r.attribute == "IsDefinedBy":
                            return r
   
rule_tree = get_xset_rule(mvd_fn, 'IfcWall', 'Property Sets for Objects')
for pre, _, node in RenderTree(create_tree(rule_tree)):
    print("%s%s" % (pre, node.name))


tree = create_tree(rule_tree) # Create the tree (call the function)
print(RenderTree(tree).by_attr('id'))
print(RenderTree(tree))


