import xml.etree.ElementTree as ET

class Environment:
    def __init__(self, dict, next_env=None):
        self.dict = dict
        self.next = next_env

    def lookup(self, key):
        if key in self.dict:
            return self.dict[key]
        elif self.next is not None:
            return self.next.lookup(key)
        else:
            return None


class RenderError(Exception):
    def __init__(self, error):
        self.error = error

class LMCPXMLRenderer:
    def __init__(self, schemas):
        self.schemas = schemas

    def get_value(self, obj, value, env, foreach_map):
        if value["value_type"] == "string":
            return value["value"]
        elif value["value_type"] == "named":
            if value["name"] not in obj:
                raise RenderError("For value "+value["name"]+" no such value in object")
            obj_value = obj[value["name"]]
            return obj_value
        elif value["value_type"] == "current":
            return obj
        elif value["value_type"] == "foreach":
            if value["foreach"] not in foreach_map:
                raise RenderError("For value "+value["foreach"]+"."+value["name"]+
                                  ", parent structure doesn't declare any foreach types "+value["foreach"])
            return foreach_map[value["foreach"]][value["name"]]
        else:
            return None

    def expand_foreach(self, foreach, env):
        all_foreach = []

        for f in foreach:
            flist = env.lookup(f)
            if flist is None:
                print("Warning: No items named " + f + " available for foreach")
                continue

            if len(all_foreach) == 0:
                for fitem in flist:
                    all_foreach.append({f: fitem})
            else:
                new_all = []
                for fitem in flist:
                    for allitem in all_foreach:
                        c = allitem.copy()
                        c[f] = fitem
                        new_all.append(c)
                all_foreach = new_all
        return all_foreach

    def render(self, parent, obj):
        return self.render_with_env(parent, obj, Environment(obj))

    def render_with_env(self, parent, obj, env):
        if obj["struct_type"] not in self.schemas:
            raise RenderError("No schema definition for type "+obj["struct_type"])

        s1 = self.schemas[obj["struct_type"]]

        if obj["type"] in s1:
            schema = s1[obj["type"]]
        elif "" in s1:
            schema = s1[""]
        else:
            raise RenderError("No schema definition for type "+obj["struct_type"] +
                              " subtype "+obj["type"])


        if "xml" not in schema:
            raise RenderError("No XML description for type "+obj["struct_type"] +
                              " subtype "+obj["type"])

        xml_schema = schema["xml"]

        return self.render_with_schema(parent, obj, env, xml_schema, {})

    def render_with_schema(self, parent, obj, env, xml_schema, foreach_map):
        if type(obj) is dict:
            if "variable_definitions" in obj:
                variable_environments = [[]]
                for variable_definition in obj["variable_definitions"]:
                    referenced = variable_definition["reference"]
                    new_ve = []
                    if type(referenced) is list:
                        for ve in variable_environments:
                            for item in referenced:
                                ve2 = ve[:]
                                ve2.append([variable_definition["variable"], item])
                                new_ve.append(ve2)
                    else:
                        for ve in variable_environments:
                            ve2 = ve[:]
                            ve2.append([variable_definition["variable"], referenced])
                            new_ve.append(ve2)

                    variable_environments = new_ve

                    for ve in variable_environments:
                        new_dict = {}
                        for vr in ve:
                            new_dict[vr[0]] = vr[1]
                        new_env = Environment(new_dict, env)
                        self.render_with_schema_impl(parent, obj, new_env, xml_schema, foreach_map)
            else:
                return self.render_with_schema_impl(parent, obj, env, xml_schema, foreach_map)
        else:
            return self.render_with_schema_impl(parent, obj, env, xml_schema, foreach_map)

    def render_with_schema_impl(self, parent, obj, env, xml_schema, foreach_map):
        tag_name = ""

        if len(xml_schema) == 1 and xml_schema[0]["type"] == "foreach":
            param = xml_schema[0]
            foreach_list = self.expand_foreach(param["foreach"], env)
            first_elem = None
            for foreach_map in foreach_list:
                elem = self.render_with_schema(parent, obj, env, param["foreach_schema"], foreach_map)
                if first_elem is None:
                    first_elem = elem
            return first_elem

        for param in xml_schema:
            if param["type"] == "tag":
                tag_name = self.get_value(obj, param["tag_value"], env, foreach_map)
                break
            elif param["type"] == "render" and not "containing_tag" in param:
                return self.render_with_env(parent, obj, env)

        if tag_name == "":
            raise RenderError("No XML tag name defined for type "+obj["struct_type"] +
                              " subtype "+obj["type"])

        if parent is None:
            element = ET.Element(tag_name)
        else:
            element = ET.SubElement(parent, tag_name)

        for param in xml_schema:
            if param["type"] == "attr":
                v = self.get_value(obj, param["attr_value"], env, foreach_map)
                if v is not None:
                    element.attrib[param["attr_type"]] = str(v)
            elif param["type"] == "children":
                children = []
                if param["children_source"] in obj:
                    children = obj[param["children_source"]]
                child_container = element
                if "containing_tag" in param and param["containing_tag"] is not None:
                    child_container = ET.SubElement(element, param["containing_tag"])
                for child in children:
                    self.render_with_schema(child_container, child, env, param["children_schema"], foreach_map)
            elif param["type"] == "child":
                v = self.get_value(obj, param["child_value"], env, foreach_map)
                if v is not None:
                    child_elem = ET.SubElement(element, param["tag_name"])
                    child_elem.text = str(v)
            elif param["type"] == "reference":
                collection = env.lookup(param["collection"])
                if collection is None:
                    raise RenderError("No collection of items named "+param["collection"])
                for item in collection:
                    if item["type"] == param["name"]:
                        if param["param"] not in item:
                            raise RenderError("Can't find "+param["param"]+" in item "+param["name"]+" in "+param["collection"])
                    element.text = str(item[param["name"]])
            elif param["type"] == "foreach":
                foreach_list = self.expand_foreach(param["foreach"], env)
                for foreach_map in foreach_list:
                    self.render_with_schema(element, obj, env, param["foreach_schema"], foreach_map)
            elif param["type"] == "value":
                v = self.get_value(obj, param["value"], env, foreach_map)
                if v is not None:
                    element.text  = str(v)
            elif param["type"] == "render":
                child_container = element
                if "containing_tag" in param and param["containing_tag"] is not None:
                    child_container = ET.SubElement(element, param["containing_tag"])
                object_to_render = self.get_value(obj, param["value"], env, foreach_map)
                self.render_with_env(child_container, object_to_render, env)

        return element
