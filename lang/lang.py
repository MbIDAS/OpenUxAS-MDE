from textx.metamodel import metamodel_from_file
from textx.export import metamodel_export, model_export
from textx.exceptions import TextXSemanticError, TextXSyntaxError
import textx.model

from xml.etree import ElementTree

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


def process_uxas_ast(parser, ast):
    pass


def process_uxas_file(file_model):
    parser = file_model._tx_parser
    for config_item in file_model.config:
        if config_item.struct_type != "uxas":
            raise ParseError("Only uxas configurations are allowed at top level", config_item, parser)
        process_uxas_ast(parser, config_item)


uxas_meta = metamodel_from_file("/extra/midas/openuxas-mde/lang/uxas.tx")
uxas_file = uxas_meta.model_from_file("/extra/midas/openuxas-mde/example_waterway.uxas")

try:
    process_uxas_file(uxas_file)
except ParseError as err:
    print(err.error)
