import openuxas_mde.lang.parser
from openuxas_mde.lang import config_checker
from openuxas_mde.lang.parser import UxasParser
from openuxas_mde.lang.schema import UxasSchemaParser
from openuxas_mde.lang.type_checker import TypeChecker
from openuxas_mde.target.render import (UxasXMLRenderer, Environment)
import xml.etree.ElementTree as ET
import os
import xml.dom.minidom
import argparse
import pkg_resources

exclude_schemas_from_load = {
    "network_schema.uxsch",
    "standard_services_schema.uxsch",
    "uxas_configuration_schema.uxsch",
    "standard_vehicles_schema.uxsch",
    "standard_plans_schema.uxsch",
    "external_services.uxsch",
    "amase_schema.uxsch"
}

def load_uxas_schemas(lib_path):
    uxas_schema_parser = UxasSchemaParser(lib_path)

    uxas_schema_parser.load_schema_from_file("network_schema.uxsch")
    uxas_schema_parser.load_schema_from_file("standard_services_schema.uxsch")
    uxas_schema_parser.load_schema_from_file("uxas_configuration_schema.uxsch")
    uxas_schema_parser.load_schema_from_file("standard_vehicles_schema.uxsch")
    uxas_schema_parser.load_schema_from_file("standard_plans_schema.uxsch")

    for lib_part in lib_path:
        files = os.listdir(lib_part)
        for file in files:
            if file.endswith(".uxsch") and file not in exclude_schemas_from_load:
                uxas_schema_parser.load_schema_from_file(file)

    return uxas_schema_parser

def load_external_services_schemas(lib_path):
    uxas_schema_parser = UxasSchemaParser(lib_path)
    uxas_schema_parser.load_schema_from_file("external_services.uxsch")

    return uxas_schema_parser

def load_amase_schemas(lib_path):
    amase_schema_parser = UxasSchemaParser(lib_path)

    amase_schema_parser.load_schema_from_file("amase_schema.uxsch")
    return amase_schema_parser


def write_elementtree(elem, filename):
    xmlstr = xml.dom.minidom.parseString(ET.tostring(elem)).toprettyxml()
    file = open(filename, "w")
    file.write(xmlstr)
    file.close()


