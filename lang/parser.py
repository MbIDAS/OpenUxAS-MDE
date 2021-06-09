from textx.metamodel import metamodel_from_file
import textx.model
import os.path
import sys
from .util import get_filename_in_path

lang_dir = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "lang")
uxas_meta = metamodel_from_file(os.path.join(lang_dir, "uxas.tx"))

class ParseError(Exception):
    def __init__(self, error, obj=None, parser=None):
        self.error = error
        self.line = -1
        self.col = -1
        if obj is not None and parser is not None:
            line, col = parser.pos_to_linecol(obj._tx_position)
            self.line = line
            self.col = col
            self.error = "Line {}, Col {}: {}".format(line, col, self.error)


class UxasParser:
    def __init__(self, lib_path):
        self.config = {}
        self.configs = []
        self.config_types = {}
        self.lib_dir = lib_path

    def simplify_ast(self, node):
        if textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["StructValue"]) or \
           textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["OverrideStruct"]):
            struct_value = {"type": node.type, "struct_type": node.struct_type,
                            "_is_override": textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["OverrideStruct"])
            }
            for param in node.params:
                if param.paramValue is not None:
                    struct_value[param.tag] = self.simplify_ast(param.paramValue.value)
                elif param.include is not None:
                    simplified = self.simplify_ast(param.include)
                    for simp in simplified:
                        for k, v in simp.items():
                            if k not in struct_value or (v != "" and struct_value[k] == ""):
                                struct_value[k] = v
            if node.variable_definitions is not None:
                variable_definitions = []
                for var_def in node.variable_definitions.variable_definition:
                    variable_definitions.append({"variable": var_def.variable_name,
                                                 "reference": self.simplify_ast(var_def.reference)})
                struct_value["variable_definitions"] = variable_definitions
            if struct_value["struct_type"] not in self.config_types:
                self.config_types[struct_value["struct_type"]] = [struct_value]
            else:
                self.config_types[struct_value["struct_type"]].append(struct_value)

            return struct_value


        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["RemoveStruct"]):
            struct_value = {"is_remove": True, "struct_type": node.struct_type, "type": node.type}
            return struct_value
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["Include"]):
            cfgs = []
            included_cfg = []
            filename = get_filename_in_path(["."] + self.lib_dir, node.filename)
            included_cfg = uxas_meta.model_from_file(filename)

            for cfg in included_cfg.config:
                if node.include_ref:
                    if cfg.type == node.include_ref.item_ref:
                        cfgs.append(self.simplify_ast(cfg))
                else:
                    simplified = self.simplify_ast(cfg)
                    cfgs.append(self.simplify_ast(cfg))
            return cfgs
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["ArrayValue"]):
            vals = []
            for v in node.values:
                simplified = self.simplify_ast(v.value)
                if not isinstance(simplified, list):
                    if isinstance(simplified, dict):
                        if "_is_override" in simplified and simplified["_is_override"]:
                            for i in range(0, len(vals)):
                                curr_val = vals[i]
                                if "struct_type" in curr_val:
                                    if curr_val["struct_type"] == simplified["struct_type"] and \
                                       curr_val["type"] == simplified["type"]:
                                        for param in simplified.keys():
                                            if param == "type" or param == "struct_type" or param == "_is_override":
                                                continue
                                            curr_val[param] = simplified[param]
                                        break
                        elif "is_remove" in simplified:
                            for i in range(0, len(vals)):
                                curr_val = vals[i]
                                if "struct_type" in curr_val:
                                    if curr_val["struct_type"] == simplified["struct_type"] and \
                                            curr_val["type"] == simplified["type"]:
                                        vals = vals[:i]+vals[i+1:]
                                        break
                        else:
                            vals.append(simplified)
                    else:
                        vals.append(simplified)
                else:
                    vals = vals + simplified
            return vals
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["ReferenceValue"]):
            param_list = []
            for param in node.param_list:
                param_list.append(param.param)
            if node.reference.name is not None:
                return {"category": node.reference.category, "name": node.reference.name, "param_list": param_list}
            else:
                return {"category": node.reference.category, "param_list": param_list}
        else:
            return node

    def simplify(self):
        for cfg in self.config.config:
            simplified = self.simplify_ast(cfg)
            self.configs.append(simplified)

    def load_config_from_file(self, filename):
        self.config = uxas_meta.model_from_file(filename)
        self.simplify()
