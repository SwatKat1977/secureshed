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
import multiprocessing
import wx
from KeypadController.ControlPanelFrame import ControlPanelFrame


##### https://pastebin.com/ZWKMeABY
##### https://www.journaldev.com/15631/python-multiprocessing-example


class GuiThread():

    #  @param self The object pointer.
    def __init__(self, app, config):

        self.__app = app
        self.__config = config

        self.event = multiprocessing.Event()
        self._processingQueue = multiprocessing.Queue()
        self.__process = multiprocessing.Process(target=self.OpenKeypadGui,
                                                 args=(self._processingQueue,
                                                       self.event))
        self.__process.daemon = True
        self.__process.start()


    #  @param self The object pointer.
    def TerminateGuiThread(self):
        self.__process.terminate()
        self.__process.join()


    #  @param self The object pointer.
    def OpenKeypadGui(self, _processingQueue, _event):
        app = wx.App()

        fsize = (400, 400)
        self.__modal = ControlPanelFrame(self.__config, fsize)
        self.__modal.Show()

        app.MainLoop()


    #  @param self The object pointer.
    def UpdateProgress(self):
        curVal = getattr(self.objWithProgressAttribute, self.progressAttributeName)
        self._q.put(curVal)
