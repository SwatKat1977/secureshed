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
from centralController.Configuration import Configuration
from centralController.ConfigurationJsonSchema import CONFIGURATIONJSONSCHEMA
from centralController.FailedCodeAttemptAction import (FailedCodeAttemptActionType,
                                                       ActionTypeParams)


class ConfigurationManager:

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

        except jsonschema.exceptions.ValidationError:
            self.__lastErrorMsg = f"Configuration file {filename} failed " + \
                "to validate against expected schema.  Please check!"
            return None

        centralCtrlApiSect = configJson[self.JSON_CentralCtrlApi]
        centralApi = self.__ProcessCentralControllerSection(centralCtrlApiSect)

        generalSetting = configJson[self.JSON_GeneralSettings]
        devicesCfgFile = generalSetting[self.JSON_GeneralSettingsDevicesConfigFile]
        generalSettingsCfg = Configuration.GeneralSettings(devicesCfgFile)

        # Populate the keypad controller configuration items.
        keypadController = configJson[self.JSON_KeypadController]
        keypadCtrlEndpoint = keypadController[self.JSON_KeypadControllerEndpoint]
        keypadCtrlAuthKey = keypadController[self.JSON_KeypadControllerAuthKey]
        keypadCtrlCfg = Configuration.KeypadControllerCfg(keypadCtrlEndpoint,
                                                          keypadCtrlAuthKey)

        failedAttemptResponses = {}

        for resp in configJson[self.JSON_FailedAttemptResponses]:

            processedResp = self.__ProcessFailedCodeResponse(resp)

            if processedResp is None:
                return None

            attemptNo, response = processedResp
            failedAttemptResponses[attemptNo] = response

        return Configuration(centralApi, generalSettingsCfg,
                             failedAttemptResponses, keypadCtrlCfg)


    ## Process the central controller api settings section.
    #  @param self The object pointer.
    def __ProcessCentralControllerSection(self, sect):
        networkPort = sect[self.JSON_CentralCtrlApiPort]
        authKey = sect[self.JSON_CentralCtrlApiAuthKey]
        return Configuration.CentralControllerApiCfg(networkPort, authKey)


    #  @param self The object pointer.
    def __ProcessFailedCodeResponse(self, response):

        processedResponse = {}

        attemptNo = response[self.JSON_failedAttemptResponseAttemptNo]
        actions = response[self.JSON_failedAttemptResponseActions]

        for action in actions:
            paramsList = action[self.JSON_failedAttemptResponseActionsParams]
            actionType = action[self.JSON_failedAttemptResponseActionsType]

            processedParams = {}

            # This should never happen, but verify is the action type is known
            # about, throwing an error if not.
            if not FailedCodeAttemptActionType.IsName(actionType):
                self.__lastErrorMsg = f'Action type {actionType} not valid'
                return None

            # Extract the name of all of the parameters for the action out and
            # then verify they are all valid.
            paramKeys = [d['key'] for d in paramsList]
            if not all(elem in ActionTypeParams[actionType].keys() for elem in paramKeys):
                self.__lastErrorMsg = f'Action type {actionType} has an invalid ' +\
                    'list of parameters'
                return None

            for param in paramsList:
                paramName = param['key']

                if ActionTypeParams[actionType][paramName] == int:
                    try:
                        processedParams[paramName] = int(param['value'])
                    except ValueError:
                        self.__lastErrorMsg = f'Parameter {paramName} has ' +\
                            'an invalid type, expecting integer, value is ' +\
                            f"{param['value']}"
                        return None

                elif ActionTypeParams[actionType][paramName] == str:
                    processedParams[paramName] = param['value']

            processedResponse[actionType] = processedParams

        return (attemptNo, processedResponse)
