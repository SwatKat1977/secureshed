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

class Routes:
    ReceiveKeyCode = 'ReceiveKeyCode'


ReceiveKeyCodeJsonSchema = {
    "type" : "object",
    "additionalProperties" : False,

    "properties" : {
        "additionalProperties" : False,
        "keySequence" : {"type" : "string"},
    },
    "required": ["keySequence"]
}


class receiveKeyCodeHeader:
    AuthKey = 'authorisationKey'


class receiveKeyCodeBody:
    KeySeq = 'keySequence'


class receiveKeyCodeResponse:
    ReturnCode = 'returnCode'
    Actions = 'actions'


class receiveKeyCodeResponseAction_KeycodeAccepted:
    AlarmUnlocked = 'alarmUnlocked'


class receiveKeyCodeResponseAction_KeycodeRefused:
    DisableKeypad = 'disableKeypad'


class receiveKeyCodeResponseAction_KeycodeIncorrect:
    DisableKeypad = 'disableKeypad'
    TriggerAlarm = 'triggerAlarm'


RECEIVEKEYPADLOCKSCHEMA = {
    "type" : "object",
    "properties":
    {
        "additionalProperties" : False,
        "lockTime" :
        {
            "type" : "integer",
            "minimum": 0
        },
    },
    "required": ["lockTime"],
    "additionalProperties" : False
}
