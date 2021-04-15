from lang.parser import UxasParser
from lang.schema import UxasSchemaParser
from target.render import UxasXMLRenderer
import xml.etree.ElementTree as ET
import os
import datetime
import xml.dom.minidom

def write_elementtree(elem, filename):
    xmlstr = xml.dom.minidom.parseString(ET.tostring(elem)).toprettyxml()
    file = open(filename, "w")
    file.write(xmlstr)
    file.close()


uxas_parser = UxasParser()
uxas_parser.load_config_from_file("/extra/midas/openuxas-mde/example_waterway.uxas")

uxas_schema_parser = UxasSchemaParser()
uxas_schema_parser.load_schema_from_file("/extra/midas/openuxas-mde/network_schema.uxsch")
uxas_schema_parser.load_schema_from_file("/extra/midas/openuxas-mde/standard_services_schema.uxsch")
uxas_schema_parser.load_schema_from_file("/extra/midas/openuxas-mde/uxas_configuration_schema.uxsch")
uxas_schema_parser.load_schema_from_file("/extra/midas/openuxas-mde/standard_vehicles_schema.uxsch")
uxas_schema_parser.load_schema_from_file("/extra/midas/openuxas-mde/standard_plans_schema.uxsch")

uxas_plan_parser = UxasParser()
uxas_plan_parser.load_config_from_file("/extra/midas/openuxas-mde/waterway_plan.uxas")

renderer = UxasXMLRenderer(uxas_schema_parser.schemas)

amase_schema_parser = UxasSchemaParser()
amase_schema_parser.load_schema_from_file("/extra/midas/openuxas-mde/amase_schema.uxsch")

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
