import ifcopenshell
import sys 
import requests
import json

ifc_fn = sys.argv[1]
ifc_file = ifcopenshell.open(ifc_fn)


def get_classification_object(uri):
    url = "https://bs-dd-api-prototype.azurewebsites.net/api/Classification/v3"
    base_url = "https://bs-dd-api-prototype.azurewebsites.net/api/"

    return requests.get(url, {'namespaceUri':uri})

def validate_ifc_classification_reference(relating_classification):
    uri = relating_classification.Location
    bsdd_response = get_classification_object(uri)
    if bsdd_response.status_code != 200:
        return 0
    elif bsdd_response == 200:
        return bsdd_response

def has_specifications(bsdd_response_content):
    if bsdd_response_content["classificationProperties"]:
        return 1
    else:
        return 0

def validate_instance(bsdd_response_content, instance):
    return 0


for  rel in ifc_file.by_type("IfcRelAssociatesClassification"):
    #print(rel)
    related_objects = rel.RelatedObjects
    relating_classification = rel.RelatingClassification

    bsdd_response = validate_ifc_classification_reference(relating_classification)

    for instance in related_objects:
        if bsdd_response:
            if has_specifications(json.loads(bsdd_response.text)):
                # Record in the field (the constraints and other)

                # Validation the instance
                results = validate_instance(bsdd_response, instance)
                # Store results in DB
                pass
            else:
                # Record NULL in other fields
                pass
        else:
            # Record NULL everywhere in bsdd_result
            pass






