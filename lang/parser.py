from textx.metamodel import metamodel_from_file
import collections
import textx.model

uxas_meta = metamodel_from_file("/extra/midas/openuxas-mde/lang/uxas.tx")

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
    def __init__(self):
        self.config = {}
        self.configs = []

    def simplify_ast(self, node):
        if textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["StructValue"]):
            struct_value = {"type": node.type, "struct_type": node.struct_type}
            for field in node.fields:
                if field.fieldValue is None:
                    print("Field "+field.tag+" is None")
                struct_value[field.tag] = self.simplify_ast(field.fieldValue.value)
            return struct_value
        elif textx.textx_isinstance(node, uxas_meta.namespaces["uxas"]["Include"]):
            cfgs = []
            included_cfg = uxas_meta.model_from_file(node.filename)
            for cfg in included_cfg.config:
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
            self.configs.append(self.simplify_ast(cfg))

    def load_config_from_file(self, filename):
        self.config = uxas_meta.model_from_file(filename)
        self.simplify()
#try:
#    uxas_parser = UxasParser()
#    uxas_parser.load_config_from_file("/extra/midas/openuxas-mde/example_waterway.uxas")

#except ParseError as err:
#    print(err.error)
