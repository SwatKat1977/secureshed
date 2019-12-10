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
from centralController.Configuration import KeypadAPIConfig, Configuration
from centralController.ConfigurationJsonSchema import ConfigurationJsonSchema
from centralController.FailedCodeAttemptAction import (FailedCodeAttemptActionType,
                                                       ActionTypeParams)


class ConfigurationManager:

    JSON_keypadAPI = 'keypadAPI'
    JSON_keypadAPI_Port = 'NetworkPort'
    JSON_failedAttemptResponses = 'failedAttemptResponses'

    JSON_failedAttemptResponseAttemptNo = 'attemptNo'
    JSON_failedAttemptResponseActions = 'actions'
    JSON_failedAttemptResponseActionsType = 'actionType'
    JSON_failedAttemptResponseActionsParams = 'parameters'


    ## Property getter : Last error message
    @property
    def lastErrorMsg(self):
        return self.__lastErrorMsg


    def __init__(self):
        self.__lastErrorMsg = ''


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
                                schema=ConfigurationJsonSchema)

        except jsonschema.exceptions.ValidationError:
            self.__lastErrorMsg = f"Configuration file {filename} failed " + \
                "to validate against expected schema.  Please check!"
            return None

        keypadApiNetworkPort = configJson[self.JSON_keypadAPI][self.JSON_keypadAPI_Port]
        keypadAPIConfig = KeypadAPIConfig(keypadApiNetworkPort)

        failedAttemptResponses = {}

        for resp in configJson[self.JSON_failedAttemptResponses]:

            processedResp = self.__ProcessFailedCodeResponse(resp)

            if processedResp is None:
                return None

            attemptNo, response = processedResp
            failedAttemptResponses[attemptNo] = response

        return Configuration(keypadAPIConfig, failedAttemptResponses)


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
