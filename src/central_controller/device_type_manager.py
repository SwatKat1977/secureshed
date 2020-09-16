'''
Copyright 2019 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import collections
import re
import json
import importlib
import jsonschema
from central_controller.DeviceTypes.base_device_type import BaseDeviceType
from common.Logger import LogType


class DeviceTypeManager:
    # pylint: disable=R0903
    __slots__ = ['_device_types', '_expected_types', '_logger',
                 '_last_error_msg']

    DeviceTypeCfg = collections.namedtuple('DeviceTypeCfg', 'name enabled')

    # Json devices array element.
    JsonDeviceTypesArray = 'deviceTypes'

    # Json top element : Device type.
    JsonTopElement_DeviceType = 'deviceType'

    JsonDeviceTypeElement_Name = 'name'
    JsonDeviceTypeElement_Enabled = 'enabled'

    ## Device types configuration file's Json schema.
    JsonSchema = \
    {
        "$schema": "http://json-schema.org/draft-07/schema#",

        "definitions":
        {
            JsonTopElement_DeviceType:
            {
                "type" : "object",
                "properties":
                {
                    JsonDeviceTypeElement_Name:
                    {
                        "type": "string"
                    },
                    JsonDeviceTypeElement_Enabled:
                    {
                        "type": "boolean"
                    }
                },
                "additionalProperties": False,
                "required":
                [
                    JsonDeviceTypeElement_Name,
                    JsonDeviceTypeElement_Enabled
                ]
            }
        },
        "type" : "object",
        "properties":
        {
            JsonDeviceTypesArray:
            {
                "type": "array",
                "items": {"$ref": f"#/definitions/{JsonTopElement_DeviceType}"}
            }
        },
        "required" : [JsonDeviceTypesArray],
        "additionalProperties" : False
    }

    @property
    def device_types(self):
        return self._device_types

    @property
    def last_error_msg(self):
        return self._last_error_msg


    #  @param self The object pointer.
    def __init__(self, logger):
        self._expected_types = []

        self._device_types = {}

        self._last_error_msg = ''

        self._logger = logger


    #  @param self The object pointer.
    def read_device_types_config(self, filename):
        self._last_error_msg = ''

        try:
            with open(filename) as file_handle:
                file_contents = file_handle.read()

        except IOError as excpt:
            self._last_error_msg = "Unable to read device types file '" + \
                f"{filename}', reason: {excpt.strerror}"
            return False

        try:
            config_json = json.loads(file_contents)

        except json.JSONDecodeError as excpt:
            self._last_error_msg = "Unable to parse device types file" + \
                f"{filename}, reason: {excpt}"
            return False

        try:
            jsonschema.validate(instance=config_json,
                                schema=self.JsonSchema)

        except jsonschema.exceptions.SchemaError:
            self._last_error_msg = f"FATAL internal error, schema file invalid!"
            return False

        except jsonschema.exceptions.ValidationError as ex:
            self._last_error_msg = "Schema validation failed for devices " + \
                f"file '{filename} failed. " + ex.message
            return False

        # Populate the device types from the configuration file.
        for device_type in config_json[self.JsonDeviceTypesArray]:
            device_type_entry = self.DeviceTypeCfg(
                name=device_type[self.JsonDeviceTypeElement_Name],
                enabled=device_type[self.JsonDeviceTypeElement_Enabled])
            self._logger.Log(LogType.Info,
                             f"Loading device name: {device_type[self.JsonDeviceTypeElement_Name]}")
            self._expected_types.append(device_type_entry)

        return True


    #  @param self The object pointer.
    def load_device_types(self):
        default_module_path = 'central_controller.DeviceTypes.'

        for device in self._expected_types:
            device_name = device.name

            if not device.enabled:
                msg = f"Plug-in for device type '{device_name}' is disabled" +\
                       " so loading won't be attempted."
                self._logger.Log(LogType.Warn, msg)
                continue

            # The module names are in camel case so do conversion before
            # building the module name.
            device_name_camel = re.sub(r'(?<!^)(?=[A-Z])', '_',
                                       device_name).lower()
            module_name = f'{default_module_path}{device_name_camel}'

            try:
                imported_module = importlib.import_module(module_name)

            except ModuleNotFoundError:
                self._logger.Log(LogType.Warn,
                                 f"No plug-in for device type '{device_name}'," +\
                                 " it has been removed from the devices list.")
                continue

            except NameError:
                self._logger.Log(LogType.Warn,
                                 f"Device type '{device_name}' Plug-in has a " +\
                                 "syntax error, it has been removed from the devices list.")
                continue

            try:
                imported_cls = getattr(imported_module, device_name, self._logger)

                valid = BaseDeviceType in imported_cls.__bases__

                if not valid:
                    self._logger.Log(LogType.Warn,
                                     f"Plug-in for device type '{device_name}'" +\
                                     " is not derived from plug-in class.  It cannot be " +\
                                     "used and was removed from the devices list.")
                    continue

                self._device_types[device_name] = imported_cls
                self._logger.Log(LogType.Info,
                                 f"Loaded plug-in for device type '{device_name}'")

            except AttributeError:
                pass
