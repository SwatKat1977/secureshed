'''
Copyright 2019-2020 Secure Shed Project Dev Team

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
import jsonschema
from ConfigurationJsonSchema import CONFIGURATIONJSONSCHEMA

## Central controller section configuration items.
CentralController = collections.namedtuple('CentralController',
                                           'endpoint authKey')

## Keypad controller section configuration items.
KeypadController = collections.namedtuple('KeypadController',
                                          'endpoint authKey')

## The complete configuration tuple.
Configuration = collections.namedtuple('Configuration',
                                       'centralController keypadController')


## Class that encompasses management and reading of a configuration file.
class ConfigurationManager:

    # -----------------------------
    # -- Top-level json elements --
    # -----------------------------
    ## Top-level element : Central controller specific items.
    JSON_CentralControllerSettings = 'centralController'

    ## Top-level element : Keypad controller specific items.
    JSON_KeypadControllerSettings = 'keypadController'

    # ----------------------------------------------
    # -- Central controller settings sub-elements --
    # ----------------------------------------------
    ## Central controller sub-element : Endpoint for the API.
    JSON_CentralControllerSettings_Endpoint = 'endpoint'
    ## Central controller sub-element : Authentication key for API.
    JSON_CentralControllerSettings_AuthKey = 'authorisationKey'

    # ----------------------------------------------
    # -- Keypad controller settings sub-elements --
    # ----------------------------------------------
    ## Keypad controller sub-element : Endpoint for the API.
    JSON_KeypadControllerSettings_Endpoint = 'endpoint'
    ## Keypad controller sub-element : Authentication key for API.
    JSON_KeypadControllerSettings_AuthKey = 'authorisationKey'

    ## Property getter : Last error message
    @property
    def lastErrorMsg(self):
        return self.__lastErrorMsg


    ## ConfigurationManager class constructor.
    #  @param self The object pointer.
    def __init__(self):
        ## Holding member variable for last error message property.
        self.__lastErrorMsg = ''


    ## Parse a configuration file, if the parse fails then the last error
    ## message is populated and None is returned.
    #  @param self The object pointer.
    #  @param filename Name of the configuration file to parse.
    #  @return Returns an instance of Configuration if successful, otherwise
    #  None is returned and the lastErrorMsg is populated.
    def ParseConfigFile(self, filename):
        self.__lastErrorMsg = ''

        try:
            with open(filename) as fileHandle:
                fileContents = fileHandle.read()

        except IOError as excpt:
            self.__lastErrorMsg = "Unable to open configuration file '" + \
                f"{filename}', reason: {excpt.strerror}"
            return None

        try:
            configJson = json.loads(fileContents)

        except json.JSONDecodeError as excpt:
            self.__lastErrorMsg = "Unable to parse configuration file" + \
                f"{filename}, reason: {excpt}"
            return None

        try:
            jsonschema.validate(instance=configJson,
                                schema=CONFIGURATIONJSONSCHEMA)

        except jsonschema.exceptions.ValidationError as ex:
            self.__lastErrorMsg = f"Configuration file {filename} failed " + \
                "to validate against expected schema.  Please check!.  "+ \
                f"Msg: {ex}"
            return None

        centralController = self.__ProcessCentralControllerSection(configJson)
        keypadController = self.__ProcessKeypadControllerSection(configJson)
        return Configuration(centralController=centralController,
                             keypadController=keypadController)


    ## Process the Central Controller section of the configuration.
    #  @param self The object pointer.
    #  @param config Raw configuration entry.
    def __ProcessCentralControllerSection(self, config):
        sctn = config[self.JSON_CentralControllerSettings]
        endpoint = sctn[self.JSON_CentralControllerSettings_Endpoint]
        authKey = sctn[self.JSON_CentralControllerSettings_AuthKey]
        return CentralController(endpoint, authKey)


    ## Process the Keypad Controller section of the configuration.
    #  @param self The object pointer.
    #  @param config Raw configuration entry.
    def __ProcessKeypadControllerSection(self, config):
        section = config[self.JSON_KeypadControllerSettings]
        endpoint = section[self.JSON_KeypadControllerSettings_Endpoint]
        authKey = section[self.JSON_KeypadControllerSettings_AuthKey]
        return KeypadController(endpoint, authKey)
