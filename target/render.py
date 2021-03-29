import xml.etree.ElementTree as ET

class RenderError(Exception):
    def __init__(self, error):
        self.error = error

class UxasXMLRenderer:
    def __init__(self, schemas):
        self.schemas = schemas

    def get_value(self, obj, value):
        if value["value_type"] == "string":
            return value["value"]
        elif value["value_type"] == "named":
            return obj[value["name"]]
        elif value["value_type"] == "current":
            return obj
        else:
            return None

    def render(self, parent, obj):
        if obj["struct_type"] not in self.schemas:
            raise RenderError("No schema definition for type "+obj["struct_type"])

        s1 = self.schemas[obj["struct_type"]]

        if obj["type"] not in s1:
            raise RenderError("No schema definition for type "+obj["struct_type"] +
                              " subtype "+obj["type"])

        schema = s1[obj["type"]]

        if "xml" not in schema:
            raise RenderError("No XML description for type "+obj["struct_type"] +
                              " subtype "+obj["type"])

        xml_schema = schema["xml"]

        return self.render_with_schema(parent, obj, xml_schema)

    def render_with_schema(self, parent, obj, xml_schema):
        tag_name = ""

        for field in xml_schema:
            if field["type"] == "tag":
                tag_name = self.get_value(obj, field["tag_value"])
            elif field["type"] == "render":
                return self.render(parent, obj)

        if tag_name == "":
            raise RenderError("No XML tag name defined for type "+obj["struct_type"] +
                              " subtype "+obj["type"])

        if parent is None:
            element = ET.Element(tag_name)
        else:
            element = ET.SubElement(parent, tag_name)

        for field in xml_schema:
            if field["type"] == "attr":
                element.attrib[field["attr_type"]] = str(self.get_value(obj, field["attr_value"]))
            elif field["type"] == "children":
                children = obj[field["children_source"]]
                for child in children:
                    self.render_with_schema(element, child, field["children_schema"])
            elif field["type"] == "value":
                element.text = self.get_value(obj, field["value"])
            elif field["type"] == "render":
                object_to_render = self.get_value(obj, field["value"])
                self.render(parent, object_to_render)

        return element
