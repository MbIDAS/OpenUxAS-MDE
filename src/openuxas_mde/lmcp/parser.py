from textx.metamodel import metamodel_from_file
import textx.model
import os.path
import sys
import pkg_resources
from openuxas_mde.lang.util import get_filename_in_path


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


lang_dir = pkg_resources.resource_filename("openuxas_mde", "lmcp")
lmcp_meta = metamodel_from_file(os.path.join(lang_dir, "../lib/lmcp.tx"))

class LMCPParser:
    def __init__(self, lib_path):
        self.configs = {}
        self.lib_dir = lib_path

    def simplify_ast(self, node):
        if textx.textx_isinstance(node, lmcp_meta.namespaces["lmcp"]["lmcpConfig"]):
            simplified_enums = []
            for e in node.enums.enumList:
                simplified_enums.append(self.simplify_ast(e))

            simplified_structs = []
            for s in node.structs.structList:
                simplified_structs.append(self.simplify_ast(s))

            return {"struct_type": "mdm", "type": "", "seriesName": node.seriesName, "namespace": node.namespace,
                    "version": node.version, "enums": simplified_enums,
                    "structs": simplified_structs}
        elif textx.textx_isinstance(node, lmcp_meta.namespaces["lmcp"]["lmcpEnum"]):
            value_list = []
            for v in node.values:
                value_list.append({"struct_type": "Entry", "type": "", "name": v.enumName, "value": v.enumValue.value})
            return {"struct_type": "Enum", "type": "", "name": node.name, "values": value_list}
        elif textx.textx_isinstance(node, lmcp_meta.namespaces["lmcp"]["lmcpStruct"]):
            extension = None
            if node.extension is not None:
                extension = node.extension.reference
            fields = []
            for f in node.fields:
                fields.append(self.simplify_ast(f))
            return {"struct_type": "Struct", "type": "", "name": node.name, "extends": extension, "fields": fields}
        elif textx.textx_isinstance(node, lmcp_meta.namespaces["lmcp"]["lmcpStructField"]):
            default = None
            if node.default is not None:
                default = node.default.value.value
            units = None
            if node.units is not None:
                units = node.units.value
            size = None
            arraySuffix=""
            if node.size is not None:
                size = node.size.size
                arraySuffix = "[]"
            return {"struct_type": "Field", "name": node.name, "type": node.type+arraySuffix, "size": size,
                    "default": default, "units": units}

    def simplify(self, config):
        return self.simplify_ast(config)

    def load_config_from_file(self, filename):
        try:
            config = lmcp_meta.model_from_file(filename)
            return self.simplify(config)
        except textx.exceptions.TextXSyntaxError as exc:
            self.diagnose_syntax_error(exc, filename)

    def diagnose_syntax_error(self, exc, filename):
        f = open(filename, 'r')
        curr_line = 0
        for line in f:
            curr_line += 1
            if curr_line > exc.line:
                break
            if self.count_quotes(line) % 2 == 1:
                print(exc.message)
                print("Possible unclosed quote in file "+filename+" at line "+str(curr_line))
                print(line)
                raise ParseError(exc)
        print(exc.message)
        raise ParseError(exc)


    def count_quotes(self, line):
        pos = 0
        quote_count = 0
        while pos < len(line):
            if line[pos] == '"':
                if pos < len(line)-1:
                    if line[pos+1] != '"':
                        quote_count += 1
                    else:
                        pos += 2
                        continue
            pos += 1
        return quote_count