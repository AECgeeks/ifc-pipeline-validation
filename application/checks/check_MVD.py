import ifcopenshell
from ifcopenshell.mvd import mvd
import logging
import json

ifc_fn = "./ifc-python-parser/files/AC20-FZK-Haus.ifc"
#ifc_fn = "./ifc-python-parser/files/Duplex_A_20110505.ifc"
ifc_file = ifcopenshell.open(ifc_fn)

mvd_fn = "./ifcopenshell/mvd/mvd_examples/officials/ReferenceView_V1-2.mvdxml"
mvd_concept_roots = ifcopenshell.mvd.concept_root.parse(mvd_fn)

log_to_construct = {}

for concept_root in mvd_concept_roots:
    # print(" ",concept_root.entity)
    entity_name = concept_root.entity
    log_to_construct[entity_name] = {}
    
    entity_type = concept_root.entity
    if len(ifc_file.by_type(entity_type)):
        entity_instances = ifc_file.by_type(entity_type)

        for concept in concept_root.concepts():
            # log_to_construct[concept_root.entity][concept.name][concept.template().name] = []
            # print("   ", concept.template().name)
            ct_name = concept.template().name
            log_to_construct[entity_name][ct_name] = {}
            for rule in concept.template().rules:
                # log_to_construct[concept_root.entity][concept][concept.template().name].append(rule.attribute)
                # print("     ", rule)
                #rule_label = (rule.tag, rule.attribute,)
                rule_att = rule.attribute
                log_to_construct[entity_name][ct_name][rule_att] = {}
                l = log_to_construct[entity_name][ct_name][rule_att]
                for e in entity_instances:
                    # print("         ", e.GlobalId)
                    guid = e.GlobalId
                    #log_to_construct[entity_name][ct_name][rule_att][guid] = []
                    # log_to_construct[concept_root.entity][concept.template().name][rule.attribute][e.GlobalId] = []
                    extraction = mvd.extract_data(rule,e)
                    # print(extraction)
                    
                
                    log_to_construct[entity_name][ct_name][rule_att][guid] = extraction

                    # for ex in extraction:
                    #     to_append = 'a'
                    #     log_to_construct[concept_root.entity][concept.template().name][rule.attribute][e.GlobalId].append(to_append)
                    #     # print("              ",ex)
                    #     # print()

# print(log_to_construct)

print(log_to_construct)

# with open('./logs/mvdlog.json', 'w', encoding='utf-8') as f:
#     json.dump(log_to_construct, f, ensure_ascii=False, indent=4)


            