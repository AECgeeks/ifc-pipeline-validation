import sys
import ifcopenshell
import requests


def get_classification_object(uri):
    return requests.get(uri)


def name_matches_code(uri, classification, schema):
    code = classification.Identification if schema == "IFC4" else classification.ItemReference
    return uri.split("/")[-1] == code


def ressource_found(status_code):
    if status_code == 200 or status_code == 202:
        return 1
    return 0


def activation_step(f):
    return len(f.by_type("IfcClassificationReference"))


def check_for_duplicates(f, ifc_type):
    cr_set = []
    for cr in f.by_type("IfcClassification"):
        info = cr.get_info()
        del info['id']
        if info in cr_set:
            print('INVALID - duplicate')
        else:
            cr_set.append(info)


def check_file(f):
    is_activated = activation_step(f)

    if is_activated:
        checked_references = set()
        schema = f.schema

        for rel in f.by_type("IfcRelAssociatesClassification"):
            classification = rel.RelatingClassification

            checked_references.add(classification.id())

            uri = classification.Location

            if uri:
                response = get_classification_object(uri)
                json_response = response.json()

                # Check: check if resource exists (in bSDD or externally)
                status_code = response.status_code
                if ressource_found(status_code):
                    print("VALID - resource found")
                else:
                    print(f"{classification} INVALID - resource not found")

                # Check: check if URI, code and name match (name can be in one of the possible languages)
                # check last bit of uri + classification.Identification
                if name_matches_code(uri, classification, schema):
                    print("VALID - name and code match")
                else:
                    print(f"{classification} INVALID - name and code do not match")

                # Check: check applicable entity type
                applicable_entity_types = json_response['relatedIfcEntityNames']
                related_objects = rel.RelatedObjects

                for entity in related_objects:
                    if entity.is_a() in applicable_entity_types:
                        print(f"VALID IFC entity type")
                    else:
                        print(
                            f"{entity} referencing {classification} INVALID IFC entity type")
            else:
                print("NO URI - skip checks")

        # Checks: check for IfcClassification/IfcClassificationReference duplicates
        check_for_duplicates(f, "IfcClassificationReference")
        check_for_duplicates(f, "IfcClassification")

        # Check: check if property exists in bSDD
        for property in f.by_type("IfcProperty"):
            uri = property.Description

            if uri:
                response = get_classification_object(uri)
                status_code = response.status_code

                if ressource_found(status_code):
                    print("VALID - resource found")
                else:
                    print(f"property {property} INVALID - resource not found")
            else:
                print("NO URI - skip checks")

        # Check: check if material exists in bSDD
        for material in f.by_type("IfcMaterial"):
            uri = material.Description

            if uri:
                response = get_classification_object(uri)
                status_code = response.status_code

                if ressource_found(status_code):
                    print("VALID - resource found")
                else:
                    print(f"material {material} INVALID - resource not found")
            else:
                print("NO URI - skip checks")

        for classification in f.by_type("IfcClassificationReference"):
            if not classification.id() in checked_references:
                uri = classification.Location
                if uri:
                    try:
                        response = get_classification_object(uri)
                        status_code = response.status_code

                        # Check: check if resource exists (in bSDD or externally)
                        if ressource_found(status_code):
                            print("VALID - resource found")
                        else:
                            print(
                                f"{classification} INVALID - resource not found")

                    except:
                        print(f"{classification} INVALID uri")

                    # Check: check if URI, code and name match (name can be in one of the possible languages)
                    # check last bit of uri + classification.Identification
                    if name_matches_code(uri, classification, schema):
                        print("VALID - name and code match")
                    else:
                        print(
                            f"{classification} INVALID - name and code do not match")
                else:
                    print("NO URI - skip checks")
    else:
        print('NOT ACTIVATED - no classifications found in the file')


if __name__ == "__main__":
    f = ifcopenshell.open(sys.argv[1])
    check_file(f)
