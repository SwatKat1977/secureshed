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


JSON_keypadAPI = 'keypadAPI'
JSON_keypadAPI_Port = 'NetworkPort'
JSON_failedAttemptResponses = 'failedAttemptResponses'

JSON_failedAttemptResponseAttemptNo = 'attemptNo'
JSON_failedAttemptResponseActions = 'actions'
JSON_failedAttemptResponseActionsType = 'actionType'
JSON_failedAttemptResponseActionsParams = 'parameters'


class ConfigurationManager(object):

    ## Property getter : Last error message
    @property
    def LastErrorMsg(self):
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
            jsonschema.validate(instance = configJson,
                schema = ConfigurationJsonSchema)

        except Exception as ex:
            self.__lastErrorMsg = f"Configuration file {filename} failed " + \
                "to validate against expected schema.  Please check!"
            return None

        keypadApiNetworkPort = configJson[JSON_keypadAPI][JSON_keypadAPI_Port]
        keypadAPIConfig = KeypadAPIConfig(keypadApiNetworkPort)

        failedAttemptResponses = {}

        for resp in configJson[JSON_failedAttemptResponses]:

            processedResp = self.__ProcessFailedCodeResponse(resp)

            if processedResp == None:
                return None

            attemptNo, response = processedResp
            failedAttemptResponses[attemptNo] = response

        return Configuration(keypadAPIConfig, failedAttemptResponses)


    def __ProcessFailedCodeResponse(self, response):

        processedResponse = {}

        attemptNo = response[JSON_failedAttemptResponseAttemptNo]
        actionsList = []

        actions = response[JSON_failedAttemptResponseActions]

        for action in actions:
            paramsList = action[JSON_failedAttemptResponseActionsParams]

            type = action[JSON_failedAttemptResponseActionsType]
            
            processedParams = {}

            # This should never happen, but verify is the action type is known
            # about, throwing an error if not.
            if not FailedCodeAttemptActionType.IsName(type):
                self.__lastErrorMsg = f'Action type {type} not valid'
                return None

            # Extract the name of all of the parameters for the action out and
            # then verify they are all valid.
            paramKeys = [d['key'] for d in paramsList]
            if not all(elem in ActionTypeParams[type].keys() for elem in paramKeys):
                self.__lastErrorMsg = f'Action type {type} has an invalid ' +\
                    'list of parameters'
                return None
 
            for p in paramsList:
                paramName = p['key']
                
                if ActionTypeParams[type][paramName] == int:
                    try:
                        processedParams[paramName] = int(p['value'])
                    except ValueError:
                        self.__lastErrorMsg = f'Parameter {paramName} has ' +\
                            'an invalid type, expecting integer, value is ' +\
                            f"{p['value']}"
                        return None

                elif ActionTypeParams[type][paramName] == string:
                    processedParams[paramName] = int(p['value'])

            processedResponse[type] = processedParams

        return (attemptNo, processedResponse)
