
class TypeChecker:
    def __init__(self, schemas):
        self.schemas = schemas

    def get_object_schema(self, obj):
        return self.get_schema(obj["struct_type"], obj["type"])

    def get_schema(self, struct_type, struct_subtype):
        if struct_type not in self.schemas:
            return None

        s1 = self.schemas[struct_type]

        if struct_subtype in s1:
            return s1[struct_subtype]
        else:
            return s1

    def check_types(self, obj):
        schema = self.get_object_schema(obj)
        if schema is None:
            return

        self.check_types_against_schema(obj, schema)

    def check_types_against_schema(self, obj, schema):
        for param in schema["params"]:
            if param["param_name"] in obj:
                val = obj[param["param_name"]]
                if param["param_type"] != "struct":
                    self.check_param_value(val, param)
                elif "anonymous_struct" in param:
                    if param["is_array"]:
                        for v in val:
                            self.check_types_against_schema(v, param["anonymous_struct"])
                    else:
                        self.check_types_against_schema(val, param["anonymous_struct"])
                else:
                    if not param["is_array"]:
                        if param["struct_type"] != val["struct_type"]:
                            print("Wrong struct type for param " + param["param_name"] + ", expected " +
                                  param["struct_type"] + ", found " + val["struct_type"])
                            continue
                        if val["type"] != "" and param["struct_type_name"] != "" and \
                            param["struct_type_name"] != val["type"]:
                            print("Wrong struct type name for param " + param["param_name"] + ", expected " +
                                  param["struct_type_name"] + ", found " + val["type"])
                            continue

                        subtype = ""
                        if "struct_type_name" in param:
                            subtype = param["struct_type_name"]
                        else:
                            subtype = val["type"]

                        subschema = self.get_schema(param["struct_type"], subtype)
                        if subschema is not None:
                            self.check_types_against_schema(val, subschema)
                    else:
                        for v in val:
                            if param["struct_type"] != v["struct_type"]:
                                print("Wrong struct type for param " + param["param_name"] + ", expected " +
                                      param["struct_type"] + ", found " + v["struct_type"])
                                continue

                            if v["type"] != "" and param["struct_type_name"] != "" and \
                                param["struct_type_name"] != v["type"]:
                                print("Wrong struct type name for param " + param["param_name"] + ", expected " +
                                      param["struct_type_name"] + ", found " + v["type"])
                                continue

                            subtype = ""
                            if param["struct_type_name"] != "":
                                subtype = param["struct_type_name"]
                            else:
                                subtype = v["type"]

                            subschema = self.get_schema(param["struct_type"], subtype)
                            if subschema is not None:
                                self.check_types_against_schema(v, subschema)
            elif param["param_required"]:
                if "type" in schema and schema["type"] is not None:
                    print("Param " + param["param_name"] + " in struct "+schema["struct_type"] +
                          " " + schema["type"] + " is required")
                else:
                    print("Param "+param["param_name"]+" in struct "+schema["struct_type"] +
                          " is required")

    def check_param_value(self, val, param):
        if param["param_type"] == "integer":
            try:
                v = int(val)
            except ValueError:
                print("Param "+param["param_name"]+" value "+val+" is not an integer")
        elif param["param_type"] == "float":
            try:
                v = float(val)
            except ValueError:
                print("Param "+param["param_name"]+" value "+val+" is not a float")
        elif param["param_type"] == "bool":
            v = val.lower()
            if v == "true" or v == "false":
                return
            else:
                print("Param "+param["param_name"]+" value "+val+" is not a bool")
        elif param["param_type"] == "enum":
            if val not in param["param_values"]:
                print("Param "+param["param_name"]+" value "+val+" is not one of "+", ".join(param["param_values"]))

