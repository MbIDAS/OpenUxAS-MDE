import argparse
import os
import sys

from lang.parser import UxasParser
from lang.schema import UxasSchemaParser

def load_uxas_schemas(lib_path):
    uxas_schema_parser = UxasSchemaParser(lib_path)
    uxas_schema_parser.load_schema_from_file("network_schema.uxsch")
    uxas_schema_parser.load_schema_from_file("standard_services_schema.uxsch")
    uxas_schema_parser.load_schema_from_file("uxas_configuration_schema.uxsch")
    uxas_schema_parser.load_schema_from_file("standard_vehicles_schema.uxsch")
    uxas_schema_parser.load_schema_from_file("standard_plans_schema.uxsch")

    return uxas_schema_parser

system_lib_path = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "lib")

arg_parser = argparse.ArgumentParser(description="Generate Graphviz graph of service messaging")
arg_parser.add_argument('-libpath', nargs=1, default="")

parsed_args, rest_args = arg_parser.parse_known_args()
parsed_args = vars(parsed_args)

lib_path_args = []
if "libpath" in parsed_args:
    if isinstance(parsed_args["libpath"], list):
        lib_path_args = parsed_args["libpath"][0].split(os.pathsep)
    else:
        lib_path_args = parsed_args["libpath"].split(os.pathsep)

lib_path = lib_path_args + [system_lib_path]
uxas_schema_parser = load_uxas_schemas(lib_path)

senders = {}
receivers = {}

for s in uxas_schema_parser.schemas["service"].values():
    if "messages" not in s:
        continue
    if "sends" in s["messages"]:
        for send in s["messages"]["sends"]:
            send = send.split(".")[-1]
            if not send in senders:
                senders[send] = [s["type"]]
            else:
                senders[send].append(s["type"])
    if "receives" in s["messages"] :
        for recv in s["messages"]["receives"]:
            recv = recv.split(".")[-1]
            if not recv in receivers:
                receivers[recv] = [s["type"]]
            else:
                receivers[recv].append(s["type"])

services_graph = open("service_interaction.graphml", "w")
print(
"""<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:java="http://www.yworks.com/xml/yfiles-common/1.0/java"
         xmlns:sys="http://www.yworks.com/xml/yfiles-common/markup/primitives/2.0"
         xmlns:x="http://www.yworks.com/xml/yfiles-common/markup/2.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:y="http://www.yworks.com/xml/graphml"
         xmlns:yed="http://www.yworks.com/xml/yed/3"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd">
  <key for="node" id="d5" yfiles.type="nodegraphics"/>
  <key for="edge" id="d9" yfiles.type="edgegraphics"/>
  <graph id="UxAS" edgedefault="directed">
""", file=services_graph)

for s in uxas_schema_parser.schemas["service"].values():
    print(
"""    <node id="%s">
         <data key="d5">
           <y:ShapeNode>
             <y:Geometry width="250" height="50"/>
             <y:NodeLabel fontSize="12">%s</y:NodeLabel>
           </y:ShapeNode>
         </data>
       </node>""" % (s["type"],s["type"]), file=services_graph)

for s in uxas_schema_parser.schemas["service"].values():
    if "messages" not in s:
        continue

    if "sends" in s["messages"]:
        for send in s["messages"]["sends"]:
            send = send.split(".")[-1]
            if send in receivers:
                for recv in receivers[send]:
                    print("""
    <edge id="%s_%s" source="%s" target="%s">
      <data key="d9">
        <y:ShapeLabel>
          <y:EdgeLabel>%s</y:EdgeLabel>
        </y:ShapeLabel>
      </data>
    </edge>"""            % (s["type"], recv, s["type"], recv, send), file=services_graph)

print("""
  </graph>
</graphml>
""", file=services_graph)
services_graph.close()