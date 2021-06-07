import operator
import ifcopenshell.util.element

from xml.dom.minidom import parse

class exception(Exception):
    pass


def error(msg):
    raise exception(msg)


class facet_evaluation:
    """
    The evaluation of a facet with data from IFC. Converts to bool and has a human readable string format.
    """

    def __init__(self, success, str):
        self.success = success
        self.str = str

    def __bool__(self):
        return self.success

    def __str__(self):
        return self.str


class meta_facet(type):
    """
    A metaclass for automatically registering facets in a map to be instantiated based on XML tagnames.
    """

    facets = {}

    def __new__(cls, clsname, bases, attrs):
        newclass = super(meta_facet, cls).__new__(cls, clsname, bases, attrs)
        meta_facet.facets[clsname] = newclass
        return newclass


class facet(metaclass=meta_facet):
    """
    The base class for IDS facets. IDS facets are functors constructed from
    XML nodes that return True or False. A getattr method is provided for
    conveniently extracting XML child node text content.
    """

    def __init__(self, node):
        self.node = node

    def __getattr__(self, k):
        if len(self.node.getElementsByTagName(k)):
            v = self.node.getElementsByTagName(k)[0]
            elems = [n for n in v.childNodes if n.nodeType == n.ELEMENT_NODE]
            if elems:
                return restriction(elems[0])
            else:
                return v.firstChild.nodeValue.strip()

    def __iter__(self):
        for k in self.parameters:
            yield k, getattr(self, k)

    def __str__(self):
        return self.message % dict(list(self))


class entity(facet):
    """
    The IDS entity facet currently *with* inheritance
    """

    parameters = ["name", "predefinedtype"]
    message = "an entity name '%(name)s'"

    def __call__(self, inst, logger):
        logger.debug("Testing %s == %s", inst.is_a(), self.name)
        # @nb with inheritance
        # return inst.is_a() == self.name
        return facet_evaluation(inst.is_a(self.name), self.message % {"name": inst.is_a()})


class classification(facet):
    """
    The IDS classification facet by traversing the HasAssociations inverse attribute
    """

    parameters = ["system", "value"]
    message = "a classification reference to '%(value)s' from '%(system)s'"

    def __call__(self, inst, logger):
        refs = []
        for association in inst.HasAssociations:
            if association.is_a("IfcRelAssociatesClassification"):
                cref = association.RelatingClassification
                refs.append((cref.ReferencedSource, cref.Name))
        

        return facet_evaluation(
            (self.system, self.value) in refs,
            # @todo
            "",
        )

    def get_res(self, inst):
        refs = []
        for association in inst.HasAssociations:
            if association.is_a("IfcRelAssociatesClassification"):
                cref = association.RelatingClassification
                refs.append((cref.ReferencedSource.Name, cref.Name + "_" + cref.ItemReference))
        return refs


        
class property(facet):
    """
    The IDS property facet implenented using `ifcopenshell.util.element`
    """

    parameters = ["name", "propertyset", "value"]
    message = "a property '%(name)s' in '%(propertyset)s' with value '%(value)s'"

    def __call__(self, inst, logger):
        props = ifcopenshell.util.element.get_psets(inst)
        
        pset = props.get(self.propertyset)
        val = pset.get(self.name) if pset else None
        logger.debug("Testing %s == %s", val, self.value)

        di = {
            "name": self.name,
            "propertyset": self.propertyset,
            "value": val,
        }

        if val is not None:
            msg = self.message % di
        else:
            if pset:
                msg = "a set '%(propertyset)s', but no property '%(name)'" % di
            else:
                msg = "no set '%(propertyset)s'" % di

        return facet_evaluation(val == self.value, msg)

    def get_res(self, inst):
        props = ifcopenshell.util.element.get_psets(inst)
        pset = props.get(self.propertyset)
        val = pset.get(self.name) if pset else None

    
        di = {
            "name": self.name,
            "propertyset": self.propertyset,
            "value": val,
        }

        if not pset:
            
            di = {
                "name": 0,
                "propertyset": 0,
                "value": 0,
            }
            return di



        return di



