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
    __slots__ = ['_log_entries', '_max_entries_returned']

    def __init__(self):
        self._log_entries = []
        self._max_entries_returned = 50


    def add_log_event(self, timestamp, log_level, msg):
        entry = LogEntry(timestamp=timestamp, logLevel=log_level, msg=msg)
        self._log_entries.append(entry)


    def count(self):
        return len(self._log_entries)


    def get_log_events(self, timestamp):

        logs = [l for l in self._log_entries if l.timestamp > timestamp]

        logs = logs[:self._max_entries_returned]

        last_timestamp = logs[-1].timestamp if len(logs) >= 1 else 0
        json_data = {
            'lastTimestamp': last_timestamp,
            'entries':
            [

            ]
        }

        for entry in logs:
            new_json_entry = {
                'timestamp' : entry.timestamp,
                'level'     : entry.logLevel.value,
                'message'   : entry.msg
            }
            json_data['entries'].append(new_json_entry)

        return json_data
