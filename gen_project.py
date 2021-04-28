from lang.parser import UxasParser
from lang.schema import UxasSchemaParser
from target.render import UxasXMLRenderer
import xml.etree.ElementTree as ET
import os
import sys
import datetime
import xml.dom.minidom
import argparse

def load_uxas_schemas(lib_dir):
    uxas_schema_parser = UxasSchemaParser()
    uxas_schema_parser.load_schema_from_file(os.path.join(lib_dir, "network_schema.uxsch"))
    uxas_schema_parser.load_schema_from_file(os.path.join(lib_dir, "standard_services_schema.uxsch"))
    uxas_schema_parser.load_schema_from_file(os.path.join(lib_dir, "uxas_configuration_schema.uxsch"))
    uxas_schema_parser.load_schema_from_file(os.path.join(lib_dir, "standard_vehicles_schema.uxsch"))
    uxas_schema_parser.load_schema_from_file(os.path.join(lib_dir, "standard_plans_schema.uxsch"))

    return uxas_schema_parser

def load_amase_schemas(lib_dir):
    amase_schema_parser = UxasSchemaParser()

    amase_schema_parser.load_schema_from_file(os.path.join(lib_dir, "amase_schema.uxsch"))
    return amase_schema_parser

def write_elementtree(elem, filename):
    xmlstr = xml.dom.minidom.parseString(ET.tostring(elem)).toprettyxml()
    file = open(filename, "w")
    file.write(xmlstr)
    file.close()


lib_dir = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "lib")

arg_parser = argparse.ArgumentParser(description="Generate UxAS Configuration")
arg_parser.add_argument('-lib', nargs=2, default=lib_dir)

parsed_args, rest_args = arg_parser.parse_known_args()
parsed_args = vars(parsed_args)

lib_dir = parsed_args["lib"]

print("lib_dir = ", lib_dir)
uxas_schema_parser = load_uxas_schemas(lib_dir)

uxas_parser = UxasParser(lib_dir)
if len(rest_args) > 0:
    uxas_parser.load_config_from_file(rest_args[0])

uxas_plan_parser = UxasParser(lib_dir)
if len(rest_args) > 1:
    uxas_plan_parser.load_config_from_file(rest_args[1])

renderer = UxasXMLRenderer(uxas_schema_parser.schemas)

amase_schema_parser = load_amase_schemas(lib_dir)

amase_renderer = UxasXMLRenderer(amase_schema_parser.schemas)

messages = []
os.makedirs("MessagesToSend/tasks", 0o777, exist_ok=True)

scen_veh_list = []
scen_veh_state_list = []

for vehicle_id in uxas_plan_parser.configs[0]["Entities"]:
    for vehicle in uxas_parser.configs[0]["vehicles"]:
        if vehicle["ID"] != vehicle_id:
            continue

        vehicle_xml = renderer.render(None, vehicle)
        tree = ET.ElementTree(vehicle_xml)
        filename = "AirVehicleConfiguration_V"+str(vehicle_id)+".xml"
        messages.append({"MessageFileName": filename, "SendTime_ms": 200})
        write_elementtree(vehicle_xml, "MessagesToSend/"+filename)
        scen_veh_list.append(vehicle)

        vehicle_state_xml = renderer.render(None, vehicle["state"])
        tree = ET.ElementTree(vehicle_state_xml)
        filename = "AirVehicleState_V"+str(vehicle_id)+".xml"
        messages.append({"MessageFileName": filename, "SendTime_ms": 250})
        write_elementtree(vehicle_state_xml, "MessagesToSend/"+filename)
        scen_veh_state_list.append(vehicle["state"])

amase_config = {
    "struct_type": "amase",
    "type": "",
    "ScenarioData": uxas_plan_parser.configs[0]["ScenarioData"],
    "ScenarioEventList": scen_veh_list + scen_veh_state_list
}

for task in uxas_plan_parser.configs[0]["Tasks"]:
    task_xml = renderer.render(None, task)
    tree = ET.ElementTree(task_xml)
    filename = "tasks/"+str(task["TaskID"])+"_"+task["Label"]+".xml"
    messages.append({"MessageFileName": filename, "SendTime_ms": 300})
    write_elementtree(task_xml, "MessagesToSend/"+filename)

for sched in uxas_plan_parser.configs[0]["Schedule"]:
    sched_xml = renderer.render(None, sched)
    tree = ET.ElementTree(sched_xml)
    filename = "tasks/"+str(sched["ID"])+"_AutomationRequest_"+sched["Label"]+".xml"
    messages.append({"MessageFileName": filename, "SendTime_ms": sched["StartDelay"]})
    write_elementtree(sched_xml, "MessagesToSend/"+filename)

sendMessageService = {"struct_type": "service", "type": "SendMessagesService",
                       "PathToMessageFiles": "../MessagesToSend/",
                       "messages": messages}

uxas_parser.configs[0]["services"].append(sendMessageService)

config = renderer.render(None, uxas_parser.configs[0])

config_filename = "cfg_"+uxas_parser.configs[0]["Name"]+".xml"
write_elementtree(config, config_filename)

amase_xml = amase_renderer.render(None, amase_config)
scenario_filename = "Scenario_"+uxas_parser.configs[0]["Name"]+".xml"
write_elementtree(amase_xml, scenario_filename)

config_file = open("config.yaml", "w")
config_file.writelines(["amase:\n",
                        "  scenario: "+scenario_filename+"\n",
                        "\n",
                        "uxas:\n",
                        "  config: "+config_filename+"\n",
                        "  rundir: RUNDIR_"+uxas_parser.configs[0]["Name"]+"\n"])
config_file.close()
