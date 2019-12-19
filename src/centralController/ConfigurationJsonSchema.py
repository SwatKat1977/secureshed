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


CONFIGURATIONJSONSCHEMA = \
{
    "$schema": "http://json-schema.org/draft-07/schema#",

    "definitions":
    {
        "action":
        {
            "type": "object",
            "additionalProperties" : False,
            "properties":
            {
                "additionalProperties" : False,
                "actionType":
                {
                    "type": "string",
                    "enum": ["disableKeyPad", "triggerAlarm", "resetAttemptAccount"]
                },
                "parameters":
                {
                    "type": "array",
                    "items": {"$ref": "#/definitions/actionParameter"},
                    "default": []
                }
            },
            "required": ["actionType"]
        },

        "actionParameter":
        {
            "type": "object",
            "additionalProperties" : False,
            "properties":
            {
                "additionalProperties" : False,
                "key":   {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["key", "value"]
        },

        "failedAttemptResponse":
        {
            "type": "object",
            "additionalProperties" : False,
            "properties":
            {
                "additionalProperties" : False,
                "attemptNo":
                {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100
                },
                "actions":
                {
                    "type": "array",
                    "items": {"$ref": "#/definitions/action"},
                    "default": []
                }
            },
            "required" : ["attemptNo", "actions"]
        }
    },

    "type" : "object",
    "additionalProperties" : False,

    "properties":
    {
        "additionalProperties" : False,
        "failedAttemptResponses":
        {
            "type": "array",
            "items": {"$ref": "#/definitions/failedAttemptResponse"},
            "default": []
        },
        "keypadAPI":
        {
            "additionalProperties" : False,
            "properties":
            {
                "additionalProperties" : False,
                "networkPort" :
                {
                    "type" : "integer",
                    "minimum": 1
                }
            },
            "required" : ["networkPort"]
        }
    },
    "required" : ["failedAttemptResponses", "keypadAPI"]
}
