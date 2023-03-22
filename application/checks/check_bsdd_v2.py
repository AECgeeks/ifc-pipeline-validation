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

def validate_instance(constraints, instance):
    to_validate = ["pset_name", "property_name", "datatype", "value"]
    validation_results = dict((el,0) for el in to_validate)

    if "propertySet" in constraints.keys():
        result = dict((el,"pset not found") for el in to_validate)
        for definition in instance.IsDefinedBy:
            if definition.is_a() == "IfcRelDefinesByProperties": 
                pset = definition.RelatingPropertyDefinition
                if pset.Name == constraints["propertySet"]:
                    result = dict((el,"property not found") for el in to_validate)
                    result["pset_name"] = pset.Name
                    validation_results["pset_name"] = 1
                    for property in pset.HasProperties:
                        if property.Name == constraints["name"]:
                            result["property_name"] = property.Name
                            validation_results["property_name"] = 1

                            # Translate datatypes and values
                            if constraints["dataType"].lower() == "boolean":
                                constraints["dataType"] = "bool"
                            
                            if constraints["dataType"].lower() == "string":
                                constraints["dataType"] = "str"

                            if "predefinedValue" in constraints.keys():
                                if constraints["predefinedValue"].lower() == "true":
                                    constraints["predefinedValue"] = 1
                                elif constraints["predefinedValue"].lower()  == "false":
                                    constraints["predefinedValue"]  = 0
                            
                            if isinstance(property.NominalValue, ifcopenshell.entity_instance):
                                result["value"] = property.NominalValue[0]   
                            else:
                                result["value"] = property.NominalValue
                            
                            result["datatype"] = type(property.NominalValue[0]).__name__
                            
                            validation_results["datatype"] = (result["datatype"] == constraints["dataType"])

                            validation_results["value"] = 1
                            if "predefinedValue" in constraints.keys():
                                validation_results["value"] = (result["value"] == constraints["predefinedValue"])
                            elif "possibleValues" in constraints.keys():
                                possible_values = constraints["possibleValues"]
                            
                                for possible_value in possible_values:
                                    to_check = possible_value["value"]
                                    if possible_value["value"].lower() == "true":
                                        to_check = 1
                                    if possible_value["value"].lower() == "false":
                                        to_check = 0
                                    if result["value"] != to_check:
                                        validation_results["value"] = 0
                                        break
    else:
        result = dict((el,"no pset in constraints") for el in to_validate) 
        validation_results["pset_name"] = 1

    return {"result":result, "validation_results":validation_results}

def get_domain_file(relating_classification):
    try:
        domain_file = relating_classification.ReferencedSource.Name
    except:
        domain_file = ""
    return domain_file

def get_related_entity_names(ifc_instance, bsdd_content):
    if 'relatedIfcEntityNames':
        val_ifc_type = any(ifc_instance.is_a(t) for t in bsdd_content["relatedIfcEntityNames"])
        bsdd_type_constraint = ";".join(bsdd_content["relatedIfcEntityNames"])
    else:
        val_ifc_type = 1
        bsdd_type_constraint = ""
    return {"val_ifc_type": val_ifc_type,"bsdd_type_constraint": bsdd_type_constraint}

