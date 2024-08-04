"""
Copyright 2019-2024 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import dataclasses
import enum
import json
import logging
import time
import APIs.CentralController.JsonSchemas as schemas
import APIs.Keypad.JsonSchemas as keypadApi
from event import Event
import events as Evts
from configuration import Configuration
from APIClient.APIEndpointClient import APIEndpointClient
from APIClient.HTTPStatusCode import HTTPStatusCode
from APIClient.MIMEType import MIMEType

class AlarmState(enum.Enum):
    """ Enumeration representing the different states of an alarm system. """

    DEACTIVATED = 0
    """
    Alarm state: alarm is deactivated.
    """

    ACTIVATED = 1
    """
    Alarm state: alarm is activated.
    """

    TRIGGERED = 2
    """
    Alarm state: alarm is triggered.
    """

@dataclasses.dataclass(slots=True)
class StateManagerState:
    """
    A data class that manages the state of an alarm system.

    Attributes:
        current_alarm_state (str): The current state of the alarm (default is
                                    an empty string).
        failed_entry_attempts (int): The number of failed entry attempts
                                      (default is 0).
        transient_states (list): A list of transient states (default is an
                                  empty list).
        unable_to_conn_error_displayed (bool): Flag indicating if the unable
                                                to connect error is displayed
                                                (default is False).
    """
    current_alarm_state: AlarmState = \
        dataclasses.field(default=AlarmState.DEACTIVATED)
    failed_entry_attempts: int = dataclasses.field(default=0)
    transient_states: list = dataclasses.field(default_factory=list)
    unable_to_conn_error_displayed: bool = dataclasses.field(default=False)

class StateManager:
    """ Implementation of alarm state management class. """
    __slots__ = ["_database", "_event_mgr", "_keypad_api_client",
                 "_logger", "_state"]

    def __init__(self, controller_db, event_mgr,
                 logger: logging.Logger):
        """
        StateManager class default constructor.

        Arguments:
            controller_db: Database controller interface instance.
            event_mgr: Event manager instance.
            logger: Logger instance.
        """
        self._state : StateManagerState = StateManagerState()
        self._database = controller_db
        self._event_mgr = event_mgr
        self._logger = logger.getChild(__name__)
        self._keypad_api_client = APIEndpointClient(
            Configuration().keypad_controller_endpoint)

    def rcv_keypad_event(self, event) -> None:
        """
        Handles an event received from a keypad.

        If the event is of type KeypadKeyCodeEntered, it delegates the handling to the
        _handle_key_code_entered_event method.

        Args:
            event (Event): The event object received from the keypad.
        """
        if event.event_id == Evts.EvtType.KeypadKeyCodeEntered:
            self._handle_key_code_entered_event(event)

    def rcv_device_event(self, event: Event) -> None:
        """
        Handles an event received from a device.

        If the event is of type SensorDeviceStateChange, it delegates the handling to the
        _handle_sensor_device_state_change_event method.

        Args:
            event (Event): The event object received from the device.
        """
        if event.event_id == Evts.EvtType.SensorDeviceStateChange:
            self._handle_sensor_device_state_change_event(event)

    def send_alive_ping_msg(self, event: Event) -> None:
        """
        Attempt to send an 'Alive Ping' message to the keypad, this is done
        when the keypad needs waking up after a system boot.

        Args:
            event (Event): The event object received.
        """
        additional_headers = {
            'authorisationKey': Configuration().general_authentication_key
        }

        response = self._keypad_api_client.SendPostMsg(
            'receiveCentralControllerPing',
            MIMEType.JSON,
            additional_headers, {})

        if response is None:
            if not self._state.unable_to_conn_error_displayed:
                self._logger.info("Unable to communicate with keypad, " +\
                                  "reason : %s",
                                  self._keypad_api_client.LastErrMsg)
                self._event_mgr.QueueEvent(event)
                self._state.unable_to_conn_error_displayed = True
            return

        # 401 Unauthenticated : Missing authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            self._logger.critical("Keypad cannot send AlivePing as the " + \
                                  "authorisation key is missing")
            return

        # 403 forbidden : Invalid authentication key.
        if response.status_code == HTTPStatusCode.Forbidden:
            self._logger.critical("Keypad cannot send AlivePing as the " +\
                                  "authorisation key is incorrect")
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:
            self._logger.info("Successfully send 'AlivePing' to keypad " +\
                              "controller")

        self._state.unable_to_conn_error_displayed = False

    def send_keypad_locked_msg(self, event):
        additional_headers = {
            'authorisationKey': Configuration().general_authentication_key
        }
        json_body = json.dumps(event.body)
        response = self._keypad_api_client.SendPostMsg('receiveKeypadLock',
                                                       MIMEType.JSON,
                                                       additional_headers,
                                                       json_body)

        if response is None:
            self._logger.info("Keypad locked msg : Unable to communicate " +\
                              "with keypad, reason : %s",
                              self._keypad_api_client.LastErrMsg)
            self._event_mgr.QueueEvent(event)
            return

        # 401 Unauthenticated : Missing authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            self._logger.critical("Keypad locked msg : Cannot send the " +\
                                  "AlivePing as the authorisation key " +\
                                  "is missing")
            return

        # 403 forbidden : Invalid authentication key.
        if response.status_code == HTTPStatusCode.Forbidden:
            self._logger.critical("Keypad locked msg : Authorisation " +\
                                  "key is incorrect")
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:
            self._logger.info("Successfully sent 'Keypad locked msg' to " +\
                              "keypad controller")

    #  @param self The object pointer.
    def update_transitory_events(self):

        # List of event id's that need to be removed
        id_list = []

        ## Transitory events go here....

        # Final stage is to remove all any of the transactions that have been
        # marked for removal.
        if id_list:
            self._state.transient_states = [evt for evt in
                                            self._state.transient_states
                                            if evt.event_id not in id_list]

    ## Function to handle a a keycode has been entered.
    #  @param self The object pointer.
    #  @param eventInst The event that contains a keycode.
    def _handle_key_code_entered_event(self, event):
        body = event.body

        key_sequence = body[schemas.ReceiveKeyCode.BodyElement.KeySeq]
        print("Key Seq", key_sequence)

        # Read the key code detail from the database.
        details = self._database.get_keycode_details(key_sequence)
        print("DETAILS: ", details)

        if details is not None:
            if self._state.current_alarm_state == AlarmState.TRIGGERED:
                self._logger.info("A triggered alarm has been deactivated")
                self._state.current_alarm_state = AlarmState.DEACTIVATED
                self._state.failed_entry_attempts = 0
                evt = Event(Evts.EvtType.DeactivateSiren, None)
                self._event_mgr.QueueEvent(evt)
                self._deactivate_alarm()

            elif self._state.current_alarm_state == AlarmState.DEACTIVATED:
                self._logger.info("The alarm has been activated")
                self._state.current_alarm_state = AlarmState.ACTIVATED
                self._state.failed_entry_attempts = 0
                self._trigger_alarm()

            elif self._state.current_alarm_state == AlarmState.ACTIVATED:
                self._logger.info("The alarm has been deactivated")
                self._state.current_alarm_state = AlarmState.DEACTIVATED
                self._state.failed_entry_attempts = 0
                self._deactivate_alarm()

        else:
            self._logger.info("An invalid key code was entered on keypad")
            self._state.failed_entry_attempts += 1

            attempts = self._state.failed_entry_attempts

            # If the attempt failed then send the response of type
            # receiveKeyCodeResponseAction_KeycodeIncorrect along with any
            # response actions that have been defined in the configuration
            # file.
            responses = Configuration().get_failed_attempt_responses()
            if attempts in responses:
                responses = responses[attempts]

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
                        if self._current_alarm_state != AlarmState.TRIGGERED:
                            self._logger.info("|=> Alarm has been triggered!")
                            self._trigger_alarm(no_grace_time=True)

                    elif response == 'resetAttemptAccount':
                        self._state.failed_entry_attempts = 0

    def _trigger_alarm(self, no_grace_time=False):
        """ Function to handle the alarm being triggered. """

        self._state.current_alarm_state = AlarmState.ACTIVATED

        alarm_set_evt_body = {
            'activationTimestamp': time.time(),
            'noGraceTime': no_grace_time
        }

        activate_event = Event(Evts.EvtType.AlarmActivated, alarm_set_evt_body)
        self._event_mgr.QueueEvent(activate_event)

    def _deactivate_alarm(self):
        """ Function to handle the alarm being deactivated. """

        self._state.current_alarm_state = AlarmState.DEACTIVATED
        self._state.failed_entry_attempts = 0

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
        if self._state.current_alarm_state == AlarmState.DEACTIVATED:
            self._logger.info("%s was %s, although alarm isn't on",
                              device_name, state_str)
            return

        # If the trigger has already been triggered then opening or closing
        # a door etc. would change the alarm state, although we should log that
        # the event has occurred.
        if self._state.current_alarm_state == AlarmState.TRIGGERED:
            self._logger.info("%s was %s, alarm already triggered",
                              device_name, state_str)
            return

        if self._state.current_alarm_state == AlarmState.ACTIVATED:
            self._logger.info("Activity on %s %s has triggerd the alarm!",
                              device_name, state_str)
            self._state.current_alarm_state = AlarmState.TRIGGERED

            evt = Event(Evts.EvtType.ActivateSiren, None)
            self._event_mgr.QueueEvent(evt)
