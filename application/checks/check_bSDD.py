import requests
import json
import pprint
import ifcopenshell


def get_ifc_types(file):
    return {e.is_a() for e in file.by_type("IfcBuildingElement")}

ifc_fn = "./ifc-python-parser/files/AC20-FZK-Haus.ifc"
ifc_file = ifcopenshell.open(ifc_fn)

types = get_ifc_types(ifc_file)

built_request = 'https://bs-dd-api-prototype.azurewebsites.net/api/Classification/v2?namespaceUri=http%3A%2F%2Fidentifier.buildingsmart.org%2Furi%2Fbuildingsmart%2Fifc-4.3%2Fclass%2F'
ifc_bsdd = {}

for t in types:
    r = requests.get(built_request+ t.lower())
    ifc_bsdd[t] = json.loads(r.text)


class_test = ifc_bsdd['IfcWindow']
print(json.dumps(class_test, indent=4, sort_keys=True))
classification_properties = class_test["classificationProperties"]
print(len(classification_properties))

