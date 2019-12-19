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
import enum
import time
import uuid
import jsonschema
import APIs.Keypad.JsonSchemas as schemas
import centralController.Events as Evts
import centralController.TransientState as TransState
from common.Event import Event


class StateManager:
    __slots__ = ['__config', '__currAlarmState', '__db', '__eventMgr',
                 '__failedEntryAttempts', '__logger', '__transientStates']

    TransientStateEntry = collections.namedtuple('TransientStateEntry',
                                                 'id TransientState body')

    class AlarmState(enum.Enum):
        Deactivated = 0
        Activated = 1
        Triggered = 2


    ## StateManager class default constructor.
    #  @param self The object pointer.
    #  @param controllerDb Database controller interface instance.
    #  @param logger Logger instance.
    #  @param config Configuration items in json format.
    #  @param eventMgr Event manager instance.
    def __init__(self, controllerDb, logger, config, eventMgr):
        self.__config = config
        self.__currAlarmState = self.AlarmState.Deactivated
        self.__db = controllerDb
        self.__eventMgr = eventMgr
        self.__failedEntryAttempts = 0
        self.__logger = logger
        self.__transientStates = []


    ## Received events from the keypad.
    #  @param self The object pointer.
    def RcvKeypadEvent(self, eventInst):

        if eventInst.id == Evts.EvtType.KeypadKeyCodeEntered:
            self.__HandleKeyCodeEnteredEvent(eventInst)


    #  @param self The object pointer.
    def RcvDeviceEvent(self, eventInst):

        if eventInst.id == Evts.EvtType.SensorDeviceStateChange:
            self.__HandleSensorDeviceStateChangeEvent(eventInst)


    def UpdateTransitoryEvents(self):

        # List of event id's that need to be removed
        idList = []

        ## Transitory events go here....

        # Final stage is to remove all any of the transactions that have been
        # marked for removal.
        if idList:
            self.__transientStates = [evt for evt in \
                self.__transientStates if evt.id not in idList]


    #  @param self The object pointer.
    def __HandleKeyCodeEnteredEvent(self, eventInst):
        body = eventInst.body

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.
        try:
            jsonschema.validate(instance=body,
                                schema=schemas.ReceiveKeyCodeJsonSchema)

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
            if self.__currAlarmState == self.AlarmState.Triggered:
                self.__logger.info('A triggered alarm has been deactivated')
                self.__currAlarmState = self.AlarmState.Deactivated
                self.__failedEntryAttempts = 0
                evt = Event(Evts.EvtType.DeactivateSiren, None)
                self.__eventMgr.QueueEvent(evt)
                self.__DeactivateAlarm()

            elif self.__currAlarmState == self.AlarmState.Deactivated:
                self.__logger.info('The alarm has been activated')
                self.__currAlarmState = self.AlarmState.Activated
                self.__failedEntryAttempts = 0
                self.__TriggerAlarm()

            elif self.__currAlarmState == self.AlarmState.Activated:
                self.__logger.info('The alarm has been deactivated')
                self.__currAlarmState = self.AlarmState.Deactivated
                self.__failedEntryAttempts = 0
                self.__DeactivateAlarm()

            actions = \
            {
                schemas.receiveKeyCodeResponseAction_KeycodeAccepted.AlarmUnlocked \
                : None,
            }
            #responseType = ReceiveKeyCodeReturnCode.KeycodeAccepted.value

        else:
            self.__logger.info('An invalid key code was entered on keypad')
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

                        if self.__currAlarmState != self.AlarmState.Triggered:
                            self.__logger.info('|=> Alarm has been triggered!')
                            self.__TriggerAlarm()

                    elif response == 'resetAttemptAccount':
                        self.__failedEntryAttempts = 0

            #responseType = ReceiveKeyCodeReturnCode.KeycodeIncorrect.value

        #responseMsg = self.__GenerateReceiveKeyCodeResponse(
        #    responseType, actions)

        #return self.__endpoint.response_class(response=responseMsg,
        #                                      status=HTTPStatusCode.OK,
        #                                      mimetype='application/json')
        return 'ok'


    #  @param self The object pointer.
    def __TriggerAlarm(self):
        self.__currAlarmState = self.AlarmState.Activated

        alarmSetEvtBody = {'activationTimestamp': time.time()}
        activateEvt = Event(Evts.EvtType.AlarmActivated, alarmSetEvtBody)
        self.__eventMgr.QueueEvent(activateEvt)


    #  @param self The object pointer.
    def __DeactivateAlarm(self):
        self.__currAlarmState = self.AlarmState.Deactivated
        self.__failedEntryAttempts = 0

        # Remove any 'InAlarmSetGraceTime' transient state events once the
        # alarm has been deactivated.
        self.__transientStates = [evt for evt in self.__transientStates if \
            evt.TransientState != TransState.TransientState.InAlarmSetGraceTime]


    #  @param self The object pointer.
    def __HandleSensorDeviceStateChangeEvent(self, eventInst):
        body = eventInst.body
        deviceName = body[Evts.SensorDeviceBodyItem.DeviceName]
        state = body[Evts.SensorDeviceBodyItem.State]

        triggered = True if state == 1 else False
        stateStr = "opened" if triggered else "closed"

        # If the alarm is deactived then ignore the sensor state change after
        # logging the change for reference.
        if self.__currAlarmState == self.AlarmState.Deactivated:
            logMsg = f"{deviceName} was {stateStr}, although alarm isn't on"
            self.__logger.info(logMsg)
            return

        # If the trigger has has already been triggered then opening or closing
        # a door etc. would change the alarm state, although we should log that
        # the even occurred.
        if self.__currAlarmState == self.AlarmState.Triggered:
            logMsg = f"{deviceName} was {stateStr}, alarm already triggered"
            self.__logger.info(logMsg)
            return

        if self.__currAlarmState == self.AlarmState.Activated:
            logMsg = f"Activity on {deviceName} ({stateStr}) has triggerd " +\
                "the alarm!"
            self.__logger.info(logMsg)
            self.__currAlarmState = self.AlarmState.Triggered

            evt = Event(Evts.EvtType.ActivateSiren, None)
            self.__eventMgr.QueueEvent(evt)
