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
from enum import Enum


## Return codes for ReceiveKeyCode route.
class ReceiveKeyCodeReturnCode(Enum):
    # The keycode has been accepted and the alarm is now off/disabled.
    KeycodeAccepted = 0

    # The keycode entered was invalid, as a result the keypad could get locked
    # for a period of time.
    KeycodeIncorrect = 1

    # The keycode was refused, possibly you are trying to enter a keycode when
    # the keypad is meant to be disabled.    
    KeycodeRefused = 2

    # a keycode was received out of sequence and is not expected so rejecting.
    OutOfSequence = 3
