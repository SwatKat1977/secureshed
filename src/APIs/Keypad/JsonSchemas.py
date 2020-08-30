'''
Copyright 2019-2020 Secure Shed Project Dev Team

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
# pylint: disable=C0103
# pylint: disable=R0903


AUTH_KEY = 'authorisationKey'


class KeypadLockRequest:

    Schema = {
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

    class BodyElement:
        LockTime = 'lockTime'


class RetrieveConsoleLogs:
    Schema = {
        "type" : "object",
        "additionalProperties" : False,

        "properties" : {
            "additionalProperties" : False,
            "startTimestamp" :
            {
                "type" : "number",
                "minimum": 0
            }
        },
        "required": ["startTimestamp"]
    }

    class BodyElement:
        StartTimestamp = 'startTimestamp'


class RequestLogsResponse:
    Schema = {
        "definitions":
        {
            "LogEntry":
            {
                "type": "object",
                "additionalProperties" : False,
                "required": ["timestamp", "level", "message"],
                "properties":
                {
                    "timestamp": {"type": "number"},
                    "level": {"type": "integer"},
                    "message": {"type": "string"}
                }
            }
        },
        "type" : "object",
        "properties":
        {
            "additionalProperties" : False,
            "lastTimestamp" :
            {
                "type" : "number",
                "minimum": 0
            },
            "entries":
            {
                "type": "array",
                "items": {"$ref": "#/definitions/LogEntry"}
            }
        },
        "required": ["lastTimestamp", "entries"],
        "additionalProperties" : False
    }

    class BodyElement:
        LastTimestamp = 'lastTimestamp'
        Entries = 'entries'
        EntryMsgLevel = 'level'
        EntryMessage = 'message'
        EntryTimestamp = 'timestamp'
