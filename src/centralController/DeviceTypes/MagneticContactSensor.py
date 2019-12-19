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
import enum
import time
from centralController.DeviceTypes.BaseDeviceType import BaseDeviceType
import centralController.Events as Evts
from common.Event import Event


class MagneticContactSensor(BaseDeviceType):
    SensorName = 'Magnetic Contact Sensor'

    class GracePeriodType(enum.Enum):
        AlarmActivate = 0
        AlarmInactivate = 1
        AlarmSetPeriod = 2
        AlarmUnsetPeriod = 3


    #  @param self The object pointer.
    def __init__(self, logger, hardwareIO, eventMgr):
        self.__eventMgr = eventMgr
        self.__logger = logger
        self.__ioPin = None
        self.__hardwareIO = hardwareIO
        self.__isTriggered = False
        self.__deviceName = None
        self.__graceTimeout = None
        self.__additionalParams = None
        self.__gracePeriodType = self.GracePeriodType.AlarmInactivate


    ExpectedPinId = 'sensorPin'


    ## Initialise the magnetic contact sensor hardware device plug-in.
    #  @param self The object pointer.
    #  @param deviceName Name of device instance.
    #  @param pins Pin(s) layout.
    #  @param additionalParams Additional optional parameters for the device.
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


    ## Check the state of the device, e.g. has the state changed so that it is
    #  triggered etc.
    #  @param self The object pointer.
    def CheckDevice(self):
        contactState = self.__hardwareIO.input(self.__ioPin)

        transitionedFronSetState = False
        currTime = time.time()

        # If we are in the alarmed set grace period then the triggered flag is
        # not changable until the grace period has expired.  Once it has then
        # revert the grace period type which means if the sensor is in a
        # triggered state (open) then an alarm event is raised.
        if self.__gracePeriodType == self.GracePeriodType.AlarmSetPeriod:
            if currTime <= self.__graceTimeout:
                self.__isTriggered = False
                return

            self.__gracePeriodType = self.GracePeriodType.AlarmActivate
            transitionedFronSetState = True

        # If we are in the alarm unset period (if no action e.g. typing in the
        # right key code is entered then the alarm is triggered) then the
        # triggered flag is not changable until the grace period has expired or
        # the alarm has been acknowledged.  If after the grace period the alarm
        # hasn't been acknowledged the an alarm even is raised.
        elif self.__gracePeriodType == self.GracePeriodType.AlarmUnsetPeriod:
            if currTime <= self.__graceTimeout:
                self.__isTriggered = False
                return

            self.__logger.debug("Device '%s' grace period ended...",
                                self.__deviceName)
            self.__gracePeriodType = self.GracePeriodType.AlarmActivate
            transitionedFronSetState = True

        if self.__isTriggered != contactState:
            graceSecs = self.__additionalParams['triggerGracePeriodSecs']
            if contactState and not transitionedFronSetState and graceSecs and \
                    self.__gracePeriodType == self.GracePeriodType.AlarmActivate:
                self.__gracePeriodType = self.GracePeriodType.AlarmUnsetPeriod
                self.__logger.info("Device '%s' sensor triggered, entered " +\
                    "grace period of %s seconds", self.__deviceName, graceSecs)
                self.__graceTimeout = time.time() + graceSecs

            else:
                self.__isTriggered = contactState

                stateMsg = "open" if contactState else "closed"
                self.__logger.info("Device '%s' changed state to %s",
                                   self.__deviceName, stateMsg)
                self.__GenerateDeviceStateChangeEvt()


    ## Recieve events from the event manager, these include the change of the
    #  the alarms state (activate/deactivated etc.).
    #  @param self The object pointer.
    def ReceiveEvent(self, eventInst):
        if eventInst.id == Evts.EvtType.AlarmActivated:
            if 'triggerGracePeriodSecs' in self.__additionalParams:
                graceSecs = self.__additionalParams['triggerGracePeriodSecs']
                self.__graceTimeout = eventInst.body['activationTimestamp'] +\
                    graceSecs
                self.__logger.info("Alarm activated, device '%s' is in " +\
                    "grace period of %s seconds", self.__deviceName, graceSecs)
                self.__gracePeriodType = self.GracePeriodType.AlarmSetPeriod

        elif eventInst.id == Evts.EvtType.AlarmDeactivated:
            self.__gracePeriodType = self.GracePeriodType.AlarmInactivate


    ## Generate and queue the event when a device state changes.
    #  @param self The object pointer.
    def __GenerateDeviceStateChangeEvt(self):
        evtBody = {
            Evts.SensorDeviceBodyItem.DeviceType: self.SensorName,
            Evts.SensorDeviceBodyItem.DeviceName: self.__deviceName,
            Evts.SensorDeviceBodyItem.State: self.__isTriggered
        }
        evt = Event(Evts.EvtType.SensorDeviceStateChange, evtBody)
        self.__eventMgr.QueueEvent(evt)
