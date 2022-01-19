import ifcopenshell
import sys 
import requests
import json
import numpy as np
import argparse



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

def validate_instance(constraint,ifc_file, instance):

    result = {"pset_name":"pset not found","property_name":"pset not found","value":"pset not found","datatype":"pset not found" }
    constraint = {
        "specified_pset_name":constraint["propertySet"],
        "specified_property_name" : constraint["name"],
        "specified_datatype" : constraint["dataType"],
        "specified_predefined_value" : constraint["predefinedValue"],
    }

    # import pdb;pdb.set_trace()

    # Integrate these:
    #   "maxExclusive": 0
    #   "maxInclusive": 0
    #   "minExclusive": 0
    #   "minInclusive": 0
    #   "pattern": ""

    for definition in instance.IsDefinedBy:
        if definition.is_a() == "IfcRelDefinesByProperties":
            
            pset = definition.RelatingPropertyDefinition
            if pset.Name == constraint["specified_pset_name"]:
                result["property_name"] = "property not found"
                result["value"] = "property not found"
                result["datatype"] = "property not found"

                result = {"pset_name":pset.Name,"property_name":"pset not found","value":"pset not found","datatype":"pset not found" }
                for property in pset.HasProperties:
                    if property.Name == constraint["specified_property_name"]:
                        result["property_name"] = property.Name

                        if isinstance(property.NominalValue, ifcopenshell.entity_instance):
                            result["value"] = property.NominalValue[0]
                            result["datatype"] = type(property.NominalValue[0])
                        else:
                            result["value"] = property.NominalValue
                            result["datatype"] = type(property.NominalValue[0])

                        

    return {"constraint":constraint,"result":result}



def check_bsdd(ifc_fn, USE_DB, task_id):
    # import pdb;pdb.set_trace()

    if USE_DB:
        # import pdb;pdb.set_trace()
        from helper import database


    file_code = ifc_fn.split(".ifc")[0]

    # file_code = "mDgWwLEwesUQnwwrnpqmyNCyVBbODQLy"


    ifc_file = ifcopenshell.open(ifc_fn)

    if USE_DB:
        session = database.Session()

        model = session.query(database.model).filter(database.model.code == file_code)[0]
        file_id = model.id
        session.close()

        
    n = len(ifc_file.by_type("IfcRelAssociatesClassification"))

    if n:
        rnd_array = np.random.multinomial(100, np.ones(n)/n, size=1)[0]
        for idx, rel in enumerate(ifc_file.by_type("IfcRelAssociatesClassification")):

            sys.stdout.write(rnd_array[idx] * ".")
            sys.stdout.flush()


            related_objects = rel.RelatedObjects
            relating_classification = rel.RelatingClassification

            bsdd_response = validate_ifc_classification_reference(relating_classification)
            
            for ifc_instance in related_objects:
                # print(ifc_instance)

                if USE_DB:

                    session = database.Session()
                    instance = database.ifc_instance(ifc_instance.GlobalId, ifc_instance.is_a(), file_id)
                    session.add(instance)
                    session.flush()
                    instance_id = instance.id
                    session.commit()
                    session.close()
                
                else:
                    instance_id = ifc_instance.GlobalId

                # This variable will contain all the information 
                # about the validation result of an entity instance
                bsdd_result = {"task_id":0,
                                    "instance_id":0,
                                    "bsdd_classification_uri":0,
                                    "bsdd_property_uri":0,
                                    "bsdd_property_constraint":0,
                                    "bsdd_type_constraint":0,
                                    "ifc_property_set":0,
                                    "ifc_property_name":0,
                                    "ifc_property_type":0,
                                    "ifc_property_value":0
                                    }

                if bsdd_response:
                    # import pdb;pdb.set_trace()
                    if has_specifications(json.loads(bsdd_response.text)):
                        specifications = json.loads(bsdd_response.text)["classificationProperties"]
                        # import pdb;pdb.set_trace()
                        #import pdb;pdb.set_trace()
                        for constraint in specifications:


                            # Validation of the instance
                            
                            constraint_content = json.loads(bsdd_response.text)

                            # Store everything in DB
                            bsdd_result["task_id"] = task_id
                            
                            # Should create instance entry
                            bsdd_result["instance_id"] = instance_id

                            bsdd_result["bsdd_classification_uri"] = constraint_content["namespaceUri"]
                            bsdd_result["bsdd_type_constraint"] = ";".join(constraint_content["relatedIfcEntityNames"])
                            bsdd_result["bsdd_property_constraint"] = json.dumps(constraint)
                            bsdd_result["bsdd_property_uri"] = constraint["propertyNamespaceUri"]

                            results = validate_instance(constraint, ifc_file, ifc_instance)


                            bsdd_result["ifc_property_set"] = results["result"]["pset_name"]
                            bsdd_result["ifc_property_name"] = results["result"]["property_name"]
                            
                            if not isinstance(results["result"]["datatype"], str):
                                bsdd_result["ifc_property_type"] = results["result"]["datatype"].__name__
                            bsdd_result["ifc_property_value"] = results["result"]["value"]
                            

                            if USE_DB:
                                session = database.Session()
                                db_bsdd_result = database.bsdd_result(bsdd_result["task_id"])

                                for key, value in bsdd_result.items():
                                    setattr(db_bsdd_result, key, value) 
                                
                                session.add(db_bsdd_result)
                                
                                session.commit()
                                session.close()

                            pass
                    else:
                        # Record NULL in other fields
                        bsdd_result["bsdd_property_constraint"] = "no constraint"
                        if USE_DB:  
                            session = database.Session()
                            db_bsdd_result = database.bsdd_result(bsdd_result["task_id"])

                            for key, value in bsdd_result.items():
                                setattr(db_bsdd_result, key, value) 

                            session.add(db_bsdd_result)
                            session.commit()
                            session.close()

                        pass
                else:
                    # Record NULL everywhere in bsdd_result
                    bsdd_result["bsdd_classification_uri"] = "classification not found"
                    
                    if USE_DB:
                        session = database.Session()
                        db_bsdd_result = database.bsdd_result(bsdd_result["task_id"])

                        for key, value in bsdd_result.items():
                            setattr(db_bsdd_result, key, value) 


                        session.add(db_bsdd_result)
                        session.commit()
                        session.close()
                        pass

    if USE_DB:
        #todo: implement scores that actually validate or not the model
        session = database.Session()
        model = session.query(database.model).filter(database.model.code == file_code)[0]
        model.status_bsdd = 'v'
        session.commit()
        session.close()
        

if __name__=="__main__":
        parser = argparse.ArgumentParser(description="Generate classified IFC file")
        parser.add_argument("--input","-i", default="Duplex_A_20110505.ifc", type=str)
        parser.add_argument("--db","-d", default=0, type=bool)
        parser.add_argument("--task","-t", default=0, type=int)

        args = parser.parse_args()
        check_bsdd(args.input,args.db, args.task)






