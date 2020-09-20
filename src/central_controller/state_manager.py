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
import json
import time
import APIs.CentralController.JsonSchemas as schemas
import APIs.Keypad.JsonSchemas as keypadApi
import central_controller.events as Evts
from common.APIClient.APIEndpointClient import APIEndpointClient
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from common.Event import Event
from common.Logger import LogType


## Implementation of an alarm state management class.
class StateManager:
    # pylint: disable=too-many-instance-attributes

    __slots__ = ['_config', '_current_alarm_state', '_database', '_event_mgr',
                 '_failed_entry_attempts', '_keypad_api_client', '_logger',
                 '_transient_states', '_unable_to_conn_error_displayed']


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
    def __init__(self, controllerDb, config, eventMgr, logger):
        self._config = config
        self._current_alarm_state = self.AlarmState.Deactivated
        self._database = controllerDb
        self._event_mgr = eventMgr
        self._failed_entry_attempts = 0
        self._logger = logger
        self._transient_states = []
        self._unable_to_conn_error_displayed = False

        endpoint = self._config.keypad_controller.endpoint
        self._keypad_api_client = APIEndpointClient(endpoint)


    ## Received events from the keypad.
    #  @param self The object pointer.
    #  @param eventInst Receieved keypad event.
    def rcv_keypad_event(self, event):
        if event.id == Evts.EvtType.KeypadKeyCodeEntered:
            self._handle_key_code_entered_event(event)


    #  @param self The object pointer.
    def rcv_device_event(self, event):
        if event.id == Evts.EvtType.SensorDeviceStateChange:
            self._handle_sensor_device_state_change_event(event)


    ## Attemp to send an 'Alive Ping' message to the keypad, this is done when
    ## the keypad needs waking up after a sytem boot.
    #  @param self The object pointer.
    #  @param eventInst Event class that was created to raise this event.
    def send_alive_ping_msg(self, event):

        additional_headers = {
            'authorisationKey' : self._config.keypad_controller.authKey
        }

        response = self._keypad_api_client.SendPostMsg(
            'receiveCentralControllerPing',
            MIMEType.JSON,
            additional_headers, {})

        if response is None:
            if not self._unable_to_conn_error_displayed:
                msg = 'Unable to communicate with keypad, reason : ' +\
                    f'{self._keypad_api_client.LastErrMsg}'
                self._logger.Log(LogType.Info, msg)
                self._event_mgr.QueueEvent(event)
                self._unable_to_conn_error_displayed = True
            return

        # 401 Unauthenticated : Missing authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            self._logger.Log(LogType.Critical,
                             'Keypad cannot send AlivePing as the ' +\
                             'authorisation key is missing')
            return

        # 403 forbidden : Invalid authentication key.
        if response.status_code == HTTPStatusCode.Forbidden:
            self._logger.Log(LogType.Critical,
                             'Keypad cannot send AlivePing as the ' +\
                             'authorisation key is incorrect')
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:
            msg = "Successfully send 'AlivePing' to keypad controller"
            self._logger.Log(LogType.Info, msg)

        self._unable_to_conn_error_displayed = False


    def send_keypad_locked_msg(self, event):
        additional_headers = {
            'authorisationKey' : self._config.keypad_controller.authKey
        }
        json_body = json.dumps(event.body)
        response = self._keypad_api_client.SendPostMsg('receiveKeypadLock',
                                                       MIMEType.JSON,
                                                       additional_headers,
                                                       json_body)

        if response is None:
            msg = 'Keypad locked msg : Unable to communicate with keypad, ' +\
                  f'reason : {self._keypad_api_client.LastErrMsg}'
            self._logger.Log(LogType.Debug, msg)
            self._event_mgr.QueueEvent(event)
            return

        # 401 Unauthenticated : Missing authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            self._logger.Log(LogType.Critical,
                             'Keypad locked msg : Cannot send the ' +\
                             'AlivePing as the authorisation key ' +\
                             'is missing')
            return

        # 403 forbidden : Invalid authentication key.
        if response.status_code == HTTPStatusCode.Forbidden:
            self._logger.Log(LogType.Critical,
                             'Keypad locked msg : Authorisation ' +\
                             'key is incorrect')
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:
            msg = "Successfully sent 'Keypad locked msg' to keypad controller"
            self._logger.Log(LogType.Debug, msg)


    #  @param self The object pointer.
    def update_transitory_events(self):

        # List of event id's that need to be removed
        id_list = []

        ## Transitory events go here....

        # Final stage is to remove all any of the transactions that have been
        # marked for removal.
        if id_list:
            self._transient_states = [evt for evt in \
                self._transient_states if evt.id not in id_list]


    ## Function to handle a a keycode has been entered.
    #  @param self The object pointer.
    #  @param eventInst The event that contains a keycode.
    def _handle_key_code_entered_event(self, event):
        body = event.body

        key_sequence = body[schemas.ReceiveKeyCode.BodyElement.KeySeq]

        # Read the key code detail from the database.
        details = self._database.get_keycode_details(key_sequence)

        if details is not None:
            if self._current_alarm_state == self.AlarmState.Triggered:
                self._logger.Log(LogType.Info, 'A triggered alarm has been deactivated')
                self._current_alarm_state = self.AlarmState.Deactivated
                self._failed_entry_attempts = 0
                evt = Event(Evts.EvtType.DeactivateSiren, None)
                self._event_mgr.QueueEvent(evt)
                self._deactivate_alarm()

            elif self._current_alarm_state == self.AlarmState.Deactivated:
                self._logger.Log(LogType.Info, 'The alarm has been activated')
                self._current_alarm_state = self.AlarmState.Activated
                self._failed_entry_attempts = 0
                self._trigger_alarm()

            elif self._current_alarm_state == self.AlarmState.Activated:
                self._logger.Log(LogType.Info, 'The alarm has been deactivated')
                self._current_alarm_state = self.AlarmState.Deactivated
                self._failed_entry_attempts = 0
                self._deactivate_alarm()

        else:
            self._logger.Log(LogType.Info, 'An invalid key code was entered on keypad')
            self._failed_entry_attempts += 1

            attempts = self._failed_entry_attempts

            # If the attempt failed then send the response of type
            # receiveKeyCodeResponseAction_KeycodeIncorrect along with any
            # response actions that have been defined in the configuraution
            # file.
            if attempts in self._config.failed_attempt_responses:
                responses = self._config.failed_attempt_responses[attempts]

                for response in responses:

                    if response == 'disableKeyPad':
                        lock_event_body = {
                            keypadApi.KeypadLockRequest.BodyElement.LockTime:
                            round(time.time()) + int(responses[response]['lockTime'])
                        }
                        lock_event = Event(Evts.EvtType.KeypadApiSendKeypadLock,
                                           lock_event_body)
                        self._event_mgr.QueueEvent(lock_event)

                    elif response == 'triggerAlarm':
                        if self._current_alarm_state != self.AlarmState.Triggered:
                            self._logger.Log(LogType.Info, '|=> Alarm has been triggered!')
                            self._trigger_alarm(no_grace_time=True)

                    elif response == 'resetAttemptAccount':
                        self._failed_entry_attempts = 0


    ## Function to handle the alarm being triggered.
    #  @param self The object pointer.
    def _trigger_alarm(self, no_grace_time=False):
        self._current_alarm_state = self.AlarmState.Activated

        alarm_set_evt_body = {
            'activationTimestamp': time.time(),
            'noGraceTime': no_grace_time
        }

        activate_event = Event(Evts.EvtType.AlarmActivated, alarm_set_evt_body)
        self._event_mgr.QueueEvent(activate_event)


    ## Function to handle the alarm being deactivated.
    #  @param self The object pointer.
    def _deactivate_alarm(self):
        self._current_alarm_state = self.AlarmState.Deactivated
        self._failed_entry_attempts = 0

        evt = Event(Evts.EvtType.AlarmDeactivated)
        self._event_mgr.QueueEvent(evt)


    ## Event handler for a sensor device state change.
    #  @param self The object pointer.
    #  @param eventInst Device change event.
    def _handle_sensor_device_state_change_event(self, event):
        body = event.body
        device_name = body[Evts.SensorDeviceBodyItem.DeviceName]
        state = body[Evts.SensorDeviceBodyItem.State]

        triggered = bool(state == 1)
        state_str = "opened" if triggered else "closed"

        # If the alarm is deactived then ignore the sensor state change after
        # logging the change for reference.
        if self._current_alarm_state == self.AlarmState.Deactivated:
            log_msg = f"{device_name} was {state_str}, although alarm isn't on"
            self._logger.Log(LogType.Info, log_msg)
            return

        # If the trigger has has already been triggered then opening or closing
        # a door etc. would change the alarm state, although we should log that
        # the even occurred.
        if self._current_alarm_state == self.AlarmState.Triggered:
            log_msg = f"{device_name} was {state_str}, alarm already triggered"
            self._logger.Log(LogType.Info, log_msg)
            return

        if self._current_alarm_state == self.AlarmState.Activated:
            log_msg = f"Activity on {device_name} ({state_str}) has triggerd " +\
                "the alarm!"
            self._logger.Log(LogType.Info, log_msg)
            self._current_alarm_state = self.AlarmState.Triggered

            evt = Event(Evts.EvtType.ActivateSiren, None)
            self._event_mgr.QueueEvent(evt)
