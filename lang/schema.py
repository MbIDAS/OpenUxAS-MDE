from textx.metamodel import metamodel_from_file
import textx.model
import os.path
import sys
from .util import get_filename_in_path

lang_dir = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "lang")
uxas_meta = metamodel_from_file(os.path.join(lang_dir, "uxas_schema.tx"))

class UxasSchemaParser:
    def __init__(self, lib_path):
        self.schemas = {}
        self.lib_path = lib_path

    def simplify_ast(self, node):
        if textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["SchemaDef"]):
            xml_fields = []
            type_fields = []
            if node.fields:
                for f in node.fields.fieldDefs:
                    type_fields.append(self.simplify_ast(f))
            if node.xml:
                xml_fields = self.simplify_ast(node.xml)
            s = {"type": node.type, "struct_type": node.struct_type, "fields": type_fields, "xml": xml_fields}
            return s
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["XMLDef"]):
            fields = []
            for field in node.fields:
                fields.append(self.simplify_ast(field))
            return fields
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["FieldsDef"]):
            field_defs = []
            for field_def in node.fieldDefs:
                field_defs.append(self.simplify_ast(field_def))
            return field_defs
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["FieldDef"]):
            field_name = node.fieldName
            required = False
            field_type = {}
            field_values = None
            for attr in node.fieldAttrs:
                if attr.attrType == "type":
                    field_type = self.simplify_ast(attr.type)
                elif attr.attrType == "required":
                    required = attr.required
                elif attr.attrType == "values":
                    field_values = []
                    for v in attr.values:
                        field_values.append(self.simplify_ast(v))
            field_type["field_name"] = field_name
            field_type["field_required"] = required
            if field_values:
                field_type["field_values"] = field_values
            return field_type
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["FieldType"]):
            if node.struct_name:
                return {"field_type": "struct", "struct_type": node.struct_name, "struct_type_name": node.struct_type,
                         "is_array": node.is_array}
            elif node.type_name != "struct":
                return {"field_type": node.type_name, "is_array": node.is_array}
            else:
                anonymous_defs = []
                for field_def in node.fieldDefs:
                    anonymous_defs.append(self.simplify_ast(field_def))
                return {"field_type": "struct", "anonymous_struct": { "fields": anonymous_defs },
                        "is_array": node.is_array}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["FieldDefValue"]):
            return node.fieldDefValue
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
        filename_in_path = get_filename_in_path(self.lib_path, filename)
        schemas = uxas_meta.model_from_file(filename_in_path)
        for schema in schemas.schemas:
            simplified_schema = self.simplify_ast(schema)
            if simplified_schema["struct_type"] not in self.schemas:
                self.schemas[simplified_schema["struct_type"]] = { simplified_schema["type"]: simplified_schema }
            else:
                self.schemas[simplified_schema["struct_type"]][simplified_schema["type"]] = simplified_schema