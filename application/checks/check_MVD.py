import ifcopenshell
from ifcopenshell.mvd import mvd

ifc_fn = "./ifc-python-parser/files/AC20-FZK-Haus.ifc"
ifc_file = ifcopenshell.open(ifc_fn)

mvd_fn = "./ifcopenshell/mvd/mvd_examples/officials/ReferenceView_V1-2.mvdxml"
mvd_concept_roots = ifcopenshell.mvd.concept_root.parse(mvd_fn)

for concept_root in mvd_concept_roots:
    if concept_root.entity == "IfcWall":
        for c in concept_root.concepts():
            # print(c.name)
            # print(c.concept_node)
            # print(c.rules())
            # print(c.template().rules)
            if len(c.template().rules) > 1:
                attribute_rules = []
                for rule in c.template().rules:
                    attribute_rules.append(rule)
                rules_root = ifcopenshell.mvd.rule("EntityRule",concept_root.entity, attribute_rules)
            else:
                rules_root = c.template().rules[0]

            d = mvd.extract_data( rules_root, ifc_file.by_type("IfcWall")[0])

           