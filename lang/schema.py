from textx.metamodel import metamodel_from_file
import textx.model
import os.path
import sys


lang_dir = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "lang")
uxas_meta = metamodel_from_file(os.path.join(lang_dir, "uxas_schema.tx"))

class UxasSchemaParser:
    def __init__(self):
        self.schemas = {}

    def simplify_ast(self, node):
        if textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["SchemaDef"]):
            xml_fields = []
            if node.xml:
                xml_fields = self.simplify_ast(node.xml)
            s = {"type": node.type, "struct_type": node.struct_type, "xml": xml_fields}
            return s
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["XMLDef"]):
            fields = []
            for field in node.fields:
                fields.append(self.simplify_ast(field))
            return fields
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["Field"]):
            return self.simplify_ast(node.field)
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["TagField"]):
            return {"type": "tag", "tag_value": self.simplify_ast(node.tag_value.value)}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["AttrField"]):
            return {"type": "attr", "attr_type": node.attr_type, "attr_value": self.simplify_ast(node.attr_value.value)}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ChildField"]):
            return {"type": "child", "tag_name": node.tag_name, "child_value": self.simplify_ast(node.child_value.value)}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ChildrenField"]):
            children_schema = []
            for child in node.children:
                children_schema.append(self.simplify_ast(child.field))
            if node.containing_tag:
                return {"type": "children", "children_source": node.children_source,
                        "children_schema": children_schema,
                        "containing_tag": node.containing_tag.containing_tag }
            else:
                return {"type": "children", "children_source": node.children_source,
                        "children_schema": children_schema}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ForeachField"]):
            foreach_schema = []
            for f in node.foreach_fields:
                foreach_schema.append(self.simplify_ast(f.field))
            return {"type": "foreach", "foreach": node.foreach, "foreach_schema": foreach_schema}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["RenderField"]):
            if node.containing_tag:
                return {"type": "render", "value": self.simplify_ast(node.value.value),
                        "containing_tag": node.containing_tag.containing_tag}
            else:
                return {"type": "render", "value": self.simplify_ast(node.value.value)}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ValueField"]):
            return {"type": "value", "value": self.simplify_ast(node.value.value)}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["StringValue"]):
            return {"value_type": "string", "value": node.string_value}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["NamedValue"]):
            return {"value_type": "named", "name": node.name}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ForeachValue"]):
            return {"value_type": "foreach", "foreach": node.foreach, "name": node.name}
        elif node == "_":
            return {"value_type": "current"}
        else:
            return node

    def load_schema_from_file(self, filename):
        schemas = uxas_meta.model_from_file(filename)
        for schema in schemas.schemas:
            simplified_schema = self.simplify_ast(schema)
            if simplified_schema["struct_type"] not in self.schemas:
                self.schemas[simplified_schema["struct_type"]] = { simplified_schema["type"]: simplified_schema }
            else:
                self.schemas[simplified_schema["struct_type"]][simplified_schema["type"]] = simplified_schema