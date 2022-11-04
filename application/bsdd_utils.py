import database
import json

def get_hierarchical_bsdd(id):
    with database.Session() as session:
        model = session.query(database.model).filter(
            database.model.code == id).all()[0]

        hierarchical_bsdd_results = {}
        if model.status_bsdd != 'n':
            for bsdd_result in model.tasks[2].results:
                
                bsdd_result = bsdd_result.serialize()
             
                if bsdd_result["instance_id"]:
                    bsdd_result['global_id'] = session.query(database.ifc_instance).filter(database.ifc_instance.id == bsdd_result["instance_id"]).all()[0].global_id
                    bsdd_result['ifc_type'] = session.query(database.ifc_instance).filter(database.ifc_instance.id == bsdd_result["instance_id"]).all()[0].ifc_type

                validation_subsections = ["val_ifc_type", "val_property_set", "val_property_name", "val_property_type", "val_property_value"]
                validation_results = [bsdd_result[subsection] for subsection in validation_subsections]

                file_values = [ 
                            bsdd_result["bsdd_type_constraint"],
                            bsdd_result["ifc_property_set"],
                            bsdd_result["ifc_property_name"],
                            bsdd_result["ifc_property_type"],
                            bsdd_result["ifc_property_value"]
                ]
                
                if None not in validation_results:
                    if sum(validation_results) != len(validation_results):
                        validation_constraints_subsections = ["propertySet","name","dataType", "predefinedValue", "possibleValues"]

                        validation_constraints= [bsdd_result['bsdd_type_constraint']]

                        for subsection in validation_constraints_subsections:
                            constraint = json.loads(bsdd_result["bsdd_property_constraint"])
                            if subsection in constraint.keys():
                                validation_constraints.append(constraint[subsection])
                
                if bsdd_result["bsdd_property_constraint"]:
                    bsdd_result["bsdd_property_constraint"] = json.loads(
                        bsdd_result["bsdd_property_constraint"])
                else:
                    bsdd_result["bsdd_property_constraint"] = 0

                if bsdd_result["domain_file"] not in hierarchical_bsdd_results.keys():
                    hierarchical_bsdd_results[bsdd_result["domain_file"]]= {}

                if bsdd_result["classification_file"] not in hierarchical_bsdd_results[bsdd_result["domain_file"]].keys():
                    hierarchical_bsdd_results[bsdd_result["domain_file"]][bsdd_result["classification_file"]] = []

                hierarchical_bsdd_results[bsdd_result["domain_file"]][bsdd_result["classification_file"]].append(bsdd_result)
    
    return hierarchical_bsdd_results     


