import xml.etree.ElementTree as ET
import collections

class RenderError(Exception):
    def __init__(self, error):
        self.error = error

class UxasXMLRenderer:
    def __init__(self, schemas):
        self.schemas = schemas

    def get_value(self, obj, value, foreach_map):
        if value["value_type"] == "string":
            return value["value"]
        elif value["value_type"] == "named":
            if value["name"] not in obj:
                raise RenderError("For value "+value["name"]+" no such value in object")
            return obj[value["name"]]
        elif value["value_type"] == "current":
            return obj
        elif value["value_type"] == "foreach":
            if value["foreach"] not in foreach_map:
                raise RenderError("For value "+value["foreach"]+"."+value["name"]+
                                  ", parent structure doesn't declare any foreach types "+value["foreach"])
            return foreach_map[value["foreach"]][value["name"]]
        else:
            return None

    def expand_foreach(self, foreach, top):
        all_foreach = []

        for f in foreach:
            if f not in top:
                print("Warning: No items named " + f + " available for foreach")
                continue

            flist = top[f]
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
        return self.render_with_top(parent, obj, obj)

    def render_with_top(self, parent, obj, top):
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

        return self.render_with_schema(parent, obj, top, xml_schema, {})

    def render_with_schema(self, parent, obj, top, xml_schema, foreach_map):
        tag_name = ""

        if len(xml_schema) == 1 and xml_schema[0]["type"] == "foreach":
            param = xml_schema[0]
            foreach_list = self.expand_foreach(param["foreach"], top)
            first_elem = None
            for foreach_map in foreach_list:
                elem = self.render_with_schema(parent, obj, top, param["foreach_schema"], foreach_map)
                if first_elem is None:
                    first_elem = elem
            return first_elem

        for param in xml_schema:
            if param["type"] == "tag":
                tag_name = self.get_value(obj, param["tag_value"], foreach_map)
                break
            elif param["type"] == "render" and not "containing_tag" in param:
                return self.render_with_top(parent, obj, top)

        if tag_name == "":
            raise RenderError("No XML tag name defined for type "+obj["struct_type"] +
                              " subtype "+obj["type"])

        if parent is None:
            element = ET.Element(tag_name)
        else:
            element = ET.SubElement(parent, tag_name)

        for param in xml_schema:
            if param["type"] == "attr":
                element.attrib[param["attr_type"]] = str(self.get_value(obj, param["attr_value"], foreach_map))
            elif param["type"] == "children":
                children = []
                if param["children_source"] in obj:
                    children = obj[param["children_source"]]
                child_container = element
                if "containing_tag" in param and param["containing_tag"] is not None:
                    child_container = ET.SubElement(element, param["containing_tag"])
                for child in children:
                    self.render_with_schema(child_container, child, top, param["children_schema"], foreach_map)
            elif param["type"] == "child":
                child_elem = ET.SubElement(element, param["tag_name"])
                child_elem.text = str(self.get_value(obj, param["child_value"], foreach_map))
            elif param["type"] == "foreach":
                foreach_list = self.expand_foreach(param["foreach"], top)
                for foreach_map in foreach_list:
                    self.render_with_schema(element, obj, top, param["foreach_schema"], foreach_map)
            elif param["type"] == "value":
                element.text = str(self.get_value(obj, param["value"], foreach_map))
            elif param["type"] == "render":
                child_container = element
                if "containing_tag" in param and param["containing_tag"] is not None:
                    child_container = ET.SubElement(element, param["containing_tag"])
                object_to_render = self.get_value(obj, param["value"], foreach_map)
                self.render_with_top(child_container, object_to_render, top)

        return element
