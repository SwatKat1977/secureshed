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
import json
import wx
from twisted.internet import reactor
from common.APIClient.APIEndpointClient import APIEndpointClient
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType


## Panel that implements a numbered keypad.
class KeypadPanel(wx.Frame):
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes

    ## Sequence timeout in seconds.
    SequenceTimeout = 5


    ## KeypadPanel class constructor.
    #  @param self The object pointer.
    #  @param config Configuration items.
    def __init__(self, config):
        frame_size = (config.gui.windowWidth,
                     config.gui.windowHeight)
        super().__init__(None, title="", size=frame_size)

        self._config = config

        # The central controller requires a secret authorisation key, this is
        # sent as part of the request header and is defined as part of the
        # configuration file.
        self._authorisation_ley = self._config.centralController.authKey

        self._panel = wx.Panel(self)

        endpoint = self._config.centralController.endpoint
        self._api_client = APIEndpointClient(endpoint)

        # Key sequence pressed.
        self._key_sequence = ''

        # Create sequence timer object and bind the timeout event.
        self._sequence_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._timeout_event, self._sequence_timer)

        self._create_user_interface()

        # make sure reactor.stop() is used to stop event loop
        self.Bind(wx.EVT_CLOSE, self._on_exit)


    def display(self):
        self.Show()
        if self._config.gui.fullscreen:
            self.ShowFullScreen(True)
            self.Maximize(True)


    ## Create the keypad user interface.
    #  @param self The object pointer.
    def _create_user_interface(self):
        # Sizer that all of the buttons will be place into.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        #font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL)

        self._buttons_list = {}
        self._default_button_details = {}

        # Array with the order and labels for the buttons.  There are two
        # special buttons:
        # * Go - enters the passcode that has typed in.
        # * Reset - Resets the sequence entered.
        buttons = [['7', '8', '9'],
                   ['4', '5', '6'],
                   ['1', '2', '3'],
                   ['0', 'GO', 'Reset']]

        for label_list in buttons:
            btn_sizer = wx.BoxSizer()
            for label in label_list:
                button = wx.Button(self._panel, label=label)
                btn_sizer.Add(button, 1, wx.EXPAND, 0)
                self._buttons_list[button] = button

                self._default_button_details[button] = \
                {
                    'backgroundColour' : button.GetBackgroundColour(),
                    'label' : label
                }

                if label == 'GO':
                    button.Bind(wx.EVT_BUTTON, self._try_transmitting_key_code)

                elif label == 'Reset':
                    button.Bind(wx.EVT_BUTTON, self._reset_keypad)

                else:
                    button.Bind(wx.EVT_BUTTON, self._press_key)

            main_sizer.Add(btn_sizer, 1, wx.EXPAND)

        self._panel.SetSizer(main_sizer)


    ## A key is pressed event handler.  If this is the 1st key in the sequence
    #  then start a timer which is your allotted time to enter the right values
    #  before they are cleared.  All of the keypresses are stored internally,
    #  ready for transmission.
    #  @param self The object pointer.
    #  @param event Key pressed event object.
    def _press_key(self, event):

        # Get the event object for the key pressed.
        pressed_key = event.GetEventObject()
        pressed_key_value = pressed_key.GetLabel()

        if not self._key_sequence:
            self._sequence_timer.Start(self.SequenceTimeout * 1000)

        self._key_sequence = self._key_sequence + pressed_key_value


    ## Reset the keypad, which involves clearing key sequence.
     #  @param self The object pointer.
     #  @param event Unused.
    def _reset_keypad(self, event=None):
        # pylint: disable=W0613

        self._key_sequence = ''


    ## Try to transmit the entered key sequence to the alarm master controller.
    #  The code will only be transmitted if 1 or more keys were pressed, also
    #  on transmission the sequence timer is stopped and sequence reset.
    #  @param self The object pointer.
    #  @param event Unused.
    def _try_transmitting_key_code(self, event):
        # pylint: disable=W0613

        additional_headers = {
            'authorisationKey' : self._authorisation_ley
        }

        if not self._key_sequence:
            return

        body = {"keySequence": self._key_sequence}
        json_body = json.dumps(body)

        self._timeout_event()

        response = self._api_client.SendPostMsg('receiveKeyCode',
                                                MIMEType.JSON,
                                                additional_headers,
                                                json_body)

        if response is None:
            print(f'failed to transmit, reason : {self._api_client.LastErrMsg}')
            return

        # 400 Bad Request : Missing or invalid json body or validation failed.
        if response.status_code == HTTPStatusCode.BadRequest:
            # [TODO] : Add a log message here
            print('failed to transmit, reason : BadRequest')
            return

        # 401 Unauthenticated : Missing or invalid authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            # [TODO] : Add a log message here
            print('failed to transmit, reason : Unauthenticated')
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:
            return


    ## Timer timeout event function.  This will cause any stored key sequence
    #  to be cleared and the timer stopped, ready for when the next key is
    #  pressed.
    #  @param self The object pointer.
    #  @param event Unused.
    def _timeout_event(self, event=None):
        # pylint: disable=W0613

        self._reset_keypad()
        self._sequence_timer.Stop()


    ## Exit event function when the application is closed.
    #  @param self The object pointer.
    #  @param event Unused, but required.
    def _on_exit(self, event):
        # pylint: disable=R0201
        # pylint: disable=W0613
        reactor.stop()
