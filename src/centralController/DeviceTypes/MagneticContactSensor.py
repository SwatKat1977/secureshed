from centralController.DeviceTypes.BaseDeviceType import BaseDeviceType


class MagneticContactSensor(BaseDeviceType):

    def __init__(self, logger, hardwareIO):
        self.__logger = logger
        self.__pins = []
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

        pinNo = int(pin[0]['ioPin'][len(pinPrefix):])
        self.__hardwareIO.setup(pinNo, self.__hardwareIO.IN,
                                pull_up_down=self.__hardwareIO.PUD_UP)

        return True


    def CheckDevice(self):
        if GPIO.input(relayPin):
            print "switch is open"
        else:
            print "switch is closed"

        self.__deviceName


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


'''
RelayPin = 23

GPIO.cleanup() 

GPIO.setmode(GPIO.BCM)


GPIO.setup(RelayPin, GPIO.OUT)
GPIO.output(RelayPin, GPIO.HIGH)
print('SETUP relay')
time.sleep(10)

print('Activating')
GPIO.output(RelayPin, GPIO.LOW)
time.sleep(10)
print('De-activating')
GPIO.output(RelayPin, GPIO.HIGH)

time.sleep(10)
print('Activating')
GPIO.output(RelayPin, GPIO.LOW)

time.sleep(10)

GPIO.cleanup() 
'''
