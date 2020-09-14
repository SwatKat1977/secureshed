'''
Copyright 2019-2020 Secure Shed Project Dev Team

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
import time
from twisted.internet import reactor
from common.APIClient.APIEndpointClient import APIEndpointClient
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from common.Logger import LogType
from Gui.KeypadPanel import KeypadPanel
from Gui.LockedPanel import LockedPanel
from Gui.CommsLostPanel import CommsLostPanel


class KeypadStateObject:
    # pylint: disable=too-many-instance-attributes

    __slots__ = ['_central_ctrl_api_client', '_comms_lost_panel', '__config',
                 '_current_panel', '_keypad_code', '_keypad_locked_panel',
                 '_keypad_panel', '_last_reconnect_time', '_logger',
                 '_new_panel']

    CommLostRetryInterval = 5

    class PanelType(enum.Enum):
        KeypadIsLocked = 0
        CommunicationsLost = 1
        Keypad = 2

    @property
    def new_panel(self):
        return self._new_panel

    @new_panel.setter
    def new_panel(self, new_panel_type):
        self._new_panel = new_panel_type

    @property
    def current_panel(self):
        return self._current_panel


    def __init__(self, config, logger):
        self.__config = config
        self._current_panel = (None, None)
        self._new_panel = (self.PanelType.CommunicationsLost, {})
        self._keypad_code = ''
        self._logger = logger

        self._comms_lost_panel = CommsLostPanel(self.__config)
        self._keypad_locked_panel = LockedPanel(self.__config)
        self._keypad_panel = KeypadPanel(self.__config)

        self._last_reconnect_time = 0

        endpoint = self.__config.centralController.endpoint
        self._central_ctrl_api_client = APIEndpointClient(endpoint)


    ## Function that is called to check if the panel has changed or needs to
    ## be changed (e.g. keypad lock expired).
    #  @param self The object pointer.
    def check_panel(self):
        if self._current_panel[0] != self._new_panel[0]:
            self._current_panel = self._new_panel
            self._update_displayed_panel()
            return

        # If the keypad is currently locked then we need to check to see if
        # the keypad lock has timed out, if it has then reset the panel.
        if self._current_panel[0] == KeypadStateObject.PanelType.KeypadIsLocked:
            curr_time = time.time()

            if curr_time >= self._current_panel[1]:
                keypad_panel = (KeypadStateObject.PanelType.Keypad, {})
                self._current_panel = keypad_panel
                self._update_displayed_panel()

            return

        # If the current panel is 'communications lost' then try to send a
        # please respond message to the central controller only at the alotted
        # intervals.
        if self._current_panel[0] == KeypadStateObject.PanelType.CommunicationsLost:
            curr_time = time.time()

            if curr_time > self._last_reconnect_time + self.CommLostRetryInterval:
                self._last_reconnect_time = curr_time
                reactor.callFromThread(self._send_please_respond_msg)


    #  @param self The object pointer.
    def _send_please_respond_msg(self):

        additional_headers = {
            'authorisationKey' : self.__config.centralController.authKey
        }

        response = self._central_ctrl_api_client.SendPostMsg(
            'pleaseRespondToKeypad', MIMEType.JSON, additional_headers)

        if response is None:
            self._logger.Log(LogType.Warn,
                             'failed to transmit, reason : %s',
                             self._central_ctrl_api_client.LastErrMsg)
            return

        # 400 Bad Request : Missing or invalid json body or validation failed.
        if response.status_code == HTTPStatusCode.BadRequest:
            self._logger.Log(LogType.Warn,
                             'failed to transmit, reason : BadRequest')
            return

        # 401 Unauthenticated : Missing or invalid authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            self._logger.Log(LogType.Warn,
                             'failed to transmit, reason : Unauthenticated')
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:
            return


    ## Display a new panel by firstly hiding all of panels and then after that
    ## show just the expected one.
    #  @param self The object pointer.
    def _update_displayed_panel(self):
        self._comms_lost_panel.Hide()
        self._keypad_panel.Hide()
        self._keypad_locked_panel.Hide()

        panel, _ = self._current_panel

        if panel == KeypadStateObject.PanelType.KeypadIsLocked:
            self._keypad_locked_panel.Display()

        elif panel == KeypadStateObject.PanelType.CommunicationsLost:
            self._comms_lost_panel.Display()

        elif panel == KeypadStateObject.PanelType.Keypad:
            self._keypad_panel.Display()

        # The displayed panel has changed, we can now reset newPanel.
        self._new_panel = self._current_panel
