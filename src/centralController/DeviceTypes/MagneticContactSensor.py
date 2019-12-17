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
import time
from centralController.DeviceTypes.BaseDeviceType import BaseDeviceType
import centralController.Events as Evts
from common.Event import Event


class MagneticContactSensor(BaseDeviceType):

    def __init__(self, logger, hardwareIO, eventMgr):
        self.__eventMgr = eventMgr
        self.__logger = logger
        self.__ioPin = None
        self.__hardwareIO = hardwareIO
        self.__isTriggered = False
        self.__deviceName = None
        self.__graceTimeout = None
        self.__additionalParams = None


    ExpectedPinId = 'sensorPin'


    def Initialise(self, deviceName, pins, additionalParams):
        self.__deviceName = deviceName
        self.__additionalParams = additionalParams

        pinPrefix = 'GPIO'

        # Expecting one pin.
        if len(pins) != 1:
            self.__logger.warn("Device '%s' was expecting 1 pin, actually %s",
                               deviceName, len(pins))
            return False

        pin = [pin for pin in pins if pin['identifier'] == self.ExpectedPinId]
        if not pin:
            self.__logger.warn("Device '%s' missing expected pin '%s'",
                               deviceName, self.ExpectedPinId)
            return False

        self.__ioPin = int(pin[0]['ioPin'][len(pinPrefix):])
        self.__hardwareIO.setup(self.__ioPin, self.__hardwareIO.IN,
                                pull_up_down=self.__hardwareIO.PUD_UP)

        return True


    def CheckDevice(self):
        contactState = self.__hardwareIO.input(self.__ioPin)

        currTime = time.time()

        if self.__graceTimeout:
            if currTime <= self.__graceTimeout:
                self.__isTriggered = False
                return

            self.__graceTimeout = None

        if self.__isTriggered != contactState:
            self.__isTriggered = contactState

            stateMsg = "open" if contactState else "closed"
            self.__logger.info("Device '%s' changed state to %s",
                               self.__deviceName, stateMsg)

            evtBody = {
                Evts.SensorDeviceBodyItem.DeviceType: 'Magnetic Contact Sensor',
                Evts.SensorDeviceBodyItem.DeviceName: self.__deviceName,
                Evts.SensorDeviceBodyItem.State: self.__isTriggered
            }
            evt = Event(Evts.EvtType.SensorDeviceStateChange, evtBody)
            self.__eventMgr.QueueEvent(evt)


    def ReceiveEvent(self, eventInst):
        if eventInst.id == Evts.EvtType.AlarmActivated:
            if 'triggerGracePeriodSecs' in self.__additionalParams:
                graceSecs = self.__additionalParams['triggerGracePeriodSecs']
                self.__graceTimeout = eventInst.body['activationTimestamp'] +\
                    graceSecs
                self.__logger.debug("Alarm activated, device '%s' is in " +\
                    "grace period of %s seconds", self.__deviceName, graceSecs)
