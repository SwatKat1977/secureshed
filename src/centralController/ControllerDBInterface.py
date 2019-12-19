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
from urllib.request import pathname2url
import sqlite3


class ControllerDBInterface:

    ## Property getter : Database name
    @property
    def DatabaseName(self):
        return self.__dbName

    ## Property getter : Is connected to database flag
    @property
    def IsConnected(self):
        return self.__isConnected

    ## Property getter : Last error message
    @property
    def LastErrorMsg(self):
        return self.__lastErrMsg


    def __init__(self):
        self.__dbName = ''
        self.__isConnected = ''
        self.__dbObj = None
        self.__lastErrMsg = ''
        self.__cursor = ''


    def Connect(self, dbName):

        try:
            dburi = 'file:{}?mode=rw'.format(pathname2url(dbName))
            self.__dbObj = sqlite3.connect(dburi, uri=True,
                check_same_thread=False)

        except sqlite3.OperationalError:
            self.__lastErrMsg = f'Unable to connect to database {dbName}'
            return False

        self.__dbName = dbName
        self.__isConnected = True
        self.__cursor = self.__dbObj.cursor()
        
        return True


    def GetKeycodeDetails(self, keycode):
        query = "SELECT IsMasterKey FROM KeyCodes WHERE KeyCode=?"
        details = self.__ExecuteWithReturn(query, (keycode,), True)

        if not details:
            return None
        
        cols, vals = details
        return dict(zip(cols, vals))


    def __ExecuteWithoutReturn(self, query, values=(), commit=True):
        if self.__ExecuteSQL(query, values) == False:
            return False

        if commit == True:
            self.__dbObj.commit()


    def __ExecuteWithReturn(self, query, values=(), fetchOnlyOne=False):
        if self.__ExecuteSQL(query, values) == False:
            return None

        columnNames = list(map(lambda x: x[0], self.__cursor.description))

        # Get the results from the query, either just one if the fetchOnlyOne
        # flag is set to true, otherwise get all of them.
        res = self.__cursor.fetchone() if fetchOnlyOne == True \
            else self.__cursor.fetchall()
 
        return None if res == None else (columnNames, res)


    def __ExecuteSQL(self, query, values):
        try:
            self.__cursor.execute(query, values)

        except sqlite3.Error as ex:
            self.__lastErrMsg = f'SQL error: {ex}'
            return False

        return True
