from textx.metamodel import metamodel_from_file
import textx.model
import os.path
import pkg_resources
from .util import get_filename_in_path

lang_dir = pkg_resources.resource_filename("openuxas_mde", "lang")
uxas_meta = metamodel_from_file(os.path.join(lang_dir, "uxas_schema.tx"))

class UxasSchemaParser:
    def __init__(self, lib_path):
        self.schemas = {}
        self.lib_path = lib_path

    def simplify_ast(self, node):
        if textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["SchemaDef"]):
            xml_params = []
            type_params = []
            messages = {"receives": [], "sends": []}
            if node.params:
                for f in node.params.paramDefs:
                    type_params.append(self.simplify_ast(f))
            if node.messages:
                messages = self.simplify_ast(node.messages)

            if node.xml:
                xml_params = self.simplify_ast(node.xml)

            s = {"type": node.type, "struct_type": node.struct_type, "params": type_params, "xml": xml_params,
                 "messages": messages}
            return s
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["XMLDef"]):
            params = []
            for param in node.params:
                params.append(self.simplify_ast(param))
            return params
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["MessagesDef"]):
            receives_messages = []
            if node.receives_messages:
                receives_messages = ["".join(x.prefix)+x.message for x in node.receives_messages.receives_messages]

            sends_messages = []
            if node.sends_messages:
                sends_messages = ["".join(x.prefix)+x.message for x in node.sends_messages.sends_messages]
            return {"receives": receives_messages, "sends": sends_messages}

        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ParamsDef"]):
            param_defs = []
            for param_def in node.paramDefs:
                param_defs.append(self.simplify_ast(param_def))
            return param_defs
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ParamDef"]):
            param_name = node.paramName
            param_desc = ""
            if node.paramDesc is not None:
                param_desc = node.paramDesc
            required = False
            param_type = {}
            param_values = None
            for attr in node.paramAttrs:
                if attr.attrType == "type":
                    param_type = self.simplify_ast(attr.type)
                elif attr.attrType == "required":
                    required = attr.required
                elif attr.attrType == "values":
                    param_values = []
                    for v in attr.values:
                        param_values.append(self.simplify_ast(v))
            param_type["param_name"] = param_name
            param_type["param_desc"] = param_desc
            param_type["param_required"] = required
            if param_values:
                param_type["param_values"] = param_values
            return param_type
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ParamType"]):
            if node.struct_name:
                return {"param_type": "struct", "struct_type": node.struct_name, "struct_type_name": node.struct_type,
                         "is_array": node.is_array}
            elif node.type_name != "struct":
                return {"param_type": node.type_name, "is_array": node.is_array}
            else:
                anonymous_defs = []
                for param_def in node.paramDefs:
                    anonymous_defs.append(self.simplify_ast(param_def))
                return {"param_type": "struct", "anonymous_struct": { "params": anonymous_defs },
                        "is_array": node.is_array}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ParamDefValue"]):
            return node.paramDefValue
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["Param"]):
            return self.simplify_ast(node.param)
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["TagParam"]):
            return {"type": "tag", "tag_value": self.simplify_ast(node.tag_value.value)}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["AttrParam"]):
            return {"type": "attr", "attr_type": node.attr_type, "attr_value": self.simplify_ast(node.attr_value.value)}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ChildParam"]):
            return {"type": "child", "tag_name": node.tag_name, "child_value": self.simplify_ast(node.child_value.value)}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ChildrenParam"]):
            children_schema = []
            for child in node.children:
                children_schema.append(self.simplify_ast(child.param))
            if node.containing_tag:
                return {"type": "children", "children_source": node.children_source,
                        "children_schema": children_schema,
                        "containing_tag": node.containing_tag.containing_tag }
            else:
                return {"type": "children", "children_source": node.children_source,
                        "children_schema": children_schema}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ForeachParam"]):
            foreach_schema = []
            for f in node.foreach_params:
                foreach_schema.append(self.simplify_ast(f.param))
            return {"type": "foreach", "foreach": node.foreach, "foreach_schema": foreach_schema}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["RenderParam"]):
            if node.containing_tag:
                return {"type": "render", "value": self.simplify_ast(node.value.value),
                        "containing_tag": node.containing_tag.containing_tag}
            else:
                return {"type": "render", "value": self.simplify_ast(node.value.value)}
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas_schema"]["ValueParam"]):
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