class material(facet):
    """
    The IDS material facet 
    """
    parameters = ["name", "value"]
    message = "a material '%(name)s'"

    def __call__(self, inst, logger):
        material_relations = [rel for rel in inst.HasAssociations if rel.is_a("IfcRelAssociatesMaterial")]

        for rel in material_relations:
            if rel.RelatingMaterial.is_a("IfcMaterialLayerSetUsage"):
                layers = rel.RelatingMaterial.ForLayerSet.MaterialLayers
                names = [layer.Material.Name for layer in layers]

        return facet_evaluation(1,"test")


    def get_res(self, inst):
        material_relations = [rel for rel in inst.HasAssociations if rel.is_a("IfcRelAssociatesMaterial")]
        values = []
        for rel in material_relations:
            if rel.RelatingMaterial.is_a("IfcMaterialLayerSetUsage"):
                layers = rel.RelatingMaterial.ForLayerSet.MaterialLayers
                names = [layer.Material.Name for layer in layers]
                values.append(names)
  
            elif rel.RelatingMaterial.is_a("IfcMaterial"):
                name = rel.RelatingMaterial.Name
                values.append(name)

        return values
                

class boolean_logic:
    """
    Boolean conjunction over a collection of functions
    """

    def __init__(self, terms):
        self.terms = terms

    def __call__(self, *args):
        eval = [t(*args) for t in self.terms]
        join = [" and ", " or "][self.fold == any]
        return facet_evaluation(self.fold(eval), join.join(map(str, eval)))

    def __str__(self):
        return [" and ", " or "][self.fold == any].join(map(str, self.terms))


class boolean_and(boolean_logic):
    fold = all


class boolean_or(boolean_logic):
    fold = any


class restriction:
    """
    The value restriction from XSD implemented as a list of values and a containment test
    """

    def __init__(self, node):
     
        self.options = []
        
        for n in node.childNodes:
            if n.nodeType == n.ELEMENT_NODE and n.tagName.endswith("enumeration"):
                self.options.append(n.getAttribute("value"))
                self.type = "enumeration"

            if n.nodeType == n.ELEMENT_NODE and n.tagName.endswith("Inclusive"):
                self.options.append(n.getAttribute("value"))
                self.type = "bound"
            
            if n.nodeType == n.ELEMENT_NODE and n.tagName.endswith("length"):
                self.options.append(n.getAttribute("value"))
                self.type = "length"
            
            if n.nodeType == n.ELEMENT_NODE and n.tagName.endswith("pattern"):
                self.options.append(n.getAttribute("value"))
                self.type = "pattern"
        

    def __eq__(self, other):
        return other in self.options

    def __repr__(self):
        #todo: different repr according to the type
        return " or ".join(self.options)


class specification:
    """
    Represents the XML <specification> node and its two children <applicability> and <requirements>
    """

    def __init__(self, node):
        def parse_rules(node):
            children = [n for n in node.childNodes if n.nodeType == n.ELEMENT_NODE]
            names = map(operator.attrgetter("tagName"), children)
            classes = map(meta_facet.facets.__getitem__, names)
            return [cls(n) for cls, n in zip(classes, children)]

        phrases = [n for n in node.childNodes if n.nodeType == n.ELEMENT_NODE]

        len(phrases) == 2 or error("expected two child nodes for <specification>")
        phrases[0].tagName == "applicability" or error("expected <applicability>")
        phrases[1].tagName == "requirements" or error("expected <requirements>")

        self.applicability, self.requirements = (boolean_and(parse_rules(phrase)) for phrase in phrases)

    def __call__(self, inst, logger):
        if self.applicability(inst, logger):
            valid = self.requirements(inst, logger)
            if valid:
                logger.info(str(self) + "\n%s has" % inst + " " + str(valid) + " so is compliant")
            else:
                logger.error(str(self) + "\n%s has" % inst + " " + str(valid) + " so is not compliant")

    def __str__(self):
        return "Given an instance with %(applicability)s\nWe expect %(requirements)s" % self.__dict__


