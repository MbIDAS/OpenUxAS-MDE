from lang.parser import UxasParser
from lang.schema import UxasSchemaParser
from target.render import UxasXMLRenderer
import xml.etree.ElementTree as ET

uxas_parser = UxasParser()
uxas_parser.load_config_from_file("/extra/midas/openuxas-mde/example_waterway.uxas")

uxas_vehicle_parser = UxasParser()
uxas_vehicle_parser.load_config_from_file("/extra/midas/openuxas-mde/waterway_vehicles.uxas")

uxas_schema_parser = UxasSchemaParser()
uxas_schema_parser.load_schema_from_file("/extra/midas/openuxas-mde/network_schema.uxsch")
uxas_schema_parser.load_schema_from_file("/extra/midas/openuxas-mde/standard_services_schema.uxsch")
uxas_schema_parser.load_schema_from_file("/extra/midas/openuxas-mde/uxas_configuration_schema.uxsch")

renderer = UxasXMLRenderer(uxas_schema_parser.schemas)

config = renderer.render(None, uxas_parser.configs[0])

tree = ET.ElementTree(config)
#with open("example_waterwaycfg.xml", mode='w', encoding='utf-8') as out_file:
tree.write("example_waterwaycfg.xml")

#print(ET.dump(config))
