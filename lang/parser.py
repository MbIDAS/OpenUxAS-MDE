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
        if textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["StructValue"]):
            struct_value = {"type": node.type, "struct_type": node.struct_type}
            for field in node.fields:
                if field.fieldValue is not None:
                    struct_value[field.tag] = self.simplify_ast(field.fieldValue.value)
                elif field.include is not None:
                    simplified = self.simplify_ast(field.include)
                    for simp in simplified:
                        for k, v in simp.items():
                            struct_value[k] = v

            if struct_value["struct_type"] not in self.config_types:
                self.config_types[struct_value["struct_type"]] = [struct_value]
            else:
                self.config_types[struct_value["struct_type"]].append(struct_value)

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
                    cfgs.append(self.simplify_ast(cfg))
            return cfgs
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["ArrayValue"]):
            vals = []
            for v in node.values:
                simplified = self.simplify_ast(v.value)
                if not isinstance(simplified, list):
                    vals.append(simplified)
                else:
                    vals = vals + simplified
            return vals
        else:
            return node

    def simplify(self):
        for cfg in self.config.config:
            simplified = self.simplify_ast(cfg)
            self.configs.append(simplified)

        for cfglist in self.config_types.values():
            for cfg in cfglist:
                continue
                if len(cfg["foreach"]) == 0:
                    continue

                all_foreach = []

                for f in cfg["foreach"]:
                    if f not in cfg:
                        print("Warning: No items named "+f+" available for foreach in "+
                              cfg["struct_type"]+" "+cfg["type"])
                        continue

                    flist = cfg[f]
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

                cfg["foreach"] = all_foreach

    def load_config_from_file(self, filename):
        self.config = uxas_meta.model_from_file(filename)
        self.simplify()
