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
from common.Logger import Logger, LogType


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
    def __init__(self, hardwareIO, eventMgr, logger):
        self._event_mgr = eventMgr
        self._io_pin = None
        self._hardware_io = hardwareIO
        self._is_triggered = False
        self._device_name = None
        self._grace_timeout = None
        self._additional_params = None
        self._logger = logger
        self._state_type = self.StateType.AlarmInactive


    ## Initialise the magnetic contact sensor hardware device plug-in.
    #  @param self The object pointer.
    #  @param deviceName Name of device instance.
    #  @param pins Pin(s) layout.
    #  @param additionalParams Additional optional parameters for the device.
    def Initialise(self, deviceName, pins, additionalParams):
        self._device_name = deviceName
        self._additional_params = additionalParams

        pinPrefix = 'GPIO'

        # Expecting one pin.
        if len(pins) != 1:
            self._logger.Log(LogType.Warn,
                             "Device '%s' was expecting 1 pin, actually %s",
                             deviceName, len(pins))
            return False

        pin = [pin for pin in pins if pin['identifier'] == self.ExpectedPinId]
        if not pin:
            self._logger.Log(LogType.Warn,
                             "Device '%s' missing expected pin '%s'",
                             deviceName, self.ExpectedPinId)
            return False

        self._io_pin = int(pin[0]['ioPin'][len(pinPrefix):])
        self._hardware_io.setup(self._io_pin, self._hardware_io.IN,
                                pull_up_down=self._hardware_io.PUD_UP)

        return True


    ## Check the state of the device, e.g. has the state changed so that it is
    #  triggered etc.
    #  @param self The object pointer.
    def CheckDevice(self):
        contactState = self._hardware_io.input(self._io_pin)

        # If we are in the alarmed set grace period then the triggered flag is
        # not changable until the grace period has expired.  Once it has then
        # revert the grace period type which means if the sensor is in a
        # triggered state (open) then an alarm event is raised.
        if self._state_type == self.StateType.AlarmSetPeriod:
            self.__HandleAlarmSetGracePeriod(contactState)

        # If we are in the alarm unset period (if no action e.g. typing in the
        # right key code is entered then the alarm is triggered) then the
        # triggered flag is not changable until the grace period has expired or
        # the alarm has been acknowledged.  If after the grace period the alarm
        # hasn't been acknowledged the an alarm even is raised.
        elif self._state_type == self.StateType.AlarmUnsetPeriod:
            self.__HandleAlarmUnsetGracePeriod()

        else:
            # The alarm has been triggered, don't change the state or allow the
            # the grace period to be updated so just return out of function.
            if self._is_triggered:
                return

            if self._is_triggered != contactState:
                stateMsg = "opened" if contactState else "closed"

                # If the alarm is inactive then just change state change.
                if self._state_type == self.StateType.AlarmInactive:
                    self._logger.Log(LogType.Info,
                                          "Device '%s' was %s",
                                          self._device_name, stateMsg)
                    self._is_triggered = contactState
                    return

                graceSecs = self._additional_params['triggerGracePeriodSecs']
                if graceSecs:
                    self._state_type = self.StateType.AlarmUnsetPeriod
                    self._logger.Log(LogType.Info,
                                          "Device '%s' sensor triggered, entered " +\
                                          "grace period of %s seconds", self._device_name, graceSecs)
                    self._grace_timeout = time.time() + graceSecs

                else:
                    self._is_triggered = contactState
                    self._logger.Log(LogType.Info, "Device '%s' was %s",
                                          self._device_name, stateMsg)
                    self.__GenerateDeviceStateChangeEvt()


    ## Recieve events from the event manager, these include the change of the
    #  the alarms state (activate/deactivated etc.).
    #  @param self The object pointer.
    #  @param eventInst Event instance.
    def ReceiveEvent(self, eventInst):
        if eventInst.id == Evts.EvtType.AlarmActivated:
            if 'triggerGracePeriodSecs' in self._additional_params:
                graceSecs = self._additional_params['triggerGracePeriodSecs']
                self._grace_timeout = eventInst.body['activationTimestamp'] +\
                    graceSecs
                self._logger.Log(LogType.Info,
                                      "Alarm activated, device '%s' is in " +\
                                      "grace period of %s seconds", self._device_name, graceSecs)
                self._state_type = self.StateType.AlarmSetPeriod
            self._is_triggered = False

        elif eventInst.id == Evts.EvtType.AlarmDeactivated:
            self._state_type = self.StateType.AlarmInactive


    ## Generate and queue the event when a device state changes.
    #  @param self The object pointer.
    def __GenerateDeviceStateChangeEvt(self):
        evtBody = {
            Evts.SensorDeviceBodyItem.DeviceType: self.SensorName,
            Evts.SensorDeviceBodyItem.DeviceName: self._device_name,
            Evts.SensorDeviceBodyItem.State: self._is_triggered
        }
        evt = Event(Evts.EvtType.SensorDeviceStateChange, evtBody)
        self._event_mgr.QueueEvent(evt)


    #  @param self The object pointer.
    def __HandleAlarmSetGracePeriod(self, contactState):
        currTime = time.time()

        # Still in grace period, thus _is_triggered flag currently cannot be
        # changed.
        if currTime <= self._grace_timeout:
            return

        # The grace period has expired, change to the state 'AlarmActivate'
        # and then check the trigger state.
        self._state_type = self.StateType.AlarmActivate
        self._logger.Log(LogType.Info,
                              "Device '%s' alarm set grace period ended...",
                              self._device_name)

        if contactState:
            self._logger.Log(LogType.Info,
                                  "Device '%s' caused alarm to trigger",
                                  self._device_name)
            self._is_triggered = True
            self.__GenerateDeviceStateChangeEvt()


    #  @param self The object pointer.
    def __HandleAlarmUnsetGracePeriod(self):
        currTime = time.time()

        # Still in grace period, thus _is_triggered flag currently cannot be
        # changed.
        if currTime <= self._grace_timeout:
            return

        # If we have come out of the grace period and the alarm hasn't been
        # deactivated during this time then trigger the alarm.
        self._logger.Log(LogType.Info,
                              "Device '%s' alarm unset grace period ended, " + \
                              "the alarm has been triggered!", self._device_name)
        self._state_type = self.StateType.AlarmActivate
        self.__GenerateDeviceStateChangeEvt()
        self._is_triggered = True
