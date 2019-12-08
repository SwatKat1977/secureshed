from centralController.DeviceTypes.BaseDeviceType import BaseDeviceType


class MagneticContactSensor(BaseDeviceType):

    def __init__(self, logger, hardwareIO):
        self.__logger = logger
        self.__ioPin = None
        self.__hardwareIO = hardwareIO
        self.__isTriggered = False
        self.__deviceName = None


    ExpectedPinId = 'sensorPin'


    def Initialise(self, deviceName, pins):
        self.__deviceName = deviceName

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
        if self.__hardwareIO.input(self.__ioPin):
            print("switch is open")
        else:
            print("switch is closed")

