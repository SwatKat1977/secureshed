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
import json
import jsonschema
from central_controller.configuration import Configuration
from central_controller.configuration_json_schema import CONFIGURATIONJSONSCHEMA
from central_controller.failed_code_attempt_action import (FailedCodeAttemptActionType,
                                                           ACTION_TYPE_PARAMS)


class ConfigurationManager:
    # pylint: disable=too-many-locals

    # -----------------------------
    # -- Top-level json elements --
    # -----------------------------
    JSON_AlarmSettings = 'alarmSettings'
    JSON_CentralCtrlApi = 'centralControllerApi'
    JSON_KeypadController = 'keypadController'
    JSON_GeneralSettings = 'generalSettings'
    JSON_FailedAttemptResponses = 'failedAttemptResponses'

    # -----------------------------------------
    # -- Central Controller Api sub-elements --
    # -----------------------------------------
    JSON_CentralCtrlApiPort = 'networkPort'
    JSON_CentralCtrlApiAuthKey = 'authKey'

    # -----------------------------
    # -- General settings sub-elements --
    # -----------------------------
    JSON_GeneralSettingsDevicesConfigFile = 'devicesConfigFile'
    JSON_GeneralSettingsDeviceTypesConfigFile = 'deviceTypesConfigFile'

    # ------------------------------------------
    # -- Failed attempt tesponse sub-elements --
    # ------------------------------------------
    JSON_failedAttemptResponseAttemptNo = 'attemptNo'
    JSON_failedAttemptResponseActions = 'actions'
    JSON_failedAttemptResponseActionsType = 'actionType'
    JSON_failedAttemptResponseActionsParams = 'parameters'

    # ---------------------------------
    # -- Alarm settings sub-elements --
    # ---------------------------------
    JSON_AlarmSettingsAlarmSetGraceTimeSecs = 'AlarmSetGraceTimeSecs'

    # ------------------------------------
    # -- Keypad Controller sub-elements --
    # ------------------------------------
    JSON_KeypadControllerEndpoint = 'endpoint'
    JSON_KeypadControllerAuthKey = 'authKey'


    ## Property getter : Last error message
    @property
    def last_error_msg(self):
        return self._last_error_msg


    #  @param self The object pointer.
    def __init__(self):
        self._last_error_msg = ''


    #  @param self The object pointer.
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

        except jsonschema.exceptions.ValidationError:
            self._last_error_msg = f"Configuration file {filename} failed " + \
                "to validate against expected schema.  Please check!"
            return None

        central_ctrl_api_sect = config_json[self.JSON_CentralCtrlApi]
        central_api = self._process_central_controller_section(central_ctrl_api_sect)

        general_setting = config_json[self.JSON_GeneralSettings]
        general_settings_cfg = self._process_general_section(general_setting)

        # Populate the keypad controller configuration items.
        keypad_controller = config_json[self.JSON_KeypadController]
        keypad_ctrl_endpoint = keypad_controller[self.JSON_KeypadControllerEndpoint]
        keypad_ctrl_auth_key = keypad_controller[self.JSON_KeypadControllerAuthKey]
        keypad_ctrl_cfg = Configuration.KeypadControllerCfg(keypad_ctrl_endpoint,
                                                            keypad_ctrl_auth_key)

        failed_attempt_responses = {}

        for resp in config_json[self.JSON_FailedAttemptResponses]:

            processed_resp = self._process_failed_code_response(resp)

            if processed_resp is None:
                return None

            attempt_no, response = processed_resp
            failed_attempt_responses[attempt_no] = response

        return Configuration(central_api, general_settings_cfg,
                             failed_attempt_responses, keypad_ctrl_cfg)


    ## Process the central controller api settings section.
    #  @param self The object pointer.
    def _process_central_controller_section(self, sect):
        network_port = sect[self.JSON_CentralCtrlApiPort]
        auth_key = sect[self.JSON_CentralCtrlApiAuthKey]
        return Configuration.CentralControllerApiCfg(network_port, auth_key)


    ## Process the general settings section.
    #  @param self The object pointer.
    def _process_general_section(self, sect):
        devices_cfg_file = sect[self.JSON_GeneralSettingsDevicesConfigFile]
        device_types_config_file = sect[self.JSON_GeneralSettingsDeviceTypesConfigFile]
        return Configuration.GeneralSettings(devices_cfg_file,
                                             device_types_config_file)


    #  @param self The object pointer.
    def _process_failed_code_response(self, response):

        processed_response = {}

        attempt_no = response[self.JSON_failedAttemptResponseAttemptNo]
        actions = response[self.JSON_failedAttemptResponseActions]

        for action in actions:
            params_list = action[self.JSON_failedAttemptResponseActionsParams]
            action_type = action[self.JSON_failedAttemptResponseActionsType]

            processed_params = {}

            # This should never happen, but verify is the action type is known
            # about, throwing an error if not.
            if not FailedCodeAttemptActionType.is_name(action_type):
                self._last_error_msg = f'Action type {action_type} not valid'
                return None

            # Extract the name of all of the parameters for the action out and
            # then verify they are all valid.
            param_keys = [d['key'] for d in params_list]
            if not all(elem in ACTION_TYPE_PARAMS[action_type].keys() for elem in param_keys):
                self._last_error_msg = f'Action type {action_type} has an invalid ' +\
                    'list of parameters'
                return None

            for param in params_list:
                param_name = param['key']

                if ACTION_TYPE_PARAMS[action_type][param_name] == int:
                    try:
                        processed_params[param_name] = int(param['value'])
                    except ValueError:
                        self._last_error_msg = f'Parameter {param_name} has ' +\
                            'an invalid type, expecting integer, value is ' +\
                            f"{param['value']}"
                        return None

                elif ACTION_TYPE_PARAMS[action_type][param_name] == str:
                    processed_params[param_name] = param['value']

            processed_response[action_type] = processed_params

        return (attempt_no, processed_response)
