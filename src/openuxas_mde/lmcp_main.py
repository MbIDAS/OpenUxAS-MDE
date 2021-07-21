import argparse
import os

import pkg_resources
import xml

from openuxas_mde.lang.schema import UxasSchemaParser
from openuxas_mde.lmcp.parser import LMCPParser
from openuxas_mde.lmcp.render import LMCPXMLRenderer
import xml.etree.ElementTree as ET


def load_lmcp_schemas(lib_path):
    lmcp_schema_parser = UxasSchemaParser(lib_path)

    lmcp_schema_parser.load_schema_from_file("lmcp_schema.lmcpsch")

    return lmcp_schema_parser

def write_elementtree(elem, filename):
    xmlstr = xml.dom.minidom.parseString(ET.tostring(elem)).toprettyxml()
    xmlstr_temp = xmlstr.replace("?>", "?>\n<!DOCTYPE MDM SYSTEM 'MDM.DTD'>")
    file = open(filename, "w")
    file.write(xmlstr_temp)
    file.close()

def lmcp_main():
    system_lib_path = pkg_resources.resource_filename("openuxas_mde", "lib")

    default_output_dir = os.curdir

    arg_parser = argparse.ArgumentParser(description="Generate LMCP definition")
    arg_parser.add_argument('-libpath', nargs=1, default=[""])
    arg_parser.add_argument('-o', nargs=1, default=[default_output_dir])

    parsed_args, rest_args = arg_parser.parse_known_args()
    parsed_args = vars(parsed_args)

    output_dir = parsed_args["o"][0]

    lib_path_args = []
    if "libpath" in parsed_args:
        if isinstance(parsed_args["libpath"], list):
            lib_path_args = parsed_args["libpath"][0].split(os.pathsep)
        else:
            lib_path_args = parsed_args["libpath"].split(os.pathsep)

    lib_path = lib_path_args + [system_lib_path]

    lmcp_parser = LMCPParser(lib_path)
    cfg = lmcp_parser.load_config_from_file("/extra/midas/openuxas-mde/test/TestSeries.lmcp")

#    print(cfg)

    lmcp_schema_parser = load_lmcp_schemas(lib_path)
    lmcp_renderer = LMCPXMLRenderer(lmcp_schema_parser.schemas)

    lmcp_xml = lmcp_renderer.render(None, cfg)


    xml_filename = cfg["seriesName"]+".xml"
    write_elementtree(lmcp_xml, os.path.join(output_dir, xml_filename))

if __name__ == '__main__':
    lmcp_main()