def main():
    system_lib_path = pkg_resources.resource_filename("openuxas_mde", "lib")

    default_output_dir = os.curdir
    if os.environ.get("UXAS_EXAMPLES_DIR") is not None:
        default_output_dir = os.environ.get("UXAS_EXAMPLES_DIR")
    elif os.path.exists(os.path.join(os.path.expanduser("~"), "OpenUxAS", "examples")):
        default_output_dir = os.path.join(os.path.expanduser("~"), "OpenUxAS", "examples")

    arg_parser = argparse.ArgumentParser(description="Generate UxAS Configuration")
    arg_parser.add_argument('-libpath', nargs=1, default=[""])
    arg_parser.add_argument('-o', nargs=1, default=[default_output_dir])
    arg_parser.add_argument('-exclude_sent', nargs=1, default=[""])
    arg_parser.add_argument('-exclude_received', nargs=1, default=[""])

    parsed_args, rest_args = arg_parser.parse_known_args()
    parsed_args = vars(parsed_args)

    output_dir = parsed_args["o"][0]
    exclude_sent_file = parsed_args["exclude_sent"][0]
    exclude_received_file = parsed_args["exclude_received"][0]

    lib_path_args = []
    if "libpath" in parsed_args:
        if isinstance(parsed_args["libpath"], list):
            lib_path_args = parsed_args["libpath"][0].split(os.pathsep)
        else:
            lib_path_args = parsed_args["libpath"].split(os.pathsep)

    lib_path = lib_path_args + [system_lib_path]

    uxas_schema_parser = load_uxas_schemas(lib_path)
    external_services_schema = load_external_services_schemas(lib_path)

    uxas_parser = UxasParser(lib_path)
    if len(rest_args) > 0:
        try:
            uxas_parser.load_config_from_file(rest_args[0])
        except openuxas_mde.lang.parser.ParseError:
            return

    if len(uxas_parser.configs) == 0:
        print("No .uxas files in command-line, nothing to generate")
        return

    type_checker = TypeChecker(uxas_schema_parser.schemas)
    type_checker.check_types(uxas_parser.configs[0])

    uxas_plan_parser = UxasParser(lib_path)
    if len(rest_args) > 1:
        try:
            uxas_plan_parser.load_config_from_file(rest_args[1])
        except openuxas_mde.lang.parser.ParseError:
            return

    excludes = { "sent": [], "received": []}
    if exclude_sent_file != "":
        send_file = open(exclude_sent_file, 'r')
        for line in send_file:
            excludes["sent"].append(line.strip())
        send_file.close()

    if exclude_received_file != "":
        receive_file = open(exclude_received_file, 'r')
        for line in receive_file:
            excludes["received"].append(line.strip())
        receive_file.close()

    config_checker.check_message_send_receive(uxas_parser.configs[0], uxas_schema_parser.schemas,
                                              external_services_schema.schemas,
                                              excludes)

    renderer = UxasXMLRenderer(uxas_schema_parser.schemas)

    amase_schema_parser = load_amase_schemas(lib_path)

    amase_renderer = UxasXMLRenderer(amase_schema_parser.schemas)

    messages = []
    output_dir = os.path.join(output_dir, uxas_parser.configs[0]["Name"])
    os.makedirs(os.path.join(output_dir, "MessagesToSend", "tasks"), 0o777, exist_ok=True)

    scen_veh_list = []
    scen_veh_state_list = []

    for vehicle_id in uxas_plan_parser.configs[0]["Entities"]:
        if isinstance(vehicle_id, dict) and "category" in vehicle_id:
            category = uxas_parser.configs[0][vehicle_id["category"]]
            item = None
            for c in category:
                if c["type"] == vehicle_id["name"]:
                    item = c
                    break
            if item is not None:
                for param in vehicle_id["param_list"]:
                    item = item[param]
                vehicle_id = item

        for vehicle in uxas_parser.configs[0]["vehicles"]:
            if vehicle["ID"] != vehicle_id:
                continue

            vehicle_xml = renderer.render(None, vehicle)
            tree = ET.ElementTree(vehicle_xml)
            filename = "AirVehicleConfiguration_V"+str(vehicle_id)+".xml"
            messages.append({"MessageFileName": filename, "SendTime_ms": 200})
            write_elementtree(vehicle_xml, os.path.join(output_dir, "MessagesToSend", filename))
            scen_veh_list.append(vehicle)

            vehicle_state_xml = renderer.render(None, vehicle["state"])
            tree = ET.ElementTree(vehicle_state_xml)
            filename = "AirVehicleState_V"+str(vehicle_id)+".xml"
            messages.append({"MessageFileName": filename, "SendTime_ms": 250})
            write_elementtree(vehicle_state_xml, os.path.join(output_dir, "MessagesToSend", filename))
            scen_veh_state_list.append(vehicle["state"])

    amase_config = {
        "struct_type": "amase",
        "type": "",
        "ScenarioData": uxas_plan_parser.configs[0]["ScenarioData"],
        "ScenarioEventList": scen_veh_list + scen_veh_state_list + uxas_plan_parser.configs[0]["MissionCommands"]
    }

    for task in uxas_plan_parser.configs[0]["Tasks"]:
        task_xml = renderer.render_with_env(None, task, Environment(uxas_parser.configs[0]))
        tree = ET.ElementTree(task_xml)
        filename = "tasks/"+str(task["TaskID"])+"_"+task["Label"]+".xml"
        messages.append({"MessageFileName": filename, "SendTime_ms": 300})
        write_elementtree(task_xml, os.path.join(output_dir, "MessagesToSend", filename))

    for sched in uxas_plan_parser.configs[0]["Schedule"]:
        sched_xml = renderer.render_with_env(None, sched, Environment(uxas_parser.configs[0]))
        tree = ET.ElementTree(sched_xml)
        filename = "tasks/"+str(sched["ID"])+"_AutomationRequest_"+sched["Label"]+".xml"
        messages.append({"struct_type": "message", "type": "SendMessagesServiceMessage",
                         "MessageFileName": filename, "SendTime_ms": sched["StartDelay"]})
        write_elementtree(sched_xml, os.path.join(output_dir, "MessagesToSend", filename))

    sendMessageService = {"struct_type": "service", "type": "SendMessagesService",
                           "PathToMessageFiles": "../MessagesToSend/",
                           "messages": messages}

    uxas_parser.configs[0]["services"].append(sendMessageService)

    config = renderer.render(None, uxas_parser.configs[0])

    config_filename = "cfg_"+uxas_parser.configs[0]["Name"]+".xml"
    write_elementtree(config, os.path.join(output_dir, config_filename))

    amase_xml = amase_renderer.render_with_env(None, amase_config, Environment(uxas_parser.configs[0]))
    scenario_filename = "Scenario_"+uxas_parser.configs[0]["Name"]+".xml"
    write_elementtree(amase_xml, os.path.join(output_dir, scenario_filename))

    config_file = open(os.path.join(output_dir, "config.yaml"), "w")
    config_file.writelines(["amase:\n",
                            "  scenario: "+scenario_filename+"\n",
                            "\n",
                            "uxas:\n",
                            "  config: "+config_filename+"\n",
                            "  rundir: RUNDIR_"+uxas_parser.configs[0]["Name"]+"\n"])
    config_file.close()

if __name__ == '__main__':
    main()