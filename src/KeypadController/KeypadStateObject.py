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


class KeypadStateObject:
    __slots__ = ['__currentPanel', '__keypadCode', '__processingQueue']

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
    def currentPanel(self):
        return self.__currentPanel

    @currentPanel.setter
    def currentPanel(self, newPanelType):
        self.__currentPanel = newPanelType
        self.__processingQueue.put(newPanelType)


    @property
    def processingQueue(self):
        return self.__processingQueue

    @processingQueue.setter
    def processingQueue(self, processingQueue):
        self.__processingQueue = processingQueue


    def __init__(self):
        self.__keypadCode = ''
        self.__currentPanel = (self.PanelType.CommunicationsLost, {})
        self.__processingQueue = None
