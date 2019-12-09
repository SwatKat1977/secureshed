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
import jsonschema
import APIs.Keypad.JsonSchemas as schemas


class EvtType(enum.Enum):
    #------------------------
    #- Alarm state change events
    ChangeAlarmStateDeactivated = 1001
    ChangeAlarmStateActivated = 1002
    ChangeAlarmStateTriggered = 1003

    #------------------------
    #- Keypad entry events
    KeypadKeyCodeEntered = 2001


class StateManager:
    __slots__ = ['__config', '__currAlarmState', '__db',
                 '__failedEntryAttempts', '__logger']

    class AlarmState(enum.Enum):
        Deactivated = 0
        Activated = 1
        Triggered = 2


	#  @param self The object pointer.
    def __init__(self, controllerDb, logger, config):
        self.__config = config
        self.__currAlarmState = self.AlarmState.Deactivated
        self.__db = controllerDb
        self.__failedEntryAttempts = 0
        self.__logger = logger


	#  @param self The object pointer.
    def RcvKeypadEvent(self, eventInst):

        if eventInst.id == EvtType.KeypadKeyCodeEntered:
            self.__HandleKeyCodeEnteredEvent(eventInst)


	#  @param self The object pointer.
    def __HandleKeyCodeEnteredEvent(self, eventInst):

        body = eventInst.body

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.
        try:
            jsonschema.validate(instance=body,
                                schema=schemas.ReceiveKeyCodeJsonSchema)

        #except Exception as ex:
        except jsonschema.exceptions.ValidationError:
            errMsg = 'Message body validation failed.'
            #response = self.__endpoint.response_class(
            #    response=errMsg, status=400, mimetype='text')
            print(errMsg)
            return 'response'

        keySeq = body[schemas.receiveKeyCodeBody.KeySeq]

        # Read the key code detail from the database.
        details = self.__db.GetKeycodeDetails(keySeq)

        if details is not None:
            self.__logger.debug('A valid key code received')

            if self.__currAlarmState == self.AlarmState.Triggered:
                self.__logger.debug('Alarm state changed : Deactivated')
                self.__currAlarmState = self.AlarmState.Deactivated

            elif self.__currAlarmState == self.AlarmState.Deactivated:
                self.__logger.debug('Alarm state changed : Activated')
                self.__currAlarmState = self.AlarmState.Activated

            elif self.__currAlarmState == self.AlarmState.Activated:
                self.__logger.debug('Alarm state changed : Deactivated')
                self.__currAlarmState = self.AlarmState.Deactivated

            actions = \
            {
                schemas.receiveKeyCodeResponseAction_KeycodeAccepted.AlarmUnlocked \
                : None,
            }
            #responseType = ReceiveKeyCodeReturnCode.KeycodeAccepted.value

        else:
            self.__logger.debug('An invalid key code received')
            self.__failedEntryAttempts += 1

            attempts = self.__failedEntryAttempts
            actions = {}

            # If the attempt failed then send the response of type
            # receiveKeyCodeResponseAction_KeycodeIncorrect along with any
            # response actions that have been defined in the configuraution
            # file.
            if attempts in self.__config.failedAttemptResponses:
                responses = self.__config.failedAttemptResponses[attempts]

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

                        self.__currAlarmState.CurrentAlarmState = \
                            self.AlarmState.Triggered


            #responseType = ReceiveKeyCodeReturnCode.KeycodeIncorrect.value

        #responseMsg = self.__GenerateReceiveKeyCodeResponse(
        #    responseType, actions)

        #return self.__endpoint.response_class(response=responseMsg,
        #                                      status=HTTPStatusCode.OK,
        #                                      mimetype='application/json')
        return 'ok'

'''
import logging
import os
from centralController.ConfigurationManager import ConfigurationManager
from centralController.ControllerDBInterface import ControllerDBInterface
from common.Event import Event
controllerDbInterface = ControllerDBInterface()
controllerDbInterface.Connect(os.getenv('CENCON_DB'))

testMsgBody = {"keySequence" : "124"}
ev = Event(EvtType.KeypadKeyCodeEntered, testMsgBody)

FORMATTER = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                              "%Y-%m-%d %H:%M:%S")
LOGGER = logging.getLogger('system log')
CONSOLESTREAM = logging.StreamHandler()
CONSOLESTREAM.setFormatter(FORMATTER)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(CONSOLESTREAM)

CONFIGMANAGER = ConfigurationManager()
CONFIGURATION = CONFIGMANAGER.ParseConfigFile('centralController/configuration.json')
p = StateManager(controllerDbInterface, LOGGER, CONFIGURATION)
p.RcvKeypadEvent(ev)
p.RcvKeypadEvent(ev)
p.RcvKeypadEvent(ev)
p.RcvKeypadEvent(ev)
p.RcvKeypadEvent(ev)
p.RcvKeypadEvent(ev)
p.RcvKeypadEvent(ev)
'''

class StatusObject:

    class AlarmState(enum.Enum):
        Deactivated = 0
        Activated = 1
        Triggered = 2


    ## Property getter : Failed entry attempts
    @property
    def FailedEntryAttempts(self):
        return self.__failedEntryAttempts

    ## Property getter : Is authenticated flag.
    @property
    def CurrentAlarmState(self):
        return self.__alarmState

    @CurrentAlarmState.setter
    def CurrentAlarmState(self, newValue):
        self.__alarmState = newValue


	## StatusObject default constructor.
	#  @param self The object pointer.
    def __init__(self):
        self.__failedEntryAttempts = 0
        self.__alarmState = self.AlarmState.Deactivated


	## Increment the failed entry attempts.
	#  @param self The object pointer.
    def IncrementFailedEntryAttempts(self):
        self.__failedEntryAttempts += 1


	## Reset the failed entry attempts.
	#  @param self The object pointer.
    def ResetFailedEntryAttempts(self):
        self.__failedEntryAttempts = 0
