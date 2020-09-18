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
from configuration_json_schema import CONFIGURATIONJSONSCHEMA

## Central controller section configuration items.
CentralController = collections.namedtuple('CentralController',
                                           'endpoint authKey')

## GUI section configuration items.
GuiSettings = collections.namedtuple('GuiSettings',
                                     'fullscreen windowHeight windowWidth')

## Keypad controller section configuration items.
KeypadController = collections.namedtuple('KeypadController', 'authKey networkPort')

## The complete configuration tuple.
Configuration = collections.namedtuple('Configuration',
                                       'centralController gui keypadController')


## Class that encompasses management and reading of a configuration file.
class ConfigurationManager:

    # -----------------------------
    # -- Top-level json elements --
    # -----------------------------
    ## Top-level element : Central controller specific items.
    JSON_CentralControllerSettings = 'centralController'

    ## Top-level element : GUI specific items.
    JSON_GuiSettings = 'gui'

    ## Top-level element : Keypad controller specific items.
    JSON_KeypadControllerSettings = 'keypadController'

    # ----------------------------------------------
    # -- Central controller settings sub-elements --
    # ----------------------------------------------
    ## Central controller sub-element : Endpoint for the API.
    JSON_CentralControllerSettings_Endpoint = 'endpoint'
    ## Central controller sub-element : Authentication key for API.
    JSON_CentralControllerSettings_AuthKey = 'authorisationKey'

    # -------------------------------
    # -- GUI settings sub-elements --
    # -------------------------------
    ## Gui sub-element : Run the keypad in fullscreen.  If enabled then the
    ## width and height element is ignored.
    JSON_Gui_Fullscreen = 'fullscreen'

    ## Gui sub-element : Height of GUI if fullscreen is disabled.
    JSON_Gui_WindowHeight = 'windowHeight'

    ## Gui sub-element : Width of GUI if fullscreen is disabled.
    JSON_Gui_WindowWidth = 'windowWidth'

    # ----------------------------------------------
    # -- Keypad controller settings sub-elements --
    # ----------------------------------------------
    ## Keypad controller sub-element : Authentication key for API.
    JSON_KeypadController_AuthKey = 'authorisationKey'

    ## Keypad controller sub-element : Network port keypad controller run on.
    JSON_KeypadController_NetworkPort = 'networkPort'

    ## Property getter : Last error message
    @property
    def last_error_msg(self):
        return self._last_error_msg


    ## ConfigurationManager class constructor.
    #  @param self The object pointer.
    def __init__(self):
        ## Holding member variable for last error message property.
        self._last_error_msg = ''


    ## Parse a configuration file, if the parse fails then the last error
    ## message is populated and None is returned.
    #  @param self The object pointer.
    #  @param filename Name of the configuration file to parse.
    #  @return Returns an instance of Configuration if successful, otherwise
    #  None is returned and the lastErrorMsg is populated.
    def parse_config_file(self, filename):
        self._last_error_msg = ''

        try:
            with open(filename) as file_handle:
                file_contents = file_handle.read()

        except IOError as excpt:
            self._last_error_msg = "Unable to open configuration file '" + \
                f"{filename}', reason: {excpt.strerror}"
            return None

        try:
            config_json = json.loads(file_contents)

        except json.JSONDecodeError as excpt:
            self._last_error_msg = "Unable to parse configuration file" + \
                f"{filename}, reason: {excpt}"
            return None

        try:
            jsonschema.validate(instance=config_json,
                                schema=CONFIGURATIONJSONSCHEMA)

        except jsonschema.exceptions.ValidationError as ex:
            self._last_error_msg = f"Configuration file {filename} failed " + \
                "to validate against expected schema.  Please check!.  "+ \
                f"Msg: {ex}"
            return None

        central_controller = self._process_central_controller_section(config_json)
        gui_section = self._process_gui_section(config_json)
        keypad_controller = self._process_keypad_controller_section(config_json)
        return Configuration(centralController=central_controller,
                             gui=gui_section,
                             keypadController=keypad_controller)


    ## Process the Central Controller section of the configuration.
    #  @param self The object pointer.
    #  @param config Raw configuration entry.
    def _process_central_controller_section(self, config):
        sctn = config[self.JSON_CentralControllerSettings]
        endpoint = sctn[self.JSON_CentralControllerSettings_Endpoint]
        auth_key = sctn[self.JSON_CentralControllerSettings_AuthKey]

        return CentralController(endpoint, auth_key)


    ## Process the GUI section of the configuration.
    #  @param self The object pointer.
    #  @param config Raw configuration entry.
    def _process_gui_section(self, config):
        sctn = config[self.JSON_GuiSettings]
        fullscreen = sctn[self.JSON_Gui_Fullscreen]
        window_height = sctn[self.JSON_Gui_WindowHeight]
        window_width = sctn[self.JSON_Gui_WindowWidth]

        return GuiSettings(fullscreen, window_height, window_width)


    ## Process the Keypad Controller section of the configuration.
    #  @param self The object pointer.
    #  @param config Raw configuration entry.
    def _process_keypad_controller_section(self, config):
        section = config[self.JSON_KeypadControllerSettings]
        auth_key = section[self.JSON_KeypadController_AuthKey]
        network_port = section[self.JSON_KeypadController_NetworkPort]
        return KeypadController(auth_key, network_port)
