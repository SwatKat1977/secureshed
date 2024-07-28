"""
Copyright 2019-2024 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import collections
import re
import importlib
import json
import logging
import typing
import jsonschema
from DeviceTypes.base_device_type import BaseDeviceType

class DeviceTypeManager:
    """ Class that manages device types """
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
    def device_types(self) -> typing.Dict:
        """
        Gets the list of device types.

        Returns:
            Dict: The list of device types managed by the system.
        """
        return self._device_types

    @property
    def last_error_msg(self) -> str:
        """
        Gets the last error message encountered by the system.

        Returns:
            str: The last error message encountered.
        """
        return self._last_error_msg

    def __init__(self, logger: logging.Logger):
        self._expected_types = []

        self._device_types = {}

        self._last_error_msg = ''

        self._logger = logger.getChild(__name__)

    def read_device_types_config(self, filename) -> bool:
        """
        Read and parse the device types configuration file.

        Arguments:
            filename (str): Device types JSON configuration file.

        Returns:
            Boolean representing load/parse status.
        """
        self._last_error_msg = ''

        try:
            with open(filename) as file_handle:
                file_contents = file_handle.read()

        except IOError as ex:
            self._last_error_msg = "Unable to read device types file '" + \
                f"{filename}', reason: {ex.strerror}"
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
            self._last_error_msg = "FATAL internal error, schema file invalid!"
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
            self._logger.info("Loading device name: %s",
                              device_type[self.JsonDeviceTypeElement_Name])
            self._expected_types.append(device_type_entry)

        return True

    def load_device_types(self):
        """ Load device types """

        default_module_path = 'DeviceTypes.'

        for device in self._expected_types:
            device_name = device.name

            if not device.enabled:
                self._logger.warning("Plug-in for device type '{%s}' is " +\
                                     "disabled so loading won't be attempted.",
                                     device_name)
                continue

            # The module names are in camel case so do conversion before
            # building the module name.
            device_name_camel = re.sub(r'(?<!^)(?=[A-Z])', '_',
                                       device_name).lower()
            module_name = f'{default_module_path}{device_name_camel}'

            try:
                imported_module = importlib.import_module(module_name)

            except ModuleNotFoundError:
                self._logger.warning("No plug-in for device type '%s', it " +\
                                     "has been removed from the devices list.",
                                     device_name)
                continue

            except NameError:
                self._logger.warning("Device type '%s' Plug-in has a syntax " +\
                                     "error, it has been removed from the " +\
                                     "devices list.", device_name)
                continue

            try:
                imported_cls = getattr(imported_module, device_name, self._logger)

                valid = BaseDeviceType in imported_cls.__bases__

                if not valid:
                    self._logger.warning("Plug-in for device type '%s' " +\
                                         "is not derived from plug-in " +\
                                         "class.  It cannot be used and  " +\
                                         "was removed from the devices list.",
                                         device_name)
                    continue

                self._device_types[device_name] = imported_cls
                self._logger.info("Loaded plug-in for device type '%s'",
                                  device_name)

            except AttributeError:
                pass
