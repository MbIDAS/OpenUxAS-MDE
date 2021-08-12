import argparse
import datetime
import os
import re

import pkg_resources
from jinja2 import Environment, PackageLoader, select_autoescape

import openuxas_mde
from openuxas_mde.lang.schema import UxasSchemaParser

def camel_case_to_upper_case(s):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s1.upper()

def type_name_to_cpp_type(type_name):
    if type_name == "integer":
        return "int"
    elif type_name == "string":
        return "std::string"
    return type_name

def uncap(s):
    return s[:1].lower()+s[1:]

def make_receives_structure(receives):
    parts = receives.split(".")
    recv = "::".join(parts)
    test_name = "is"+parts[-1]
    test = "::".join(parts[:-1] + [test_name])
    prefix_name = uncap(parts[-1])
    header_name = "/".join(parts)
    return {"message": recv, "test": test, "prefix": prefix_name, "name": parts[-1], "header_name": header_name }

def parse_existing(filename, preserved, generate):
    if os.path.exists(filename):
        file = open(filename, "r")
        preserving = False
        preserve_name = ""
        preserve_lines = []

        for line in file:
            if line.startswith("///BEGIN_PRESERVE_"):
                new_preserve_name = line.strip()[len("///BEGIN_PRESERVE_"):]
                if preserving:
                    print("Error parsing preserve comments, was already parsing BEGIN_PRESERVE_"+preserve_name+
                          ", encountered BEGIN_PRESERVE_"+new_preserve_name)
                    file.close()
                    return False
                preserving = True
                preserve_name = new_preserve_name
                preserve_lines = []
            elif line.startswith("///END_PRESERVE_"):
                new_preserve_name = line.strip()[len("///END_PRESERVE_"):]
                if not preserving:
                    print("Error parsing preserve comments, encountered END_PRESERVE_"+new_preserve_name+
                          " but there was no corresponding BEGIN_PRESERVE_"+new_preserve_name)
                    file.close()
                    return False
                preserved[preserve_name] = "".join(preserve_lines).strip()
                preserving = False
                preserve_name = ""
                preserve_lines = []
            elif line.startswith("///OVERRIDE_"):
                override_name = line.strip()[len("///OVERRIDE_"):]
                generate[override_name] = False
            else:
                preserve_lines.append(line)
        file.close()
    return True

def main():
    system_lib_path = pkg_resources.resource_filename("openuxas_mde", "lib")

    default_output_dir = os.curdir
    if os.environ.get("UXAS_CPP_DIR") is not None:
        default_output_dir = os.path.join(os.environ.get("UXAS_CPP_DIR"), "Services")
    elif os.path.exists(os.path.join(os.path.expanduser("~"), "OpenUxAS", "examples")):
        default_output_dir = os.path.join(os.path.expanduser("~"), "OpenUxAS", "examples")

    arg_parser = argparse.ArgumentParser(description="Generate UxAS Configuration")
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

    uxas_schema_parser = UxasSchemaParser(lib_path)

    if len(rest_args) > 0:
        try:
            uxas_schema_parser.load_schema_from_file(rest_args[0])
        except openuxas_mde.lang.parser.ParseError:
            return
    else:
        print("No .uxsch files in command-line, nothing to generate")
        return

    env = Environment(
        loader=PackageLoader("openuxas_mde"),
        autoescape=select_autoescape()
    )
    h_template = env.get_template("ServiceTemplate.h.jinja")
    cpp_template = env.get_template("ServiceTemplate.cpp.jinja")

    for _, service in uxas_schema_parser.schemas["service"].items():
        if service["struct_type"] != "service":
            continue
        for param in service["params"]:
            param["paramName"] = type_name_to_cpp_type(param["param_name"])
            param["paramType"] = type_name_to_cpp_type(param["param_type"])
            pt = param["param_type"]
            if pt == "integer":
                param["paramValueExtractor"] = "as_int"
            else:
                param["paramValueExtractor"] = "value"
            param["paramNameAllCaps"] = camel_case_to_upper_case(param["param_name"])
        service_data = {}
        service_data["serviceName"] = service["type"]
        service_data["serviceNameAllCaps"] = camel_case_to_upper_case(service_data["serviceName"])
        service_data["configParams"] = service["params"]
        service_data["receives"] = [make_receives_structure(r) for r in service["messages"]["receives"]]
        service_data["sends"] = [s.replace(".", "::") for s in service["messages"]["sends"]]
        service_data["creationDate"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        section_names = [
            "CPP_DECLS",
            "CONSTRUCTOR",
            "DESTRUCTOR",
            "CONFIGURE",
            "INITIALIZE",
            "START",
            "TERMINATE",
            "RECEIVE",
            "ADDITIONAL",
            "INCLUDES",
            "PUBLIC",
            "PRIVATE"]

        for r in service_data["receives"]:
            section_names.append("RECEIVE_"+r["name"])

        preserved = {}
        generate = {}
        for sn in section_names:
            preserved[sn] = ""
            generate[sn] = True

        if not parse_existing(os.path.join(output_dir, service_data["serviceName"]+".h"), preserved, generate):
            return
        if not parse_existing(os.path.join(output_dir, service_data["serviceName"]+".cpp"), preserved, generate):
            return

        service_data["preserved"] = preserved
        service_data["generate"] = generate

        file = open(os.path.join(output_dir, service_data["serviceName"]+".h"), "w")
        file.write(h_template.render(service_data))
        file.close()
        print(h_template.render(service_data))

        file = open(os.path.join(output_dir, service_data["serviceName"]+".cpp"), "w")
        file.write(cpp_template.render(service_data))
        file.close()
        print(cpp_template.render(service_data))

if __name__ == '__main__':
    main()
