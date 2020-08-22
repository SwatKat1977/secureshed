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
# pylint: disable=R0903
import json
import jsonschema
from CentralController.EmulatedRaspberryPiIO import GPIO


class DevicesConfigLoader:

    class JsonTopElement:
        Device = 'device'
        Devices = 'devices'

    class DeviceElement:
        Hardware = 'hardware'
        DeviceType = 'deviceType'
        Name = 'name'
        Pins = 'pins'
        Enabled = 'enabled'
        TriggerGracePeriodSecs = 'triggerGracePeriodSecs'

    class DevicePinsElement:
        IoPin = 'ioPin'
        Identifier = 'identifier'

    class DeviceHardwareType:
        Sensor = 'sensor'
        Siren = 'siren'

    ## Configuration file's Json schema.
    JsonSchema = \
    {
        "$schema": "http://json-schema.org/draft-07/schema#",

        "definitions":
        {
            DeviceElement.Pins:
            {
                "type" : "object",
                "properties":
                {
                    DevicePinsElement.IoPin:
                    {
                        "type": "string",
                        "enum":
                        [
                            GPIO.PinEntryGPIO05Element,
                            GPIO.PinEntryGPIO06Element,
                            GPIO.PinEntryGPIO14Element,
                            GPIO.PinEntryGPIO15Element,
                            GPIO.PinEntryGPIO18Element,
                            GPIO.PinEntryGPIO23Element,
                            GPIO.PinEntryGPIO24Element,
                            GPIO.PinEntryGPIO25Element
                        ]
                    },
                    DevicePinsElement.Identifier:
                    {
                        "type": "string"
                    }
                },
                "additionalProperties": False,
                "required":
                [
                    DevicePinsElement.IoPin,
                    DevicePinsElement.Identifier
                ]
            },
            JsonTopElement.Device:
            {
                "type" : "object",
                "properties":
                {
                    DeviceElement.DeviceType:
                    {
                        "type": "string"
                    },
                    DeviceElement.Hardware:
                    {
                        "type": "string",
                        "enum":
                        [
                            DeviceHardwareType.Sensor,
                            DeviceHardwareType.Siren
                        ]
                    },
                    DeviceElement.Name:
                    {
                        "type": "string"
                    },
                    DeviceElement.Enabled:
                    {
                        "type": "boolean"
                    },
                    DeviceElement.Pins:
                    {
                        "type": "array",
                        "items": {"$ref": f"#/definitions/{DeviceElement.Pins}"}
                    },
                    DeviceElement.TriggerGracePeriodSecs:
                    {
                        "type": "integer",
                        "minimum": 1
                    }
                },
                "additionalProperties": False,
                "required":
                [
                    DeviceElement.DeviceType,
                    DeviceElement.Hardware,
                    DeviceElement.Name,
                    DeviceElement.Enabled,
                    DeviceElement.Pins
                ]
            }
        },
        "type" : "object",
        "properties":
        {
            JsonTopElement.Devices:
            {
                "type": "array",
                "items": {"$ref": f"#/definitions/{JsonTopElement.Device}"}
            }
        },
        "required" : [JsonTopElement.Devices],
        "additionalProperties" : False
    }

    ## Property getter : Last error message
    @property
    def lastErrorMsg(self):
        return self.__lastErrorMsg


    def __init__(self):
        self.__lastErrorMsg = ''


    def ReadDevicesConfigFile(self, filename):

        self.__lastErrorMsg = ''

        try:
            with open(filename) as fileHandle:
                fileContents = fileHandle.read()

        except IOError as excpt:
            self.__lastErrorMsg = "Unable to read devices file '" + \
                f"{filename}', reason: {excpt.strerror}"
            return None

        try:
            configJson = json.loads(fileContents)

        except json.JSONDecodeError as excpt:
            self.__lastErrorMsg = "Unable to parse devices file" + \
                f"{filename}, reason: {excpt}"
            return None

        try:
            jsonschema.validate(instance=configJson,
                                schema=self.JsonSchema)

        except jsonschema.exceptions.SchemaError:
            self.__lastErrorMsg = f"FATAL internal error, schema file invalid!"
            return None

        except jsonschema.exceptions.ValidationError:
            self.__lastErrorMsg = "Schema validation failed for devices " + \
                f"file '{filename} failed."
            return None

        return configJson
