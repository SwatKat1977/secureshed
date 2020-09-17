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
from Gui.ConsoleLogsPanel import ConsoleLogsPanel
from Gui.KeypadControllerConfigPanel import KeypadControllerConfigPanel


class KeypadControllerPanel(wx.Panel):

    RetrieveConsoleLogsPath = '/retrieveConsoleLogs'
    HealthStatusPath = '/_healthStatus'


    def __init__(self, parent, config):
        wx.Panel.__init__(self, parent)

        self._config = config
        self._apiClient = APIEndpointClient(config.keypadController.endpoint)
        self._logs = []
        self._logsLastMsgTimestamp = 0
        self._lastLogId = 0
        self._main_window = parent
        self._status = (False, '')

        topSplitter = wx.SplitterWindow(self)
        self._configPanel = KeypadControllerConfigPanel(topSplitter)
        self._logsPanel = ConsoleLogsPanel(topSplitter)
        topSplitter.SplitHorizontally(self._configPanel, self._logsPanel)
        topSplitter.SetSashGravity(0.5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(topSplitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def GetLogs(self):

        if not self._check_connection_status():
            return

        msg_body = {
            "startTimestamp" : self._logsLastMsgTimestamp
        }

        additional_headers = {
            'authorisationKey' : self._config.keypadController.authKey
        }

        response = self._apiClient.SendPostMsg(self.RetrieveConsoleLogsPath,
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

        msgBody = response.json()

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.
        try:
            jsonschema.validate(instance=msgBody,
                                schema=schemas.RequestLogsResponse.Schema)

        # Caught a message body validation failed, abort read.
        except jsonschema.exceptions.ValidationError:
            return

        self._UpdateLogEntries(msgBody)


    def _UpdateLogEntries(self, msgBody):
        bodyElements = schemas.RequestLogsResponse.BodyElement

        lastMsgTimestamp = msgBody[bodyElements.LastTimestamp]

        # If the last message timestamp is 0 then we have no new log messages.
        if lastMsgTimestamp == 0:
            return

        self._logsLastMsgTimestamp = lastMsgTimestamp

        for entry in msgBody[bodyElements.Entries]:
            timestamp = entry[bodyElements.EntryTimestamp]
            timestampStr = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

            msg = f"{timestampStr} {entry[bodyElements.EntryMessage]}"

            self._logsPanel.AddLogEntry(self._lastLogId,
                                        entry[bodyElements.EntryMsgLevel], msg)
            self._lastLogId += 1


    def _check_connection_status(self):

        curr_status = self._status

        additional_headers = {
            'authorisationKey' : self._config.keypadController.authKey
        }

        response = self._apiClient.SendGetMsg(self.HealthStatusPath,
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
