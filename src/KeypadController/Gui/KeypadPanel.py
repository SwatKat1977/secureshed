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
from common.APIClient.APIEndpointClient import APIEndpointClient
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
import APIs.Keypad.JsonSchemas as JsonSchemas
from APIs.Keypad.ReceiveKeyCodeReturnCode import ReceiveKeyCodeReturnCode


## Panel that implements a numbered keypad.
class KeypadPanel(wx.Panel):

    ## Sequence timeout in seconds.
    SequenceTimeout = 5


    ## KeypadPanel class constructor.
    #  @param self The object pointer.
    #  @param parent Parent of the wxPython panel.
    #  @param configuration Configuration items.
    def __init__(self, parent, configuration):
        super().__init__(parent)

        self.__config = configuration

        # The central controller requires a secret authorisation key, this is
        # sent as part of the request header and is defined as part of the
        # configuration file.
        self.__authorisationKey = self.__config.centralController.authKey

        self.__keypadDisableTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.__KeypadDisabledTimedOut,
                  self.__keypadDisableTimer)

        endpoint = self.__config.centralController.endpoint
        self.__APIClient = APIEndpointClient(endpoint)

        # Key sequence pressed.
        self.__keySequence = ''

        # Create sequence timer object and bind the timeout event.
        self.__sequenceTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.__TimeoutEvent, self.__sequenceTimer)

        self.__CreateUserInterface()


    ## Create the keypad user interface.
    #  @param self The object pointer.
    def __CreateUserInterface(self):
        # Sizer that all of the buttons will be place into.
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        #font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL)

        self.__buttonsList = {}
        self.__defaultButtonDetails = {}

        # Array with the order and labels for the buttons.  There are two
        # special buttons:
        # * Go - enters the passcode that has typed in.
        # * Reset - Resets the sequence entered.
        buttons = [['7', '8', '9'],
                   ['4', '5', '6'],
                   ['1', '2', '3'],
                   ['0', 'GO', 'Reset']]

        for labelList in buttons:
            btnSizer = wx.BoxSizer()
            for label in labelList:
                button = wx.Button(self, label=label)
                btnSizer.Add(button, 1, wx.ALIGN_CENTER|wx.EXPAND, 0)
                self.__buttonsList[button] = button

                self.__defaultButtonDetails[button] = \
                {
                    'backgroundColour' : button.GetBackgroundColour(),
                    'label' : label
                }

                if label == 'GO':
                    button.Bind(wx.EVT_BUTTON, self.__TryTransmittingKeyCode)

                elif label == 'Reset':
                    button.Bind(wx.EVT_BUTTON, self.__ResetKeypad)

                else:
                    button.Bind(wx.EVT_BUTTON, self.__PressKey)

            mainSizer.Add(btnSizer, 1, wx.ALIGN_CENTER|wx.EXPAND)

        self.SetSizer(mainSizer)


    ## A key is pressed event handler.  If this is the 1st key in the sequence
    #  then start a timer which is your allotted time to enter the right values
    #  before they are cleared.  All of the keypresses are stored internally,
    #  ready for transmission.
    #  @param self The object pointer.
    #  @param event Key pressed event object.
    def __PressKey(self, event):

        # Get the event object for the key pressed.
        pressedKey = event.GetEventObject()
        pressedKeyValue = pressedKey.GetLabel()

        if not self.__keySequence:
            self.__sequenceTimer.Start(self.SequenceTimeout * 1000)

        self.__keySequence = self.__keySequence + pressedKeyValue


    ## Reset the keypad, which involves clearing key sequence.
     #  @param self The object pointer.
     #  @param event Unused.
    def __ResetKeypad(self, event=None):
        # pylint: disable=W0613

        self.__keySequence = ''


    ## Try to transmit the entered key sequence to the alarm master controller.
    #  The code will only be transmitted if 1 or more keys were pressed, also
    #  on transmission the sequence timer is stopped and sequence reset.
    #  @param self The object pointer.
    #  @param event Unused.
    def __TryTransmittingKeyCode(self, event):
        # pylint: disable=W0613

        additionalHeaders = {
            'authorisationKey' : self.__authorisationKey
        }

        if not self.__keySequence:
            return

        keySeq = self.__keySequence

        body = {"keySequence": self.__keySequence}
        jsonBody = json.dumps(body)

        self.__TimeoutEvent()

        response = self.__APIClient.SendPostMsg('receiveKeyCode',
                                                MIMEType.JSON,
                                                additionalHeaders,
                                                jsonBody)

        if not response:
            print(f'failed to transmit, reason : {self.__APIClient.LastErrMsg}')
            return

        # 400 Bad Request : Missing or invalid json body or validation failed.
        if response.status_code == HTTPStatusCode.BadRequest:
            # TODO : Add a log message here
            return

        # 401 Unauthenticated : Missing or invalid authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            # TODO : Add a log message here
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:

            print(f'REsponse text: {response.text}')
            print(f'--> KeycodeAccepted: {ReceiveKeyCodeReturnCode.KeycodeAccepted.value}')
            print(f'REsponse text: {response.text}')

            responseText = json.loads(response.text)

            code = responseText[JsonSchemas.receiveKeyCodeResponse.ReturnCode]

            if code == ReceiveKeyCodeReturnCode.KeycodeAccepted.value:
                self.__HandleKeycodeAcceptedActions(
                    responseText[JsonSchemas.receiveKeyCodeResponse.Actions])

            elif code == ReceiveKeyCodeReturnCode.KeycodeIncorrect.value:
                self.__HandleKeycodeIncorrectActions(
                    responseText[JsonSchemas.receiveKeyCodeResponse.Actions])

            elif code == ReceiveKeyCodeReturnCode.KeycodeRefused.value:
                self.__HandleKeycodeRefusedActions(
                    responseText[JsonSchemas.receiveKeyCodeResponse.Actions])


    ## Timer timeout event function.  This will cause any stored key sequence
    #  to be cleared and the timer stopped, ready for when the next key is
    #  pressed.
    #  @param self The object pointer.
    #  @param event Unused.
    def __TimeoutEvent(self, event=None):
        # pylint: disable=W0613

        self.__ResetKeypad()
        self.__sequenceTimer.Stop()


    ## Currently we don't do anything with this action except write a debug
    #  message.
    #  @param self The object pointer.
    #  @param actions Actions when refused.
    def __HandleKeycodeRefusedActions(self, actions):
        print('[DEBUG] The keycode was refused!')


    #  @param self The object pointer.
    #  @param actions Actions when keycode is incorrect.
    def __HandleKeycodeIncorrectActions(self, actions):
        print('[DEBUG[ Incorrect keycode event..')

        for a in actions:
            if a == JsonSchemas.receiveKeyCodeResponseAction_KeycodeRefused.\
                DisableKeypad:
                self.DisableKeypad(actions[a])


    ## STUB
    #  @param self The object pointer.
    #  @param actions Unused.
    def __HandleKeycodeAcceptedActions(self, actions):
        # pylint: disable=W0613
        print('KeycodeAccepted')


    ## Disable Keypad wxTimer has timed out event, re-enable the keypad by
    #  reverting all of the changes made during disabling of it.
    #  @param self The object pointer.
    #  @param unused Required parameter for wxTimer but not used.
    def __KeypadDisabledTimedOut(self, unused=None):
        self.__keypadDisableTimer.Stop()

        for button, defaultValues in self.__defaultButtonDetails.items():
            button.Enable()
            button.SetBackgroundColour(defaultValues['backgroundColour'])
            button.SetLabel(defaultValues['label'])


    ## Disable the keypad by setting all the buttons to disabled, changing the
    #  background to red and removing labels.
    #  @param self The object pointer.
     #  @param timeoutSecs Time (seconds) of how long keypad is disabled.
    def DisableKeypad(self, timeoutSecs):
        for _, button in self.__buttonsList.items():
            button.Disable()
            button.SetBackgroundColour((212, 13, 13))
            button.SetLabel('')

        self.__keypadDisableTimer.Start(timeoutSecs * 1000)
