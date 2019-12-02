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


class GPIO:

    ##################################
    # -- RPi.GPIO numbering systems --
    ##################################

    ## RPi.GPIO numbering systems : BCM.
    BCM = 101

    ## RPi.GPIO numbering systems : BCM.
    BOARD = 102

    IN = 201
    OUT = 202

    ##########################
    # -- RPi.GPIO pin state --
    ##########################

    ## RPi.GPIO pin state : Low.
    LOW = 301

    ## RPi.GPIO pin state : High.
    HIGH = 302


    @staticmethod
    def cleanup():
        pass


    @staticmethod
    def setup(pin, state):
        pass


    @staticmethod
    def setmode(modeType):
        pass


    @staticmethod
    def output(pin, state):
        pass
