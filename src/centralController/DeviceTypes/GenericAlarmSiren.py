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
from centralController.DeviceTypes.BaseDeviceType import BaseDeviceType
import centralController.Events as Evts
from common.Logger import Logger, LogType


class GenericAlarmSiren(BaseDeviceType):

    ExpectedPinId = 'sirenPin'


    def __init__(self, hardwareIO, eventMgr):
        self.__eventMgr = eventMgr
        self.__ioPin = None
        self.__hardwareIO = hardwareIO
        self.__isTriggered = False
        self.__deviceName = None


    def Initialise(self, deviceName, pins, additionalParams):
        self.__deviceName = deviceName

        pinPrefix = 'GPIO'

        # Expecting one pin.
        if len(pins) != 1:
            Logger.Instance().Log(LogType.Warn,
                                  "Device '%s' was expecting 1 pin, actually %s",
                                  deviceName, len(pins))
            return False

        pin = [pin for pin in pins if pin['identifier'] == self.ExpectedPinId]
        if not pin:
            Logger.Instance().Log(LogType.Warn,
                                  "Device '%s' missing expected pin '%s'",
                                  deviceName, self.ExpectedPinId)
            return False

        self.__ioPin = int(pin[0]['ioPin'][len(pinPrefix):])
        self.__hardwareIO.setup(self.__ioPin, self.__hardwareIO.OUT)
        self.__hardwareIO.output(self.__ioPin, self.__hardwareIO.HIGH)

        return True


    def CheckDevice(self):
        pass


    def ReceiveEvent(self, eventInst):
        if eventInst.id == Evts.EvtType.ActivateSiren:
            self.__hardwareIO.output(self.__ioPin, self.__hardwareIO.LOW)

        elif eventInst.id == Evts.EvtType.DeactivateSiren:
            self.__hardwareIO.output(self.__ioPin, self.__hardwareIO.HIGH)
