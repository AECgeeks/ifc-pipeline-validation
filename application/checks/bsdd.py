import requests
import json
import pprint
import ifcopenshell
from ifcopenshell.mvd import mvd
import itertools
import sys
import os 



def pack_classification(classification_props):
    return classification_props['propertySet'], classification_props['name'], classification_props['dataType'], classification_props['predefinedValue']

def pack_mvd(mvd_output):
    return list(mvd_output.values())[0], list(mvd_output.values())[1], list(mvd_output.values())[3].wrappedValue

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

pset = 'Property Sets for Objects'
qset = 'Quantity Sets'

rule_tree = get_xset_rule(mvd_fn, 'IfcWall', pset)

ifc_fn = sys.argv[1]
ifc_file = ifcopenshell.open(ifc_fn)


classref = ifc_file.by_type("IfcClassificationReference")
relclassref = ifc_file.by_type("IfcRelAssociatesClassification")

log_to_construct = {}

for rel in relclassref:
    # print(len(rel.RelatedObjects))
    domain = rel.RelatingClassification.ReferencedSource


    # import pdb; pdb.set_trace()
    #print(relclassref[0].RelatingClassification)
    domain_name = domain.Name
    classification_code = rel.RelatingClassification.ItemReference
    log_to_construct[rel.RelatingClassification.Name +"-"+classification_code] = {}
    print(rel.RelatingClassification.Name, classification_code)
  
    
    if "NL/SfB" in domain_name:
        domain_name = "nlsfb"


    # print(domain_name, classification_code)

    url = "http://identifier.buildingsmart.org/uri/"+ domain_name + "/" + "nlsfb2005-2.2/class/"+classification_code


    r = requests.get(url)
    bsdd_response = json.loads(r.text) 
    print(bsdd_response)
    if 'relatedIfcEntityNames' in bsdd_response.keys():
        print(bsdd_response['relatedIfcEntityNames'])
        
    else:
        print('no related entities')


    if 'classificationProperties' in bsdd_response.keys():
        classification_properties = bsdd_response['classificationProperties']
        # print(len(classification_properties))

        packed_properties = [pack_classification(p) for p in bsdd_response['classificationProperties']]
        # print(packed_properties)

        for e in rel.RelatedObjects:
            print("     ", e.GlobalId)
            log_to_construct[rel.RelatingClassification.Name +"-"+classification_code][e.GlobalId] = []
           
            packed_output = [pack_mvd(d) for d in mvd.extract_data(rule_tree, e)]
            to_compare = [packed_output, packed_properties]
            for mvd_data, bsdd_data in itertools.product(*to_compare):
                
                match = mvd_data[0] == bsdd_data[0] and mvd_data[1] == bsdd_data[1]
                if match:
                    compval = bsdd_data[3]
                    # print(bsdd_data)
                    # print(mvd_data)

                    if bsdd_data[3] == 'TRUE':
                        compval = True
                    elif bsdd_data[3] == 'FALSE':
                        compval = False
                    
                    if mvd_data[2] == compval:
                        print("        ",mvd_data, bsdd_data, 'PASSED')
                        log_to_construct[rel.RelatingClassification.Name +"-"+classification_code][e.GlobalId]

                    else:
                        print("        ",mvd_data, bsdd_data,  'FAILED')
                        log_to_construct[rel.RelatingClassification.Name +"-"+classification_code][e.GlobalId].append((mvd_data, bsdd_data,  'FAILED',)) 



jsonout = os.path.join(os.getcwd(), "dresult_bsdd.json")

with open(jsonout, 'w', encoding='utf-8') as f:
    json.dump(log_to_construct, f, ensure_ascii=False, indent=4)




             
               