class ids:
    """
    Represents the XML root <ids> node and its <specification> childNodes.
    """

    def __init__(self, fn):
        dom = parse(fn)
        ids = dom.childNodes[0]
        ids.tagName == "ids" or error("expected <ids>")

        self.specifications = [
            specification(n) for n in ids.childNodes if n.nodeType == n.ELEMENT_NODE and n.tagName == "specification"
        ]

        
    def validate(self, ifc_file, logger):
        for spec in self.specifications:
            for elem in ifc_file.by_type("IfcObject"):
                spec(elem, logger)


if __name__ == "__main__":
    import sys
    import logging
    import ifcopenshell
    import os
    import json

    logger = logging.getLogger("IDS")
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    ids_file = ids(sys.argv[1])
    ifc_file = ifcopenshell.open(sys.argv[2])
    
    terms = ids_file.specifications[0].requirements.terms

    requirements = ids_file.specifications[0].requirements

    walls = ifc_file.by_type("IfcWall")

    log_to_construct =  {}

    for index, specification in  enumerate(ids_file.specifications):
        log_to_construct[index] = {}
        log_to_construct[index]['applicability'] = {}

        for t_id, t in enumerate(specification.applicability.terms):
            facet_type = type(t).__name__

            if not facet_type in log_to_construct[index]['applicability'].keys():
                log_to_construct[index]['applicability'][facet_type] = {}
            
            param_values = [str(getattr(t,t.parameters[i])) for i in range(len(t.parameters)) ]
           
            zip_iterator = zip(t.parameters, param_values)
            a_dictionary = dict(zip_iterator)

            log_to_construct[index]['applicability'][facet_type][t_id] = a_dictionary

        log_to_construct[index]['requirements'] = {}

    
        for t_id, t in enumerate(specification.requirements.terms):
            
            facet_type = type(t).__name__
      

            if not facet_type in log_to_construct[index]['requirements'].keys():
                log_to_construct[index]['requirements'][facet_type] = {}

            log_to_construct[index]['requirements'][facet_type][t_id] = {}
            log_to_construct[index]['requirements'][facet_type][t_id]['requirements'] = {}
            log_to_construct[index]['requirements'][facet_type][t_id]['values'] = {}

            param_values = [str(getattr(t,t.parameters[i])) for i in range(len(t.parameters)) ]
    
            zip_iterator = zip(t.parameters, param_values)
            a_dictionary = dict(zip_iterator)


            log_to_construct[index]['requirements'][facet_type][t_id]['requirements'] = a_dictionary

            for w in ifc_file.by_type("IfcWall"):
                if facet_type == 'property':
                    log_to_construct[index]['requirements'][facet_type][t_id]['values'][w.GlobalId] = t.get_res(w)

                if facet_type == 'classification':
                    log_to_construct[index]['requirements'][facet_type][t_id]['values'][w.GlobalId] = t.get_res(w)

                if facet_type == 'material':
                    log_to_construct[index]['requirements'][facet_type][t_id]['values'][w.GlobalId] = t.get_res(w)



    # try:
    #     config_path = os.path.join(os.getcwd(), "config.json")
    #     with open(config_path) as json_file:
    #         config = json.load(json_file)

    #         config["results"]["idsdlog"] = "v"
        
    #     with open(config_path, 'w', encoding='utf-8') as f:
    #         json.dump(config, f, ensure_ascii=False, indent=4)
    
    # except:
    #     pass


    ids_results_path = os.path.join(os.getcwd(), "ids_result_bsdd.json")

    with open(ids_results_path, 'w', encoding='utf-8') as f:
        json.dump(log_to_construct, f, ensure_ascii=False, indent=4)
