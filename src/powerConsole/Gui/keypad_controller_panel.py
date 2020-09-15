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
from datetime import datetime
import json
import jsonschema
import wx
import APIs.Keypad.JsonSchemas as schemas
from common.APIClient.APIEndpointClient import APIEndpointClient
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from Gui.console_logs_panel import ConsoleLogsPanel
from Gui.keypad_controller_config_panel import KeypadControllerConfigPanel


class KeypadControllerPanel(wx.Panel):
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    RetrieveConsoleLogsPath = '/retrieveConsoleLogs'
    HealthStatusPath = '/_healthStatus'


    def __init__(self, parent, config):
        wx.Panel.__init__(self, parent)

        self._config = config
        self._api_client = APIEndpointClient(config.keypadController.endpoint)
        self._logs = []
        self._logs_last_msg_timestamp = 0
        self._last_log_id = 0
        self._main_window = parent
        self._status = (False, '')

        top_splitter = wx.SplitterWindow(self)
        self._config_panel = KeypadControllerConfigPanel(top_splitter)
        self._logs_panel = ConsoleLogsPanel(top_splitter)
        top_splitter.SplitHorizontally(self._config_panel, self._logs_panel)
        top_splitter.SetSashGravity(0.5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(top_splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def get_logs(self):

        if not self._check_connection_status():
            return

        msg_body = {
            "startTimestamp" : self._logs_last_msg_timestamp
        }

        additional_headers = {
            'authorisationKey' : self._config.keypadController.authKey
        }

        response = self._api_client.SendPostMsg(self.RetrieveConsoleLogsPath,
                                                MIMEType.JSON,
                                                additional_headers,
                                                json.dumps(msg_body))

        # Not able to communicated with the central controller.
        if response is None:
            # NOT able to communicate with central controller...
            return

        if response.status_code != HTTPStatusCode.OK:
            print("Communications error with central controller, " + \
                  f"status {response.status_code}")
            print(response.text)
            return

        msg_body = response.json()

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.
        try:
            jsonschema.validate(instance=msg_body,
                                schema=schemas.RequestLogsResponse.Schema)

        # Caught a message body validation failed, abort read.
        except jsonschema.exceptions.ValidationError:
            return

        self._update_log_entries(msg_body)


    def _update_log_entries(self, msg_body):
        body_elements = schemas.RequestLogsResponse.BodyElement

        last_msg_timestamp = msg_body[body_elements.LastTimestamp]

        # If the last message timestamp is 0 then we have no new log messages.
        if last_msg_timestamp == 0:
            return

        self._logs_last_msg_timestamp = last_msg_timestamp

        for entry in msg_body[body_elements.Entries]:
            timestamp = entry[body_elements.EntryTimestamp]
            timestamp_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

            msg = f"{timestamp_str} {entry[body_elements.EntryMessage]}"

            self._logs_panel.add_log_entry(self._last_log_id,
                                           entry[body_elements.EntryMsgLevel], msg)
            self._last_log_id += 1


    def _check_connection_status(self):

        additional_headers = {
            'authorisationKey' : self._config.keypadController.authKey
        }

        response = self._api_client.SendGetMsg(self.HealthStatusPath,
                                               MIMEType.JSON,
                                               additional_headers)

        # We are not able to communicate with the keypad controller...
        if response is None:
            self._update_status((False, 'No connection'))
            return False

        if response.status_code != HTTPStatusCode.OK:
            self._update_status((False, 'API Error'))
            return False

        # Initially hard-code to normal as it's hard-coded into the response.
        self._update_status((True, 'Normal'))
        return True


    def _update_status(self, new_status):
        curr_state, curr_str = self._status
        new_state, new_str = new_status

        # If no change at all we can leave now...
        if curr_state == new_state and curr_str == new_str:
            return

        if new_state:
            new_str = f'Connected: ({new_str})'
            self._main_window.update_keypad_status(new_str)

        else:
            new_str = f'Disconnected: ({new_str})'
            self._main_window.update_keypad_status(new_str)

        self._status = new_status
