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
import json
import importlib
import jsonschema
from CentralController.DeviceTypes.BaseDeviceType import BaseDeviceType


class DeviceTypeManager:
    # pylint: disable=R0903
    __slots__ = ['__deviceTypes', '__expectedTypes', '__lastErrorMsg',
                 '__logger']

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
    def deviceTypes(self):
        return self.__deviceTypes

    @property
    def lastErrorMsg(self):
        return self.__lastErrorMsg


    #  @param self The object pointer.
    def __init__(self, logger):
        self.__logger = logger

        self.__expectedTypes = []

        self.__deviceTypes = {}

        self.__lastErrorMsg = ''


    #  @param self The object pointer.
    def ReadDeviceTypesConfig(self, filename):
        self.__lastErrorMsg = ''

        try:
            with open(filename) as fileHandle:
                fileContents = fileHandle.read()

        except IOError as excpt:
            self.__lastErrorMsg = "Unable to read device types file '" + \
                f"{filename}', reason: {excpt.strerror}"
            return False

        try:
            configJson = json.loads(fileContents)

        except json.JSONDecodeError as excpt:
            self.__lastErrorMsg = "Unable to parse device types file" + \
                f"{filename}, reason: {excpt}"
            return False

        try:
            jsonschema.validate(instance=configJson,
                                schema=self.JsonSchema)

        except jsonschema.exceptions.SchemaError:
            self.__lastErrorMsg = f"FATAL internal error, schema file invalid!"
            return False

        except jsonschema.exceptions.ValidationError as ex:
            self.__lastErrorMsg = "Schema validation failed for devices " + \
                f"file '{filename} failed. " + ex.message
            return False

        # Populate the device types from the configuration file.
        for deviceType in configJson[self.JsonDeviceTypesArray]:
            deviceTypeEntry = self.DeviceTypeCfg(
                name=deviceType[self.JsonDeviceTypeElement_Name],
                enabled=deviceType[self.JsonDeviceTypeElement_Enabled])
            self.__expectedTypes.append(deviceTypeEntry)

        return True


    #  @param self The object pointer.
    def LoadDeviceTypes(self):
        defaultModulePath = 'centralController.DeviceTypes.'

        for device in self.__expectedTypes:
            deviceName = device.name

            if not device.enabled:
                msg = f"Plug-in for device type '{deviceName}' is disabled" +\
                       " so loading won't be attempted."
                self.__logger.warn(msg)
                continue

            moduleName = f'{defaultModulePath}{deviceName}'

            try:
                importedModule = importlib.import_module(moduleName)

            except ModuleNotFoundError:
                self.__logger.warn(f"No plug-in for device type '{deviceName}'," +\
                    " it has been removed from the devices list.")
                continue

            except NameError:
                self.__logger.warn(f"Device type '{deviceName}' Plug-in has a " +\
                    "syntax error, it has been removed from the devices list.")
                continue

            try:
                importedCls = getattr(importedModule, deviceName)

                valid = BaseDeviceType in importedCls.__bases__

                if not valid:
                    self.__logger.warn(f"Plug-in for device type '{deviceName}'" +\
                        " is not derived from plug-in class.  It cannot be " +\
                         "used and was removed from the devices list.")
                    continue

                self.__deviceTypes[deviceName] = importedCls
                self.__logger.info(f"Loaded plug-in for device type '{deviceName}'")

            except AttributeError:
                pass
