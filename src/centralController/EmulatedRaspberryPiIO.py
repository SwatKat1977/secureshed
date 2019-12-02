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
import hashlib
import json
import jsonschema


class GPIO:

    # |============================|
    # | Pin out file json elements |
    # |============================|

    ## Pin entry: GPIO05.
    PinEntryGPIO05Element = 'GPIO05'

    ## Pin entry: GPIO06.
    PinEntryGPIO06Element = 'GPIO06'

    ## Pin entry: GPIO14.
    PinEntryGPIO14Element = 'GPIO14'

    ## Pin entry: GPIO15.
    PinEntryGPIO15Element = 'GPIO15'

    ## Pin entry: GPIO18.
    PinEntryGPIO18Element = 'GPIO18'

    ## Pin entry: GPIO23.
    PinEntryGPIO23Element = 'GPIO23'

    ## Pin entry: GPIO24.
    PinEntryGPIO24Element = 'GPIO24'

    ## Pin entry: GPIO25.
    PinEntryGPIO25Element = 'GPIO25'

    # |========================|
    # | IO pin object elements |
    # |========================|

    ## IO pin element.
    IOPinElement = 'IOPin'

    ## IO pin element : Pin state (e.g. high, low or unused).
    IOPinElement_State = 'State'

    ## IO pin state constant : High.
    IOPinStateElement_High = 'high'

    ## IO pin state constant : Low.
    IOPinStateElement_Low = 'low'

    ## IO pin state constant : Unused.
    IOPinStateElement_Unused = 'unused'

    PinOutJsonFileSchema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions":
        {
            IOPinElement:
            {
                "type": "object",
                "properties":
                {
                    IOPinElement_State:
                    {
                        "type": "string",
                        "enum":
                        [
                            IOPinStateElement_High,
                            IOPinStateElement_Low,
                            IOPinStateElement_Unused
                        ]
                    }
                },
                "required": [IOPinElement_State],
                "additionalProperties": False
            }
        },
        "type": "object",
        "properties":
        {
            PinEntryGPIO05Element: {"$ref": f"#/definitions/{IOPinElement}"},
            PinEntryGPIO06Element: {"$ref": f"#/definitions/{IOPinElement}"},
            PinEntryGPIO14Element: {"$ref": f"#/definitions/{IOPinElement}"},
            PinEntryGPIO15Element: {"$ref": f"#/definitions/{IOPinElement}"},
            PinEntryGPIO18Element: {"$ref": f"#/definitions/{IOPinElement}"},
            PinEntryGPIO23Element: {"$ref": f"#/definitions/{IOPinElement}"},
            PinEntryGPIO24Element: {"$ref": f"#/definitions/{IOPinElement}"},
            PinEntryGPIO25Element: {"$ref": f"#/definitions/{IOPinElement}"}
        },
        "additionalProperties": False
    }

    ##################################
    # -- RPi.GPIO numbering systems --
    ##################################

    ## RPi.GPIO numbering systems : BCM.
    BCM = 101

    ## RPi.GPIO numbering systems : BCM.
    BOARD = 102

    IN = 201
    OUT = 202

    ##########################
    # -- RPi.GPIO pin state --
    ##########################

    ## RPi.GPIO pin state : Low.
    LOW = 301

    ## RPi.GPIO pin state : High.
    HIGH = 302


    @staticmethod
    def cleanup():
        pass


    @staticmethod
    def setup(pin, state):
        pass


    @staticmethod
    def setmode(modeType):
        pass


    @staticmethod
    def output(pin, state):
        pass


    @staticmethod
    def HashPinoutFile(pinoutFile):

        try:
            with open(pinoutFile, 'rb') as fileHandle:
                fileContents = fileHandle.read()
                return hashlib.md5(fileContents).hexdigest()

        except IOError:
            return None


    @staticmethod
    def ReadPinoutFile(filename):
        try:
            with open(filename, 'rb') as fileHandle:
                fileContents = fileHandle.read()

        except IOError:
            return (False, 'Cannot read file')

        try:
            readJson = json.loads(fileContents)

        except json.JSONDecodeError as excpt:
            msg = f"Unable to parse '{filename}', reason: {excpt}"
            return (False, msg)

        try:
            jsonschema.validate(instance=readJson,
                                schema=GPIO.PinOutJsonFileSchema)

        except jsonschema.exceptions.ValidationError as ex:
            msg = f"Header file {filename} failed to validate against " + \
                  f"expected schema. Reason: {ex}"
            return (False, msg)

        except jsonschema.exceptions.SchemaError as ex:
            msg = f"Header file {filename} failed to validate due to " + \
                  f"schema syntax error, Traceback: {ex}"
            return (False, msg)

        return readJson
