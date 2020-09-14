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
import enum
import logging
import time


class LogType(enum.Enum):
    Debug = 0
    Info = 1
    Warn = 2
    Error = 3
    Critical = 4


class Logger:
    __slots__ = ['_externalLogger', '_isInitialised', '_loggerInst',
                 '_writeToConsole']

    LoggerMappings = {
        LogType.Debug : ('debug', logging.DEBUG),
        LogType.Error : ('error', logging.ERROR),
        LogType.Info : ('info', logging.INFO),
        LogType.Warn : ('warn', logging.WARN),
        LogType.Critical : ('critical', logging.CRITICAL),
    }

    @property
    def WriteToConsole(self):
        return self._writeToConsole

    @WriteToConsole.setter
    def WriteToConsole(self, value):
        self._writeToConsole = value

    @property
    def ExternalLogger(self):
        return self._externalLogger

    @ExternalLogger.setter
    def ExternalLogger(self, value):
        self._externalLogger = value


    def __init__(self):
        self._externalLogger = None
        self._isInitialised = False
        self._loggerInst = None
        self._writeToConsole = False


    def Initialise(self):
        if self._isInitialised:
            raise RuntimeError('Logger is already initialised!')

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                      "%Y-%m-%d %H:%M:%S")

        self._loggerInst = logging.getLogger('system log')
        consoleStream = logging.StreamHandler()
        consoleStream.setFormatter(formatter)
        self._loggerInst.setLevel(logging.DEBUG)
        self._loggerInst.addHandler(consoleStream)

        self._isInitialised = True


    def Log(self, logLevel, msg, *args):
        if not self._isInitialised:
            raise RuntimeError('Logger is not initialised!')

        if self._writeToConsole:
            mappedMethod, _ = self.LoggerMappings[logLevel]
            methodToCall = getattr(self._loggerInst, mappedMethod)
            methodToCall(msg, *args)

        if self._externalLogger:
            currTime = time.time()
            compiledMsg = msg % args
            self._externalLogger.AddLogEvent(currTime, logLevel, compiledMsg)
