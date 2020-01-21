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
from Gui.KeypadPanel import KeypadPanel
from Gui.LockedPanel import LockedPanel
from Gui.CommsLostPanel import CommsLostPanel


class KeypadStateObject:
    __slots__ = ['__centralCtrlApiClient', '__config', '__currentPanel',
                 '__keypadCode', '__logger', '__newPanel', '__commsLostPanel',
                 '__keypadLockedPanel', '__keypadPanel', '__lastReconnectTime']

    CommLostRetryInterval = 5

    class PanelType(enum.Enum):
        KeypadIsLocked = 0
        CommunicationsLost = 1
        Keypad = 2

    @property
    def keypadCode(self):
        return self.__keypadCode

    @keypadCode.setter
    def keypadCode(self, newCode):
        self.__keypadCode = newCode

    @property
    def newPanel(self):
        return self.__newPanel

    @newPanel.setter
    def newPanel(self, newPanelType):
        self.__newPanel = newPanelType

    @property
    def currentPanel(self):
        return self.__currentPanel


    def __init__(self, config, logger):
        self.__config = config
        self.__currentPanel = (None, None)
        self.__newPanel = (self.PanelType.CommunicationsLost, {})
        self.__keypadCode = ''

        self.__commsLostPanel = CommsLostPanel(self.__config)
        self.__keypadLockedPanel = LockedPanel(self.__config)
        self.__keypadPanel = KeypadPanel(self.__config)

        self.__lastReconnectTime = 0

        self.__logger = logger

        endpoint = self.__config.centralController.endpoint
        self.__centralCtrlApiClient = APIEndpointClient(endpoint)


    ## Function that is called to check if the panel has changed or needs to
    ## be changed (e.g. keypad lock expired).
    #  @param self The object pointer.
    def CheckPanel(self):
        if self.__currentPanel[0] != self.__newPanel[0]:
            self.__currentPanel = self.__newPanel
            self.__UpdateDisplayedPanel()
            return

        # If the keypad is currently locked then we need to check to see if
        # the keypad lock has timed out, if it has then reset the panel.
        if self.__currentPanel[0] == KeypadStateObject.PanelType.KeypadIsLocked:
            currTime = time.time()

            if currTime >= self.__currentPanel[1]:
                keypadPanel = (KeypadStateObject.PanelType.Keypad, {})
                self.__currentPanel = keypadPanel
                self.__UpdateDisplayedPanel()

            return

        # If the current panel is 'communications lost' then try to send a
        # please respond message to the central controller only at the alotted
        # intervals.
        if self.__currentPanel[0] == KeypadStateObject.PanelType.CommunicationsLost:
            curTime = time.time()
            if curTime > self.__lastReconnectTime + self.CommLostRetryInterval:
                self.__lastReconnectTime = curTime
                reactor.callFromThread(self.__SendPleaseRespondMsg)


    #  @param self The object pointer.
    def __SendPleaseRespondMsg(self):

        additionalHeaders = {
            'authorisationKey' : self.__config.centralController.authKey
        }

        response = self.__centralCtrlApiClient.SendPostMsg(
            'pleaseRespondToKeypad', MIMEType.JSON, additionalHeaders)

        if response is None:
            self.__logger.warn('failed to transmit, reason : %s',
                               self.__centralCtrlApiClient.LastErrMsg)
            return

        # 400 Bad Request : Missing or invalid json body or validation failed.
        if response.status_code == HTTPStatusCode.BadRequest:
            self.__logger.warn('failed to transmit, reason : BadRequest')
            return

        # 401 Unauthenticated : Missing or invalid authentication key.
        if response.status_code == HTTPStatusCode.Unauthenticated:
            self.__logger.warn('failed to transmit, reason : Unauthenticated')
            return

        # 200 OK : code accepted, code incorrect or code refused.
        if response.status_code == HTTPStatusCode.OK:
            return


    ## Display a new panel by firstly hiding all of panels and then after that
    ## show just the expected one.
    #  @param self The object pointer.
    def __UpdateDisplayedPanel(self):
        self.__commsLostPanel.Hide()
        self.__keypadPanel.Hide()
        self.__keypadLockedPanel.Hide()

        panel, _ = self.__currentPanel

        if panel == KeypadStateObject.PanelType.KeypadIsLocked:
            self.__keypadLockedPanel.Display()

        elif panel == KeypadStateObject.PanelType.CommunicationsLost:
            self.__commsLostPanel.Display()

        elif panel == KeypadStateObject.PanelType.Keypad:
            self.__keypadPanel.Display()

        # The displayed panel has changed, we can now reset newPanel.
        self.__newPanel = self.__currentPanel