def check_bsdd(ifc_fn, task_id, db):
   
    file_code = ifc_fn.split(".ifc")[0]
    ifc_file = ifcopenshell.open(ifc_fn)
   
    with database.Session() as session:
        if db:
            model = session.query(database.model).filter(database.model.code == file_code)[0]
            file_id = model.id

 
        n = len(ifc_file.by_type("IfcRelAssociatesClassification"))
        if n:
            percentages = [i * 100. / n for i in range(n+1)]
            num_dots = [int(b) - int(a) for a, b in zip(percentages, percentages[1:])]

            for idx, rel in enumerate(ifc_file.by_type("IfcRelAssociatesClassification")):
                sys.stdout.write(num_dots[idx] * ".")
                sys.stdout.flush()

                related_objects = rel.RelatedObjects
                relating_classification = rel.RelatingClassification

                bsdd_response = validate_ifc_classification_reference(relating_classification)
                
                bsdd_results = []
                for ifc_instance in related_objects:
                    if db:
                        instance = database.ifc_instance(ifc_instance.GlobalId, ifc_instance.is_a(), file_id)
                        session.add(instance)
                        session.flush()
                        instance_id = instance.id
                        session.commit()
                    else:
                        instance_id = ifc_instance.GlobalId


                    if bsdd_response:
                        bsdd_content = json.loads(bsdd_response.text)
                        domain_name = get_domain(bsdd_content["namespaceUri"]).json()[0]["name"]

                        if has_specifications(bsdd_content):
                            specifications = bsdd_content["classificationProperties"]
                            for constraint in specifications: 
                                bsdd_result = database.bsdd_result(task_id) if db else {}

                                val_output = validate_instance(constraint, ifc_instance)
                                results = val_output["result"]
                                val_results = val_output["validation_results"]

                                attrs = {
                                    "classification_file": relating_classification.Name,
                                    "domain_file": get_domain_file(relating_classification),
                                    "instance_id": instance_id, # Should create instance entry
                                    "bsdd_classification_uri":  bsdd_content["namespaceUri"],
                                    "classification_name": bsdd_content["name"],
                                    "classification_code": bsdd_content["code"],
                                    "classification_domain": domain_name,
                                    "val_ifc_type": get_related_entity_names(ifc_instance, bsdd_content)["val_ifc_type"],
                                    "bsdd_type_constraint": get_related_entity_names(ifc_instance, bsdd_content)["bsdd_type_constraint"],
                                    "bsdd_property_constraint": json.dumps(constraint),
                                    "bsdd_property_uri": constraint["propertyNamespaceUri"],
                                    "ifc_property_set": results["pset_name"],
                                    "ifc_property_name": results["property_name"],
                                    "ifc_property_type": results["datatype"],
                                    "ifc_property_value": results["value"],
                                    "val_property_set": val_results["pset_name"],
                                    "val_property_name": val_results["property_name"],
                                    "val_property_type": val_results["datatype"],
                                    "val_property_value": val_results["value"]
                                }

                                if db:    
                                    for attr, value in attrs.items():
                                        setattr(bsdd_result, attr, value)
                                    if sum([bsdd_result.val_ifc_type,val_results["pset_name"],val_results["property_name"], val_results["datatype"]], val_results["value"]) != 5:
                                        model.status_bsdd = 'i'
                                        #Validation output 
                                    session.add(bsdd_result)
                                    session.commit()
                                else:
                                    bsdd_results.append(attrs)

                        else:
                            # No classificationProperties
                            bsdd_result = database.bsdd_result(task_id) if db else {}
                            attrs = {
                                "domain_file": get_domain_file(relating_classification),
                                "classification_file": relating_classification.Name,
                                "instance_id": instance_id,
                                "bsdd_property_constraint": "no constraint"
                            }

                            if db:
                                for attr, value in attrs.items():
                                    setattr(bsdd_result, attr, value)
                                model.status_bsdd = 'v'
                                session.add(bsdd_result)
                                session.commit()
                            else:
                                bsdd_results.append(attrs)
                    else:
                        # No uri provided or invalid uri
                        bsdd_result = database.bsdd_result(task_id) if db else {}
                        attrs = {
                            "domain_file": get_domain_file(relating_classification),
                            "classification_file": relating_classification.Name,
                            "instance_id": instance_id,
                            "bsdd_classification_uri": "classification not found"
                        }
                        if db:
                            for attr, value in attrs.items():
                                setattr(bsdd_result, attr, value)
                            model.status_bsdd = 'v'
                            session.add(bsdd_result)
                            session.commit()
                        else:
                            bsdd_results.append(attrs)


        else:
            bsdd_result = database.bsdd_result(task_id) if db else {}
            attrs = {
                "domain_file": "no IfcClassification",
                "classification_file":"no IfcClassificationReference",
                "classification_name": "file not classified",
                "classification_code": "file not classified",
                "classification_domain": "file not classified"
            }
            if db:
                for attr, value in attrs.items():
                    setattr(bsdd_result, attr, value)
                model.status_bsdd = 'v'
                session.add(bsdd_result)
                session.commit()
            else:
                bsdd_results.append(attrs)
                
    json.dump(bsdd_results, open('check_bsdd.json', 'w')) if not db else None


if __name__=="__main__":
        parser = argparse.ArgumentParser(description="Generate classified IFC file")
        parser.add_argument("--input","-i", default="Duplex_A_20110505.ifc", type=str)
        parser.add_argument("--task","-t", default=0, type=int, required=False)
        parser.add_argument("--database", "-db", default=1, type=int)
        

        args = parser.parse_args()
        check_bsdd(args.input, args.task, args.database)





