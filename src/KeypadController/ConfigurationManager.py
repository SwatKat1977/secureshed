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
import jsonschema
from ConfigurationJsonSchema import CONFIGURATIONJSONSCHEMA


CentralController = collections.namedtuple('CentralController', 'endpoint')
Configuration = collections.namedtuple('Configuration', 'CentralController')


class ConfigurationManager:

    # -----------------------------
    # -- Top-level json elements --
    # -----------------------------
    JSON_CentralControllerSettings = 'centralControllerSettings'

    # ----------------------------------------------
    # -- Central controller settings sub-elements --
    # ----------------------------------------------
    JSON_CentralControllerSettings_Endpoint = 'endpoint'


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

        keypadApiNetworkPort = configJson[self.JSON_keypadAPI][self.JSON_keypadAPI_Port]
        keypadAPIConfig = Configuration.KeypadAPICfg(keypadApiNetworkPort)

        generalSetting = configJson[self.JSON_GeneralSettings]
        devicesCfgFile = generalSetting[self.JSON_GeneralSettings_DevicesConfigFile]
        generalSettingsCfg = Configuration.GeneralSettings(devicesCfgFile)

        failedAttemptResponses = {}

        for resp in configJson[self.JSON_failedAttemptResponses]:

            processedResp = self.__ProcessFailedCodeResponse(resp)

            if processedResp is None:
                return None

            attemptNo, response = processedResp
            failedAttemptResponses[attemptNo] = response

        return Configuration(keypadAPIConfig, generalSettingsCfg,
                             failedAttemptResponses)


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


testCls = ConfigurationManager()
x = testCls.ParseConfigFile('configuration.json')
print(x)
print(testCls.lastErrorMsg)