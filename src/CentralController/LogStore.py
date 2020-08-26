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


LogEntry = collections.namedtuple('LogEntry',
                                  'timestamp logLevel msg')


class LogStore:
    __slots__ = ['_logEntries', '_maxEntriesReturned']

    def __init__(self):
        self._logEntries = []
        self._maxEntriesReturned = 50


    def AddLogEvent(self, timestamp, logLevel, msg):
        entry = LogEntry(timestamp=timestamp, logLevel=logLevel, msg=msg)
        self._logEntries.append(entry)


    def Count(self):
        return len(self._logEntries)


    def GetLogEvents(self, timestamp):

        logs = [l for l in self._logEntries if l.timestamp > timestamp]

        logs = logs[:self._maxEntriesReturned]

        lastTimestamp = logs[-1].timestamp if len(logs) >= 1 else 0
        jsonData = {
            'lastTimestamp': lastTimestamp,
            'entries':
            [

            ]
        }

        for entry in logs:
            newJsonEntry = {
                'timestamp' : entry.timestamp,
                'level'     : entry.logLevel.value,
                'message'   : entry.msg
            }
            jsonData['entries'].append(newJsonEntry)

        return jsonData
