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
from flask import Flask, request, abort
import jsonschema
import APIs.Keypad.JsonSchemas as schemas
from APIs.Keypad.ReceiveKeyCodeReturnCode import ReceiveKeyCodeReturnCode
from common.APIClient.HTTPStatusCode import HTTPStatusCode


## Implementation of thread that handles API calls to the keypad API.
class KeypadApiController:

    __slots__ = ['__config', '__db', '__endpoint', '__logger', '__statusObject']


    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param listeningPort Network port to listen on.
    def __init__(self, logger, statusObject, controllerDb, config, endpoint):

        self.__config = config
        self.__db = controllerDb
        self.__endpoint = endpoint
        self.__logger = logger
        self.__statusObject = statusObject

        # Add route : /receiveKeyCode
        self.__endpoint.add_url_rule('/receiveKeyCode', methods=['POST'],
                                     view_func=self.__ReceiveKeyCode)


    ## API route : receiveKeyCode
    #  Recieve a key code from the keypad.  This is for unlocking/disabling the
    #  alarm system.
    #  Return codes:
    #  * 200 (OK) - code accepted, rejected or refused.
    #  * 400 (Bad Request) - Missing or invalid json body or validation failed.
    #  * 401 (Unauthenticated) - Missing or invalid authentication key.
    def __ReceiveKeyCode(self):

        # Check for that the message body ia of type application/json and that
        # there is one, if not report a 400 error status with a human-readable.
        body = request.get_json()
        if not body:
            errMsg = 'Missing/invalid json body'
            response = self.__endpoint.response_class(
                response=errMsg, status=400, mimetype='text')
            return response

        # Verify that an authorisation key exists in the requet header, if not
        # then return a 401 error with a human-readable reasoning. 
        if schemas.receiveKeyCodeHeader.AuthKey not in request.headers:
            errMsg = 'Authorisation key is missing'
            response = self.__endpoint.response_class(
                response=errMsg, status=401, mimetype='text')
            return response

        authorisationKey = request.headers[schemas.receiveKeyCodeHeader.AuthKey]

        # As the authorisation key functionality isn't currently implemented I
        # have hard-coded as 'authKey'.  If the key isn't valid then the error
        # code of 401 (Unauthenticated) is returned.
        if authorisationKey != 'authKey':
            errMsg = 'Authorisation key is invalid'
            response = self.__endpoint.response_class(
                response=errMsg, status=401, mimetype='text')
            return response

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.
        try:
            jsonschema.validate(instance=body,
                                schema=schemas.ReceiveKeyCodeJsonSchema)

        except Exception as ex:
            errMsg = 'Message body validation failed.'
            response = self.__endpoint.response_class(
                response=errMsg, status=400, mimetype='text')
            return response

        keySeq = body[schemas.receiveKeyCodeBody.KeySeq]

        # Read the key code detail from the database.
        details = self.__db.GetKeycodeDetails(keySeq)

        if details != None:
            self.__logger.debug('A valid key code received')

            if self.__statusObject.CurrentAlarmState == \
                self.__statusObject.AlarmState.Triggered:
                self.__logger.debug(
                    'Alarm state changed : Unlocked')
                self.__statusObject.CurrentAlarmState = \
                    self.__statusObject.AlarmState.Deactivated

            elif self.__statusObject.CurrentAlarmState == \
                self.__statusObject.AlarmState.Deactivated:
                self.__logger.debug(
                    'Alarm state changed : Activated')
                self.__statusObject.CurrentAlarmState = \
                    self.__statusObject.AlarmState.Activated

            elif self.__statusObject.CurrentAlarmState == \
                self.__statusObject.AlarmState.Activated:
                self.__logger.debug(
                    'Alarm state changed : Deactivated')
                self.__statusObject.CurrentAlarmState = \
                    self.__statusObject.AlarmState.Deactivated

            actions = \
            {
                schemas.receiveKeyCodeResponseAction_KeycodeAccepted.AlarmUnlocked \
                : None,
            }
            responseType = ReceiveKeyCodeReturnCode.KeycodeAccepted.value

        else:
            self.__logger.debug('An invalid key code received')

            self.__statusObject.IncrementFailedEntryAttempts()
            attempts = self.__statusObject.FailedEntryAttempts

            actions = {}

            # If the attempt failed then send the response of type
            # receiveKeyCodeResponseAction_KeycodeIncorrect along with any
            # response actions that have been defined in the configuraution
            # file.
            if attempts in self.__config.FailedAttemptResponses:
                responses = self.__config.FailedAttemptResponses[attempts]

                for response in responses:

                    if response == 'disableKeyPad':
                        actions[schemas. \
                        receiveKeyCodeResponseAction_KeycodeIncorrect. \
                        DisableKeypad] = int(responses[response]['lockTime'])

                    elif response == 'triggerAlarm':
                        actions[schemas. \
                        receiveKeyCodeResponseAction_KeycodeIncorrect. \
                        TriggerAlarm] = None
                        self.__logger.debug('Alarm triggered!')

                        self.__statusObject.CurrentAlarmState = \
                            self.__statusObject.AlarmState.Triggered

            responseType = ReceiveKeyCodeReturnCode.KeycodeIncorrect.value

        responseMsg = self.__GenerateReceiveKeyCodeResponse(
            responseType, actions)

        return self.__endpoint.response_class(response=responseMsg,
                                              status=HTTPStatusCode.OK,
                                              mimetype='application/json')


    ## Generate a receive key code response message.
    #  @param self The object pointer.
    #  @param returnCode The return code for the response.
    #  @param actions List of actions to do with the response.
    #  @return Returns a JSON string with return code and actions. 
    def __GenerateReceiveKeyCodeResponse(self, returnCode, actions):
        responseJson = \
        {
            schemas.receiveKeyCodeResponse.ReturnCode : returnCode,
            schemas.receiveKeyCodeResponse.Actions : actions
        }
        return json.dumps(responseJson)
