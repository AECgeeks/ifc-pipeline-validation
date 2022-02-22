import ifcopenshell
import sys 
import requests
import json
import argparse
from helper import database



def get_classification_object(uri):
    url = "https://bs-dd-api-prototype.azurewebsites.net/api/Classification/v3"
    return requests.get(url, {'namespaceUri':uri})

def get_domain(classification_uri):
    url = "https://bs-dd-api-prototype.azurewebsites.net/api/Domain/v2"
    uri = classification_uri.split("/class")[0]
    return requests.get(url, {'namespaceUri':uri})


def validate_ifc_classification_reference(relating_classification):
    uri = relating_classification.Location
    bsdd_response = get_classification_object(uri)
    if bsdd_response.status_code != 200:
        return 0
    elif bsdd_response.status_code == 200:
        return bsdd_response

def has_specifications(bsdd_response_content):
    if "classificationProperties" in bsdd_response_content.keys():
        return 1
    else:
        return 0

def validate_instance(constraints,ifc_file, instance):

    constraint = {
        "specified_pset_name":constraints["propertySet"],
        "specified_property_name" : constraints["name"],
        "specified_datatype" : constraints["dataType"],
        "specified_predefined_value" : constraints["predefinedValue"],
    }

    # Translate datatypes and values
    if constraint["specified_datatype"] == "Boolean":
        constraint["specified_datatype"] = "bool"
        if constraint["specified_predefined_value"] == "TRUE":
            constraint["specified_predefined_value"] = 1
        elif constraint["specified_predefined_value"] == "FALSE":
            constraint["specified_predefined_value"] = 0

    to_validate = ["pset_name", "property_name", "datatype", "value"]
    validation_results = dict((el,0) for el in to_validate)

    if "propertySet" in constraints.keys():
        result = dict((el,"pset not found") for el in to_validate)
        for definition in instance.IsDefinedBy:
            if definition.is_a() == "IfcRelDefinesByProperties": 
                pset = definition.RelatingPropertyDefinition
                if pset.Name == constraint["specified_pset_name"]:
                    result = dict((el,"property not found") for el in to_validate)
                    result["pset_name"] = pset.Name
                    validation_results["pset_name"] = 1
                    for property in pset.HasProperties:
                        if property.Name == constraint["specified_property_name"]:
                            result["property_name"] = property.Name
                            validation_results["property_name"] = 1
                            if isinstance(property.NominalValue, ifcopenshell.entity_instance):
                                result["value"] = property.NominalValue[0]   
                            else:
                                result["value"] = property.NominalValue
                            
                            result["datatype"] = type(property.NominalValue[0]).__name__
                            
                            validation_results["datatype"] = (result["datatype"] == constraint["specified_datatype"])
                            validation_results["value"] = (result["value"] == constraint["specified_predefined_value"])

    else:
        result["pset_name"] = "no pset in constraints"
        result["property_name"] = "no pset in constraints"
        result["datatype"] = "no pset in constraints"
        result["value"] = "no pset in constraints"

    return {"constraint":constraint,"result":result, "validation_results":validation_results}


