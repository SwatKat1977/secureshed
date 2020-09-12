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
import json
import time
import APIs.CentralController.JsonSchemas as schemas
import APIs.Keypad.JsonSchemas as keypadApi
import centralController.Events as Evts
from common.APIClient.APIEndpointClient import APIEndpointClient
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from common.Event import Event
from common.Logger import Logger, LogType


## Implementation of an alarm state management class.
class StateManager:
    __slots__ = ['__config', '__currAlarmState', '__db', '__eventMgr',
                 '__failedEntryAttempts', '__keypadApiClient',
                 '__transientStates', '_unableToConnErrorDisplayed']

    TransientStateEntry = collections.namedtuple('TransientStateEntry',
                                                 'id TransientState body')

    ## Alarm state enumeration.
    class AlarmState(enum.Enum):
        ## Alarm state : alarm is deactivated.
        Deactivated = 0

        ## Alarm state : alarm is activated.
        Activated = 1

        Triggered = 2


    ## StateManager class default constructor.
    #  @param self The object pointer.
    #  @param controllerDb Database controller interface instance.
    #  @param config Configuration items in json format.
    #  @param eventMgr Event manager instance.
    def __init__(self, controllerDb, config, eventMgr):
        self.__config = config
        self.__currAlarmState = self.AlarmState.Deactivated
        self.__db = controllerDb
        self.__eventMgr = eventMgr
        self.__failedEntryAttempts = 0
        self.__transientStates = []
        self._unableToConnErrorDisplayed = False

        endpoint = self.__config.keypadController.endpoint
        self.__keypadApiClient = APIEndpointClient(endpoint)


    ## Received events from the keypad.
    #  @param self The object pointer.
    #  @param eventInst Receieved keypad event.
    def RcvKeypadEvent(self, eventInst):

        if eventInst.id == Evts.EvtType.KeypadKeyCodeEntered:
            self.__HandleKeyCodeEnteredEvent(eventInst)


    #  @param self The object pointer.
    def RcvDeviceEvent(self, eventInst):

        if eventInst.id == Evts.EvtType.SensorDeviceStateChange:
            self.__HandleSensorDeviceStateChangeEvent(eventInst)


    ## Attemp to send an 'Alive Ping' message to the keypad, this is done when
    ## the keypad needs waking up after a sytem boot.
    #  @param self The object pointer.
    #  @param eventInst Event class that was created to raise this event.
    def SendAlivePingMsg(self, eventInst):

        additionalHeaders = {
            'authorisationKey' : self.__config.keypadController.authKey
        }

        response = self.__keypadApiClient.SendPostMsg('receiveCentralControllerPing',
                                                      MIMEType.JSON,
                                                      additionalHeaders, {})

        if response is None:
            if not self._unableToConnErrorDisplayed:
                msg = f'Unable to communicate with keypad, reason : ' +\
                    f'{self.__keypadApiClient.LastErrMsg}'
                Logger.Instance().Log(LogType.Info, msg)
                self.__eventMgr.QueueEvent(eventInst)
                self._unableToConnErrorDisplayed = True
            return

        # 401 Unauthenticated : Missing authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            Logger.Instance().Log(LogType.Critical,
                                  'Keypad cannot send AlivePing as the ' +\
                                  'authorisation key is missing')
            return

        # 403 forbidden : Invalid authentication key.
        if response.status_code == HTTPStatusCode.Forbidden:
            Logger.Instance().Log(LogType.Critical,
                                  'Keypad cannot send AlivePing as the ' +\
                                  'authorisation key is incorrect')
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:
            msg = f"Successfully send 'AlivePing' to keypad controller"
            Logger.Instance().Log(LogType.Info, msg)

        self._unableToConnErrorDisplayed = False


    def SendKeypadLockedMsg(self, eventInst):
        additionalHeaders = {
            'authorisationKey' : self.__config.keypadController.authKey
        }
        jsonBody = json.dumps(eventInst.body)
        response = self.__keypadApiClient.SendPostMsg('receiveKeypadLock',
                                                      MIMEType.JSON,
                                                      additionalHeaders,
                                                      jsonBody)

        if response is None:
            msg = f'Keypad locked msg : Unable to communicate with keypad, ' +\
                  f'reason : {self.__keypadApiClient.LastErrMsg}'
            Logger.Instance().Log(LogType.Debug, msg)
            self.__eventMgr.QueueEvent(eventInst)
            return

        # 401 Unauthenticated : Missing authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            Logger.Instance().Log(LogType.Critical,
                                  'Keypad locked msg : Cannot send the ' +\
                                  'AlivePing as the authorisation key ' +\
                                  'is missing')
            return

        # 403 forbidden : Invalid authentication key.
        if response.status_code == HTTPStatusCode.Forbidden:
            Logger.Instance().Log(LogType.Critical,
                                  'Keypad locked msg : Authorisation ' +\
                                  'key is incorrect')
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:
            msg = "Successfully sent 'Keypad locked msg' to keypad controller"
            Logger.Instance().Log(LogType.Debug, msg)


    #  @param self The object pointer.
    def UpdateTransitoryEvents(self):

        # List of event id's that need to be removed
        idList = []

        ## Transitory events go here....

        # Final stage is to remove all any of the transactions that have been
        # marked for removal.
        if idList:
            self.__transientStates = [evt for evt in \
                self.__transientStates if evt.id not in idList]


    ## Function to handle a a keycode has been entered.
    #  @param self The object pointer.
    #  @param eventInst The event that contains a keycode.
    def __HandleKeyCodeEnteredEvent(self, eventInst):
        body = eventInst.body

        keySeq = body[schemas.ReceiveKeyCode.BodyElement.KeySeq]

        # Read the key code detail from the database.
        details = self.__db.GetKeycodeDetails(keySeq)

        if details is not None:
            if self.__currAlarmState == self.AlarmState.Triggered:
                Logger.Instance().Log(LogType.Info, 'A triggered alarm has been deactivated')
                self.__currAlarmState = self.AlarmState.Deactivated
                self.__failedEntryAttempts = 0
                evt = Event(Evts.EvtType.DeactivateSiren, None)
                self.__eventMgr.QueueEvent(evt)
                self.__DeactivateAlarm()

            elif self.__currAlarmState == self.AlarmState.Deactivated:
                Logger.Instance().Log(LogType.Info, 'The alarm has been activated')
                self.__currAlarmState = self.AlarmState.Activated
                self.__failedEntryAttempts = 0
                self.__TriggerAlarm()

            elif self.__currAlarmState == self.AlarmState.Activated:
                Logger.Instance().Log(LogType.Info, 'The alarm has been deactivated')
                self.__currAlarmState = self.AlarmState.Deactivated
                self.__failedEntryAttempts = 0
                self.__DeactivateAlarm()

        else:
            Logger.Instance().Log(LogType.Info, 'An invalid key code was entered on keypad')
            self.__failedEntryAttempts += 1

            attempts = self.__failedEntryAttempts

            # If the attempt failed then send the response of type
            # receiveKeyCodeResponseAction_KeycodeIncorrect along with any
            # response actions that have been defined in the configuraution
            # file.
            if attempts in self.__config.failedAttemptResponses:
                responses = self.__config.failedAttemptResponses[attempts]

                for response in responses:

                    if response == 'disableKeyPad':
                        lockEvtBody = {
                            keypadApi.KeypadLockRequest.BodyElement.LockTime:
                            round(time.time()) + int(responses[response]['lockTime'])
                        }
                        lockEvt = Event(Evts.EvtType.KeypadApiSendKeypadLock,
                                        lockEvtBody)
                        self.__eventMgr.QueueEvent(lockEvt)

                    elif response == 'triggerAlarm':
                        if self.__currAlarmState != self.AlarmState.Triggered:
                            Logger.Instance().Log(LogType.Info, '|=> Alarm has been triggered!')
                            self.__TriggerAlarm(noGraceTime=True)

                    elif response == 'resetAttemptAccount':
                        self.__failedEntryAttempts = 0


    ## Function to handle the alarm being triggered.
    #  @param self The object pointer.
    def __TriggerAlarm(self, noGraceTime=False):
        self.__currAlarmState = self.AlarmState.Activated

        alarmSetEvtBody = {
            'activationTimestamp': time.time(),
            'noGraceTime': noGraceTime
        }

        activateEvt = Event(Evts.EvtType.AlarmActivated, alarmSetEvtBody)
        self.__eventMgr.QueueEvent(activateEvt)


    ## Function to handle the alarm being deactivated.
    #  @param self The object pointer.
    def __DeactivateAlarm(self):
        self.__currAlarmState = self.AlarmState.Deactivated
        self.__failedEntryAttempts = 0

        evt = Event(Evts.EvtType.AlarmDeactivated)
        self.__eventMgr.QueueEvent(evt)

        # Remove any 'InAlarmSetGraceTime' transient state events once the
        # alarm has been deactivated.
        #self.__transientStates = [evt for evt in self.__transientStates if \
        #    evt.TransientState != TransState.TransientState.InAlarmSetGraceTime]


    ## Event handler for a sensor device state change.
    #  @param self The object pointer.
    #  @param eventInst Device change event.
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
            Logger.Instance().Log(LogType.Info, logMsg)
            return

        # If the trigger has has already been triggered then opening or closing
        # a door etc. would change the alarm state, although we should log that
        # the even occurred.
        if self.__currAlarmState == self.AlarmState.Triggered:
            logMsg = f"{deviceName} was {stateStr}, alarm already triggered"
            Logger.Instance().Log(LogType.Info, logMsg)
            return

        if self.__currAlarmState == self.AlarmState.Activated:
            logMsg = f"Activity on {deviceName} ({stateStr}) has triggerd " +\
                "the alarm!"
            Logger.Instance().Log(LogType.Info, logMsg)
            self.__currAlarmState = self.AlarmState.Triggered

            evt = Event(Evts.EvtType.ActivateSiren, None)
            self.__eventMgr.QueueEvent(evt)
