import sys, os
import json
import ifcopenshell


ifc_fn = sys.argv[1]
ifc_file = ifcopenshell.open(ifc_fn)

try:
    #ifc_file.header.file_description.description[0].split(" ", 1)[1]
    detected_mvd = ifc_file.header.file_description.description[0].split(" ", 1)[1]
    detected_mvd = detected_mvd[1:]
    detected_mvd = detected_mvd[:-1]
    detected_mvd = detected_mvd.split(",")
except:
    detected_mvd: "no MVD detected"

# try:
#     authoring_app = ifc_file.header.file_name.toString().split(",")[-3]
# except:
#     authoring_app = 'no authoring app detected'

#import pdb; pdb.set_trace()

file_info = {
    'size':str(round(os.path.getsize(sys.argv[1])*10**-6)) + "MB",
    'schema':ifc_file.schema,
    # 'app': authoring_app
    'mvd': detected_mvd

    }

print(file_info)

results_path = os.path.join(os.getcwd(), "info.json")

with open(results_path, 'w', encoding='utf-8') as f:
    json.dump(file_info, f, ensure_ascii=False, indent=4)

