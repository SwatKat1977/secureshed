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
import collections
from centralController.DevicesConfigLoader import DevicesConfigLoader

try:
    import RPi.GPIO as GPIO
    RPIO_EMULATED = False
except ModuleNotFoundError:
    from centralController.EmulatedRaspberryPiIO import GPIO
    RPIO_EMULATED = True


'''
# the pin numbers refer to the board connector not the chip
GPIO.setmode(GPIO.BCM)

relayPin = 18

print(relayPin)
GPIO.setup(relayPin, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
# set up pin ?? (one of the above listed pins) as an input with
# a pull-up resistor

while True:
    if GPIO.input(relayPin):
        print "switch is open"
    else:
        print "switch is closed"

    time.sleep(1)
'''


class DeviceManager:
    __slots__ = ['__devices', '__deviceTypeMgr', '__logger']

    Device = collections.namedtuple('Device', 'name hardware deviceType pins')


    #  @param self The object pointer.
    def __init__(self, logger, deviceTypeMgr):
        self.__logger = logger
        self.__deviceTypeMgr = deviceTypeMgr
        self.__devices = []

        if RPIO_EMULATED:
            self.__logger.info('Using Raspberry PI IO Emulation...')

        GPIO.setmode(GPIO.BCM)


    #  @param self The object pointer.
    def Load(self, devices):
        deviceTypes = self.__deviceTypeMgr.deviceTypes

        for device in devices:
            name = device[DevicesConfigLoader.DeviceElement.Name]
            enabled = device[DevicesConfigLoader.DeviceElement.Enabled]

            if not enabled:
                self.__logger.warn("Device '%s' is disabled, not loading it!",
                                   name)
                continue

            pins = device[DevicesConfigLoader.DeviceElement.Pins]
            hardware = device[DevicesConfigLoader.DeviceElement.Hardware]
            deviceType = device[DevicesConfigLoader.DeviceElement.DeviceType]

            if deviceType not in deviceTypes:
                self.__logger.warn("Ignoring device '%s' as it has invalid " +\
                                   "device type of '%s'", name, deviceType)
                continue

            newDevice = self.Device(name=name, hardware=hardware,
                                    deviceType=deviceTypes[deviceType](),
                                    pins=pins)
            self.__devices.append(newDevice)


    #  @param self The object pointer.
    def InitialiseHardware(self):

        for device in self.__devices:

            # deviceName = device.name
            self.__logger.info(f'|=> Device name : {device.name}')
            self.__logger.info(f'|=> Device type : {device.deviceType}')

            for pin in device.pins:
                self.__logger.debug(f'|=> PIN : {pin}')

            # Device(name='Garage door sensor', hardware='siren',
            # deviceType=<class 'centralController.DeviceTypes.GenericAlarmSiren.GenericAlarmSiren'>,
            # enabled=True, pins=[{'ioPin': 'GPIO18', 'initialState': 'high', 'mode': 'output'}])


    def CleanupDevices(self):
        GPIO.cleanup()
