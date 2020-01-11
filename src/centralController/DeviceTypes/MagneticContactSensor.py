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


## Implementation of generic magnetic contact sensor device which supports
## a configurable grace period if the state changes.
class MagneticContactSensor(BaseDeviceType):
    SensorName = 'Magnetic Contact Sensor'

    ExpectedPinId = 'sensorPin'

    class StateType(enum.Enum):
        AlarmActivate = 0
        AlarmInactive = 1
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
        self.__stateType = self.StateType.AlarmInactive


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

        # If we are in the alarmed set grace period then the triggered flag is
        # not changable until the grace period has expired.  Once it has then
        # revert the grace period type which means if the sensor is in a
        # triggered state (open) then an alarm event is raised.
        if self.__stateType == self.StateType.AlarmSetPeriod:
            self.__HandleAlarmSetGracePeriod(contactState)

        # If we are in the alarm unset period (if no action e.g. typing in the
        # right key code is entered then the alarm is triggered) then the
        # triggered flag is not changable until the grace period has expired or
        # the alarm has been acknowledged.  If after the grace period the alarm
        # hasn't been acknowledged the an alarm even is raised.
        elif self.__stateType == self.StateType.AlarmUnsetPeriod:
            self.__HandleAlarmUnsetGracePeriod()

        else:
            # The alarm has been triggered, don't change the state or allow the
            # the grace period to be updated so just return out of function.
            if self.__isTriggered:
                return

            if self.__isTriggered != contactState:
                stateMsg = "opened" if contactState else "closed"

                # If the alarm is inactive then just change state change.
                if self.__stateType == self.StateType.AlarmInactive:
                    self.__logger.info("Device '%s' was %s",
                                       self.__deviceName, stateMsg)
                    self.__isTriggered = contactState
                    return

                graceSecs = self.__additionalParams['triggerGracePeriodSecs']
                if graceSecs:
                    self.__stateType = self.StateType.AlarmUnsetPeriod
                    self.__logger.info("Device '%s' sensor triggered, entered " +\
                        "grace period of %s seconds", self.__deviceName, graceSecs)
                    self.__graceTimeout = time.time() + graceSecs

                else:
                    self.__isTriggered = contactState
                    self.__logger.info("Device '%s' was %s",
                                       self.__deviceName, stateMsg)
                    self.__GenerateDeviceStateChangeEvt()


    ## Recieve events from the event manager, these include the change of the
    #  the alarms state (activate/deactivated etc.).
    #  @param self The object pointer.
    #  @param eventInst Event instance.
    def ReceiveEvent(self, eventInst):
        if eventInst.id == Evts.EvtType.AlarmActivated:
            if 'triggerGracePeriodSecs' in self.__additionalParams:
                graceSecs = self.__additionalParams['triggerGracePeriodSecs']
                self.__graceTimeout = eventInst.body['activationTimestamp'] +\
                    graceSecs
                self.__logger.info("Alarm activated, device '%s' is in " +\
                    "grace period of %s seconds", self.__deviceName, graceSecs)
                self.__stateType = self.StateType.AlarmSetPeriod
            self.__isTriggered = False

        elif eventInst.id == Evts.EvtType.AlarmDeactivated:
            self.__stateType = self.StateType.AlarmInactive


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


    #  @param self The object pointer.
    def __HandleAlarmSetGracePeriod(self, contactState):
        currTime = time.time()

        # Still in grace period, thus __isTriggered flag currently cannot be
        # changed.
        if currTime <= self.__graceTimeout:
            return

        # The grace period has expired, change to the state 'AlarmActivate'
        # and then check the trigger state.
        self.__stateType = self.StateType.AlarmActivate
        self.__logger.info("Device '%s' alarm set grace period ended...",
                           self.__deviceName)

        if contactState:
            self.__logger.info("Device '%s' caused alarm to trigger",
                               self.__deviceName)
            self.__isTriggered = True
            self.__GenerateDeviceStateChangeEvt()


    #  @param self The object pointer.
    def __HandleAlarmUnsetGracePeriod(self):
        currTime = time.time()

        # Still in grace period, thus __isTriggered flag currently cannot be
        # changed.
        if currTime <= self.__graceTimeout:
            return

        # If we have come out of the grace period and the alarm hasn't been
        # deactivated during this time then trigger the alarm.
        self.__logger.info("Device '%s' alarm unset grace period ended, " + \
            "the alarm has been triggered!", self.__deviceName)
        self.__stateType = self.StateType.AlarmActivate
        self.__GenerateDeviceStateChangeEvt()
        self.__isTriggered = True
