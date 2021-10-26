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
    elif bsdd_response.status_code == 200:
        return bsdd_response

def has_specifications(bsdd_response_content):
    if bsdd_response_content["classificationProperties"]:
        return 1
    else:
        return 0

def validate_instance(bsdd_response_content,ifc_file, instance):

    result = {"pset_name":"pset not found","property_name":"pset not found","value":"pset not found","datatype":"pset not found" }
    constraint = {
        "specified_pset_name":bsdd_response_content["propertySet"],
        "specified_property_name" : bsdd_response_content["name"],
        "specified_datatype" : bsdd_response_content["dataType"],
        "specified_predefined_value" : bsdd_response_content["predefinedValue"]
    }

    for pset in ifc_file.by_type("IfcPropertySet"):
        if pset.Name == constraint["specified_pset_name"]:
            result["pset_name"] = pset.Name
            for property in pset.HasProperties:
                if property.Name == constraint["specified_property_name"]:
                    result["property_name"] = property.Name
                    result["value"] = property.NominalValue
                    result["value"] = type(str(property))
                else:
                    result["property_name"] = "property not found"
                    result["value"] = "property not found"
                    result["datatype"] = "property not found"
            break

    return {"constraint":constraint,"result":result}


for  rel in ifc_file.by_type("IfcRelAssociatesClassification"):
    related_objects = rel.RelatedObjects
    relating_classification = rel.RelatingClassification

    bsdd_response = validate_ifc_classification_reference(relating_classification)
    
    for instance in related_objects:

        # This variable will contain all the information 
        # about the validation result of an entity instance
        validation_results = {"task_id":0,
                            "instance_id":0,
                            "bsDD_classification_uri":0,
                            "bsDD_property_uri":0,
                            "bsDD_property_constraint":0,
                            "bsDD_type_constraint":0,
                            "ifc_property_name":0,
                            "ifc_property_set":0,
                            "ifc_property_type":0,
                            "ifc_property_value":0
                            }

        if bsdd_response:
            if has_specifications(json.loads(bsdd_response.text)):
                specifications = json.loads(bsdd_response.text)["classificationProperties"]

                for constraint in specifications:
                    # Validation of the instance
                    results = validate_instance(constraint, ifc_file, instance)

                    # Store everything in DB
                    validation_results["task_id"]
                    validation_results["instance_id"]
                    validation_results["bsDD_classification_uri"]
                    validation_results["bsDD_classification_uri"]
                    validation_results["bsDD_type_constraint"] = json.loads(bsdd_response.text)["relatedIfcEntityNames"]
                    validation_results["bsDD_property_constraint"]
                    validation_results["ifc_property_name"]
                    validation_results["ifc_property_set"] 
                    validation_results["ifc_property_type"] 
                    validation_results["ifc_property_value"]

                    #import pdb;pdb.set_trace()
                    pass
            else:
                # Record NULL in other fields
                pass
        else:
            # Record NULL everywhere in bsdd_result
            pass


        






