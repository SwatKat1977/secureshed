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
import centralController.Events as Evts


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

        if eventInst.id == Evts.EvtType.KeypadKeyCodeEntered:
            self.__HandleKeyCodeEnteredEvent(eventInst)


	#  @param self The object pointer.
    def RcvDeviceEvent(self, eventInst):

        if eventInst.id == Evts.EvtType.SensorDeviceStateChange:
            self.__HandleSensorDeviceStateChangeEvent(eventInst)


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
                self.__logger.info('Alarm state has been deactivated')
                self.__currAlarmState = self.AlarmState.Deactivated
                self.__failedEntryAttempts = 0

            elif self.__currAlarmState == self.AlarmState.Deactivated:
                self.__logger.info('Alarm state has been activated')
                self.__currAlarmState = self.AlarmState.Activated
                self.__failedEntryAttempts = 0

            elif self.__currAlarmState == self.AlarmState.Activated:
                self.__logger.info('Alarm state has been deactivated')
                self.__currAlarmState = self.AlarmState.Deactivated
                self.__failedEntryAttempts = 0

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
                            self.__currAlarmState = self.AlarmState.Triggered

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
            self.__logger.debug(logMsg)
            return

        # If the trigger has has already been triggered then opening or closing
        # a door etc. would change the alarm state, although we should log that
        # the even occurred.
        if self.__currAlarmState == self.AlarmState.Triggered:
            logMsg = f"{deviceName} was {stateStr}, alarm already triggered"
            self.__logger.debug(logMsg)
            return

        elif self.__currAlarmState == self.AlarmState.Activated:
            logMsg = f"Activity on {deviceName} ({stateStr}) has triggerd " +\
                "the alarm!"
            self.__logger.debug(logMsg)
            self.__currAlarmState = self.AlarmState.Triggered