def check_bsdd(ifc_fn, task_id):
   
    file_code = ifc_fn.split(".ifc")[0]
    ifc_file = ifcopenshell.open(ifc_fn)
   
    with database.Session() as session:
        model = session.query(database.model).filter(database.model.code == file_code)[0]
        file_id = model.id
 
        n = len(ifc_file.by_type("IfcRelAssociatesClassification"))
        if n:
            percentages = [i * 100. / n for i in range(n+1)]
            num_dots = [int(b) - int(a) for a, b in zip(percentages, percentages[1:])]

            for idx, rel in enumerate(ifc_file.by_type("IfcRelAssociatesClassification")):
                # if num_dots[idx]:
                    #print(num_dots[idx] * ".", file=sys.stdout)
                sys.stdout.write(num_dots[idx] * ".")
                sys.stdout.flush()

                related_objects = rel.RelatedObjects
                relating_classification = rel.RelatingClassification

                bsdd_response = validate_ifc_classification_reference(relating_classification)
                
                
                for ifc_instance in related_objects:
                    instance = database.ifc_instance(ifc_instance.GlobalId, ifc_instance.is_a(), file_id)
                    session.add(instance)
                    session.flush()
                    instance_id = instance.id
                    session.commit()               

                    if bsdd_response:
                        bsdd_content = json.loads(bsdd_response.text)
                        domain_name = get_domain(bsdd_content["namespaceUri"]).json()[0]["name"]

                        if has_specifications(bsdd_content):
                            specifications = bsdd_content["classificationProperties"]
                            for constraint in specifications: 
                                bsdd_result = database.bsdd_result(task_id)
                                bsdd_result.domain_file = relating_classification.ReferencedSource.Name
                                bsdd_result.classification_file = relating_classification.Name

                                # Should create instance entry
                                bsdd_result.instance_id = instance_id

                                bsdd_result.bsdd_classification_uri = bsdd_content["namespaceUri"]
                                bsdd_result.classification_name = bsdd_content["name"]
                                bsdd_result.classification_code = bsdd_content["code"]
                                bsdd_result.classification_domain = domain_name

                                bsdd_result.val_ifc_type = sum(ifc_instance.is_a(t) for t in bsdd_content["relatedIfcEntityNames"]) >= 1

                                bsdd_result.bsdd_type_constraint = ";".join(bsdd_content["relatedIfcEntityNames"])
                                bsdd_result.bsdd_property_constraint = json.dumps(constraint)
                                bsdd_result.bsdd_property_uri = constraint["propertyNamespaceUri"]

                                val_output = validate_instance(constraint, ifc_file, ifc_instance)

                                results = val_output["result"]
                                bsdd_result.ifc_property_set = results["pset_name"]
                                bsdd_result.ifc_property_name = results["property_name"]
                                
                                bsdd_result.ifc_property_type = results["datatype"]
                                bsdd_result.ifc_property_value = results["value"]
                          
                                val_results = val_output["validation_results"]
                                bsdd_result.val_property_set = val_results["pset_name"]
                                bsdd_result.val_property_name = val_results["property_name"]
                                bsdd_result.val_property_type = val_results["datatype"]
                                bsdd_result.val_property_value = val_results["value"]

                                #Validation output 
                                session.add(bsdd_result)
                                session.commit()
                        else:
                            # No classificationProperties
                            bsdd_result = database.bsdd_result(task_id)
                            bsdd_result.domain_file = relating_classification.ReferencedSource.Name
                            bsdd_result.classification_file = relating_classification.Name
                            bsdd_result.instance_id = instance_id
                            bsdd_result.bsdd_property_constraint = "no constraint"
                            session.add(bsdd_result)
                            session.commit()
                    else:
                        # No uri provided or invalid uri
                        bsdd_result = database.bsdd_result(task_id)

                        bsdd_result.domain_file = relating_classification.ReferencedSource.Name
                        bsdd_result.classification_file = relating_classification.Name
                        bsdd_result.instance_id = instance_id
                        bsdd_result.bsdd_classification_uri = "classification not found"

                        session.add(bsdd_result)
                        session.commit()
                    
            
            model = session.query(database.model).filter(database.model.code == file_code)[0]
            model.status_bsdd = 'v'
            session.commit()


        else:
            bsdd_result = database.bsdd_result(task_id)
            bsdd_result.domain_file = "no IfcClassification"
            bsdd_result.classification_file = "no IfcClassificationReference"
            model = session.query(database.model).filter(database.model.code == file_code)[0]
            model.status_bsdd = 'v'
            session.add(bsdd_result)
            session.commit()



if __name__=="__main__":
        parser = argparse.ArgumentParser(description="Generate classified IFC file")
        parser.add_argument("--input","-i", default="Duplex_A_20110505.ifc", type=str)
        parser.add_argument("--task","-t", default=0, type=int)

        args = parser.parse_args()
        check_bsdd(args.input, args.task)





