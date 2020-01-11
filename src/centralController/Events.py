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


class EvtType(enum.Enum):
    #------------------------
    #- Keypad entry events
    KeypadKeyCodeEntered = 1001

    #------------------------
    #- Device state change events
    SensorDeviceStateChange = 2001

    #------------------------
    #- Siren related events
    ActivateSiren = 3001
    DeactivateSiren = 3002

    #------------------------
    #- Alarm state change events
    AlarmActivated = 4001
    AlarmDeactivated = 4002

    #------------------------
    #- Keypad Api events
    KeypadApiSendAlivePing = 5001
    KeypadApiSendKeypadLock = 5002


class SensorDeviceBodyItem:
    DeviceType = 'deviceType'
    DeviceName = 'deviceName'
    State = 'state'
