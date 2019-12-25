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
import enum
import hashlib
import json
import jsonschema


## Simulation of the Raspberry GPIO package.
class GPIO:

    ## Enumerated of the state of a pin.
    class PinState(enum.Enum):
        ## Pin is in low state.
        Low = 0

        ## Pin is in high state.
        High = 1

    # |============================|
    # | Pin out file json elements |
    # |============================|

    ## Pin entry Prefix.
    PinEntryGPIOPrefix = 'GPIO'

    ## Pin entry: GPIO05.
    PinEntryGPIO05Element = f'{PinEntryGPIOPrefix}05'

    ## Pin entry: GPIO06.
    PinEntryGPIO06Element = f'{PinEntryGPIOPrefix}06'

    ## Pin entry: GPIO14.
    PinEntryGPIO14Element = f'{PinEntryGPIOPrefix}14'

    ## Pin entry: GPIO15.
    PinEntryGPIO15Element = f'{PinEntryGPIOPrefix}15'

    ## Pin entry: GPIO18.
    PinEntryGPIO18Element = f'{PinEntryGPIOPrefix}18'

    ## Pin entry: GPIO23.
    PinEntryGPIO23Element = f'{PinEntryGPIOPrefix}23'

    ## Pin entry: GPIO24.
    PinEntryGPIO24Element = f'{PinEntryGPIOPrefix}24'

    ## Pin entry: GPIO25.
    PinEntryGPIO25Element = f'{PinEntryGPIOPrefix}25'

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

    ## Definition of the pinout json file's schema to validate against.
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
                            IOPinStateElement_Low
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
        "required":
        [
            PinEntryGPIO05Element,
            PinEntryGPIO06Element,
            PinEntryGPIO14Element,
            PinEntryGPIO15Element,
            PinEntryGPIO18Element,
            PinEntryGPIO23Element,
            PinEntryGPIO24Element,
            PinEntryGPIO25Element
        ],
        "additionalProperties": False
    }

    ## The current simulated state of the IO pins.
    CurrentPinOutStates = {
        PinEntryGPIO05Element : PinState.High,
        PinEntryGPIO06Element : PinState.High,
        PinEntryGPIO14Element : PinState.High,
        PinEntryGPIO15Element : PinState.High,
        PinEntryGPIO18Element : PinState.High,
        PinEntryGPIO23Element : PinState.High,
        PinEntryGPIO24Element : PinState.High,
        PinEntryGPIO25Element : PinState.High
    }

    ## Last MD5 for the pinout file.
    PinOutFileHash = None

    ## File and location of the pin out file.
    PinOutFile = 'centralController/pinOutFile.json'


    ##################################
    # -- RPi.GPIO numbering systems --
    ##################################

    ## RPi.GPIO numbering systems : Broadcom SOC channel.
    BCM = 101

    ## RPi.GPIO numbering systems : Board numbers.
    BOARD = 102

    #########################
    # -- RPi.GPIO pin mode --
    #########################

    ## RPi.GPIO pin mode : Input (e.g. senors).
    IN = 201

    ## RPi.GPIO pin mode : Output (e.g. relay).
    OUT = 202

    ##########################
    # -- RPi.GPIO pin state --
    ##########################

    ## RPi.GPIO pin state : Low.
    LOW = 0

    ## RPi.GPIO pin state : High.
    HIGH = 1


    PUD_UP = 401


    ## Simulated version of the Raspberry Pi GPIO cleanup() function for
    #  testing purposes.
    #  Note: This method is currently empty as nothing needs simualting.
    @staticmethod
    def cleanup():
        # pylint: disable=C0103
        pass


    ## Simulated version of the Raspberry Pi GPIO setup() function for
    #  testing purposes.
    #  Note: This method is currently empty as nothing needs simualting.
    @staticmethod
    def setup(pin, state, pull_up_down=None):
        # pylint: disable=C0103
        pass


    ## Simulated version of the Raspberry Pi GPIO setmode() function for
    #  testing purposes.
    #  Note: This method is currently empty as nothing needs simualting.
    @staticmethod
    def setmode(modeType):
        # pylint: disable=C0103
        pass


    ## Simulation of the Raspberry Pi GPIO input() function for testing
    #  purposes.
    #  @param pin Pin to check the state of.
    @staticmethod
    def input(pin):
        # pylint: disable=C0103
        pinId = f'{GPIO.PinEntryGPIOPrefix}{pin}'
        return GPIO.CurrentPinOutStates[pinId].value


    ## Simulation of the Raspberry Pi GPIO output() function for testing
    #  purposes.
    @staticmethod
    def output(pin, state):
        # pylint: disable=C0103

        pinId = f'{GPIO.PinEntryGPIOPrefix}{pin}'
        newValue = GPIO.PinState.High if state == 1 else GPIO.PinState.Low
        GPIO.CurrentPinOutStates[pinId] = newValue


    ## Generate a MD5 hash of the pinout state file, this is to allow the file
    #  to be checked to see if has changed between last checks.
    #  of the Raspberry Pi GPIO output() function for testing
    #  @returns MD5 hash if the file was hashed correctly, otherwise None.
    @staticmethod
    def HashPinoutFile(pinoutFile):
        try:
            with open(pinoutFile, 'rb') as fileHandle:
                fileContents = fileHandle.read()
                return hashlib.md5(fileContents).hexdigest()

        except IOError:
            return None


    ## Read the json contents of the simulated pinout file and return it along
    #  with an error status (if there is one).
    # @returns Returns a tuple of (status, pinoutFileContents), If the read was
    # successful status is an empty string and file contents is the contents of
    # the pinout file in json format.  If read fails then the status is a
    # human-readable string with the error status and file contents is None.
    @staticmethod
    def ReadPinoutFile():
        try:
            with open(GPIO.PinOutFile, 'rb') as fileHandle:
                fileContents = fileHandle.read()

        except IOError:
            return ('Cannot read file', None)

        try:
            readJson = json.loads(fileContents)

        except json.JSONDecodeError as excpt:
            return (f"Unable to parse pinout file, reason: {excpt}",
                    None)

        try:
            jsonschema.validate(instance=readJson,
                                schema=GPIO.PinOutJsonFileSchema)

        except jsonschema.exceptions.ValidationError as ex:
            return (f"File Schema validation failed, Reason: {ex}", None)

        except jsonschema.exceptions.SchemaError as ex:
            return (f"Internal schema syntax error, Traceback: {ex}", None)

        return ('', readJson)


    ## Update the simulated states of the Raspberry Pi GPIO pins only if the
    #  MD5 hash of the file has changed.
    #  @param logger Instance of the logger object.
    @staticmethod
    def UpdateFromPinOutFile(logger):
        newHash = GPIO.HashPinoutFile(GPIO.PinOutFile)
        if newHash is None or newHash == GPIO.PinOutFileHash:
            return

        GPIO.PinOutFileHash = newHash

        newPinOutStates = {}

        status, pinouts = GPIO.ReadPinoutFile()
        if status or not pinouts:
            logger.info(f'Unable to read pin file, reason: {status}')
            return

        for key in pinouts:
            pinState = pinouts[key][GPIO.IOPinElement_State]
            newPinOutStates[key] = GPIO.PinState.High \
                if pinState == GPIO.IOPinStateElement_High \
                else GPIO.PinState.Low

        GPIO.CurrentPinOutStates = newPinOutStates
        logger.debug(f'Emulated Pin states : {GPIO.CurrentPinOutStates}')
