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
from KeypadController.ConfigurationJsonSchema import CONFIGURATIONJSONSCHEMA


CentralController = collections.namedtuple('CentralController',
                                           'endpoint authKey')
GuiSettings = collections.namedtuple('GuiSettings',
                                     'fullscreen windowHeight windowWidth')
KeypadController = collections.namedtuple('KeypadController', 'authKey')

Configuration = collections.namedtuple('Configuration',
                                       'centralController gui keypadController')


class ConfigurationManager:

    # -----------------------------
    # -- Top-level json elements --
    # -----------------------------
    JSON_CentralControllerSettings = 'centralController'
    JSON_GuiSettings = 'gui'
    JSON_KeypadControllerSettings = 'keypadController'

    # ----------------------------------------------
    # -- Central controller settings sub-elements --
    # ----------------------------------------------
    JSON_CentralControllerSettings_Endpoint = 'endpoint'
    JSON_CentralControllerSettings_AuthKey = 'authorisationKey'

    # -------------------------------
    # -- GUI settings sub-elements --
    # -------------------------------
    JSON_Gui_Fullscreen = 'fullscreen'
    JSON_Gui_WindowHeight = 'windowHeight'
    JSON_Gui_WindowWidth = 'windowWidth'

    # ----------------------------------------------
    # -- Keypad controller settings sub-elements --
    # ----------------------------------------------
    JSON_KeypadController_AuthKey = 'authorisationKey'


    ## Property getter : Last error message
    @property
    def lastErrorMsg(self):
        return self.__lastErrorMsg


    #  @param self The object pointer.
    def __init__(self):
        self.__lastErrorMsg = ''


    #  @param self The object pointer.
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
        guiSection = self.__ProcessGuiSection(configJson)

        # Populate the keypad controller configuration items.
        keypadCtrlSection = configJson[self.JSON_KeypadControllerSettings]
        keypadCtrlAuthKey = keypadCtrlSection[self.JSON_KeypadController_AuthKey]
        keypadController = KeypadController(keypadCtrlAuthKey)

        return Configuration(centralController=centralController,
                             gui=guiSection, keypadController=keypadController)


    #  @param self The object pointer.
    def __ProcessCentralControllerSection(self, config):
        sctn = config[self.JSON_CentralControllerSettings]
        endpoint = sctn[self.JSON_CentralControllerSettings_Endpoint]
        authKey = sctn[self.JSON_CentralControllerSettings_AuthKey]

        return CentralController(endpoint, authKey)


    #  @param self The object pointer.
    def __ProcessGuiSection(self, config):
        sctn = config[self.JSON_GuiSettings]
        fullscreen = sctn[self.JSON_Gui_Fullscreen]
        windowHeight = sctn[self.JSON_Gui_WindowHeight]
        windowWidth = sctn[self.JSON_Gui_WindowWidth]

        return GuiSettings(fullscreen, windowHeight, windowWidth)
