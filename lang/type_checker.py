
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
        for field in schema["fields"]:
            if field["field_name"] in obj:
                val = obj[field["field_name"]]
                if field["field_type"] != "struct":
                    self.check_field_value(val, field)
                elif "anonymous_struct" in field:
                    if field["is_array"]:
                        for v in val:
                            self.check_types_against_schema(v, field["anonymous_struct"])
                    else:
                        self.check_types_against_schema(val, field["anonymous_struct"])
                else:
                    if not field["is_array"]:
                        if field["struct_type"] != val["struct_type"]:
                            print("Wrong struct type for field " + field["field_name"] + ", expected " +
                                  field["struct_type"] + ", found " + val["struct_type"])
                            continue
                        if val["type"] != "" and field["struct_type_name"] != "" and \
                            field["struct_type_name"] != val["type"]:
                            print("Wrong struct type name for field " + field["field_name"] + ", expected " +
                                  field["struct_type_name"] + ", found " + val["type"])
                            continue

                        subtype = ""
                        if "struct_type_name" in field:
                            subtype = field["struct_type_name"]
                        else:
                            subtype = val["type"]

                        subschema = self.get_schema(field["struct_type"], subtype)
                        if subschema is not None:
                            self.check_types_against_schema(val, subschema)
                    else:
                        for v in val:
                            if field["struct_type"] != v["struct_type"]:
                                print("Wrong struct type for field " + field["field_name"] + ", expected " +
                                      field["struct_type"] + ", found " + v["struct_type"])
                                continue

                            if v["type"] != "" and field["struct_type_name"] != "" and \
                                field["struct_type_name"] != v["type"]:
                                print("Wrong struct type name for field " + field["field_name"] + ", expected " +
                                      field["struct_type_name"] + ", found " + v["type"])
                                continue

                            subtype = ""
                            if field["struct_type_name"] != "":
                                subtype = field["struct_type_name"]
                            else:
                                subtype = v["type"]

                            subschema = self.get_schema(field["struct_type"], subtype)
                            if subschema is not None:
                                self.check_types_against_schema(v, subschema)
            elif field["field_required"]:
                if "type" in schema and schema["type"] is not None:
                    print("Field " + field["field_name"] + " in struct "+schema["struct_type"] +
                          " " + schema["type"] + " is required")
                else:
                    print("Field "+field["field_name"]+" in struct "+schema["struct_type"] +
                          " is required")

    def check_field_value(self, val, field):
        if field["field_type"] == "integer":
            try:
                v = int(val)
            except ValueError:
                print("Field "+field["field_name"]+" value "+val+" is not an integer")
        elif field["field_type"] == "float":
            try:
                v = float(val)
            except ValueError:
                print("Field "+field["field_name"]+" value "+val+" is not a float")
        elif field["field_type"] == "bool":
            v = val.lower()
            if v == "true" or v == "false":
                return
            else:
                print("Field "+field["field_name"]+" value "+val+" is not a bool")