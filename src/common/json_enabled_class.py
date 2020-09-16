'''
    EnigmaSimulator - A software implementation of the Engima Machine.
    Copyright (C) 2015-2020 Engima Simulator Development Team

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
'''
import json
import jsonschema


class JsonLoadingClass:

    ## Read a JSON file and validate it.
    #  @param self The object pointer
    #  @param filename JSON configuration filename
    #  @return Success: Rotor object, failure: None with LastErrorMessage set.
    def read_json_file(self, filename, json_schema, show_validate_error=False):

        try:
            with open(filename) as file_handle:
                file_contents = file_handle.read()

        except IOError as excpt:
            return (None, f"Unable to read file, reason: {excpt.strerror}")

        try:
            json_data = json.loads(file_contents)

        except json.JSONDecodeError as excpt:
            return (None, f"Unable to parse json, reason: {excpt.msg}")

        try:
            jsonschema.validate(instance=json_data, schema=json_schema)

        except jsonschema.exceptions.ValidationError as ex:
            msg = f", reason: {ex}" if show_validate_error is True else "."
            return (None, f"Failed to validate against schema{msg}")

        return (json_data, '')
