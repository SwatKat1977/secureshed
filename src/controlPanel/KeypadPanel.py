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
import wx


## Panel that implements a numbered keypad.
class KeypadPanel(wx.Panel):

    ## Sequence timeout in seconds.
    SequenceTimeout = 5


	## KeypadPanel class constructor.
	#  @param self The object pointer.
	#  @param parent Parent of the wxPython panel.
    def __init__(self, parent):
        super().__init__(parent)
        
        # Key sequence pressed.
        self.__keySequence = ''
        
        # Create sequence timer object and bind the timeout event.
        self.__sequenceTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.__TimeoutEvent, self.__sequenceTimer)
 
        self.__CreateUI()


	## Create the keypad user interface.
	#  @param self The object pointer.
    def __CreateUI(self):
        # Sizer that all of the buttons will be place into.
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL)

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
                button = wx.Button(self, label=label)
                btn_sizer.Add(button, 1, wx.ALIGN_CENTER|wx.EXPAND, 0)

                if label == 'GO':
                    button.Bind(wx.EVT_BUTTON, self.__TryTransmittingKeyCode)

                elif label == 'Reset':
                    button.Bind(wx.EVT_BUTTON, self.__ClearKeypad)

                else:
                    button.Bind(wx.EVT_BUTTON, self.__PressKey)

            main_sizer.Add(btn_sizer, 1, wx.ALIGN_CENTER|wx.EXPAND)

        self.SetSizer(main_sizer)


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

        if len(self.__keySequence) == 0:
            print('[DEBUG] First key in sequence, starting timer...')
            self.__sequenceTimer.Start(self.SequenceTimeout * 1000)

        self.__keySequence = self.__keySequence + pressedKeyValue

 
    def __ClearKeypad(self, event):
        self.__keySequence = ''


	## Try to transmit the entered key sequence to the alarm master controller.
	#  The code will only be transmitted if 1 or more keys were pressed, also
	#  on transmission the sequence timer is stopped and sequence reset.
	#  @param self The object pointer.
	#  @param event Unused.
    def __TryTransmittingKeyCode(self, event):
        if len(self.__keySequence) == 0:
            return

        print(f"[DEBUG] Transmitting key sequence '{self.__keySequence}'")
        self.__ClearKeypad(None)
        self.__sequenceTimer.Stop()        


	## Timer timeout event function.  This will cause any stored key sequence
	#  to be cleared and the timer stopped, ready for when the next key is
	#  pressed.
	#  @param self The object pointer.
	#  @param event Unused.
    def __TimeoutEvent(self, event):
        print("[DEBUG] Keypad sequence has timed out...'")
        self.__ClearKeypad(None)
        self.__sequenceTimer.Stop()
