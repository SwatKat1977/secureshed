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
    def databaseName(self):
        return self.__dbName

    ## Property getter : Is connected to database flag
    @property
    def isConnected(self):
        return self.__isConnected

    ## Property getter : Last error message
    @property
    def lastErrorMsg(self):
        return self.__lastErrMsg


    ## Default constructor for ControllerDBInterface class instance.
    #  @param self The object pointer.
    def __init__(self):
        ## Internal variable for databaseName attribute.
        self.__dbName = ''

        ## Internal variable for isConnected attribute.
        self.__isConnected = ''

        ## Database object instance.
        self.__dbObj = None

        ## Last error message in human-readable format.
        self.__lastErrMsg = ''

        ## Instance of the cursor object.
        self.__cursor = ''


    ## Attempt to connect to the database.
    #  @param self The object pointer.
    #  @param dbName Name of the database to connect to.
    #  @returns False if connect fails, True if connection succeeded.
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


    ## Get the details for a keycode. based on the keycode passed in.
    #  @param self The object pointer.
    #  @param keycode Keycode to search on.
    def GetKeycodeDetails(self, keycode):
        query = "SELECT IsMasterKey FROM KeyCodes WHERE KeyCode=?"
        details = self.__ExecuteWithReturn(query, (keycode,), True)

        if not details:
            return None

        cols, vals = details
        return dict(zip(cols, vals))


    ## Internal method to execute a SQL statement that doesn't return any data
    #  set, for example INSERT or DELETE.
    #  @param self The object pointer.
    #  @param query Query statement to be executed.
    #  @param values Values to substitute.  Default is empty.
    #  @param commit Flag if to try and commit the SQL call.  Default is True.
    #  @returns False if the query fails to execute, True if successful.
    def __ExecuteWithoutReturn(self, query, values=(), commit=True):
        if not self.__ExecuteSql(query, values):
            return False

        if commit:
            self.__dbObj.commit()

        return True


    ## Internal method to execute a SQL statement that returns a data set, e.g.
    #  SELECT.
    #  @param self The object pointer.
    #  @param query Query statement to be executed.
    #  @param values Values to substitute, default is empty.
    #  @param fetchOnlyOne Fetch only one entry flag.
    #  @returns Dataset is returned if successful, if fetchOnlyOne is set then
    #  only a single row is returned otherwise all rows are returned.  If the
    #  execute failed then None is returned.
    def __ExecuteWithReturn(self, query, values=(), fetchOnlyOne=False):
        if not self.__ExecuteSql(query, values):
            return None

        columnNames = list(map(lambda x: x[0], self.__cursor.description))

        # Get the results from the query, either just one if the fetchOnlyOne
        # flag is set to true, otherwise get all of them.
        res = self.__cursor.fetchone() if fetchOnlyOne \
            else self.__cursor.fetchall()

        return None if not res else (columnNames, res)


    ## Internal method to execute a SQL statement that doesn't return any data
    #  set, for example INSERT or DELETE.
    #  @param self The object pointer.
    #  @param query Query statement to be executed.
    #  @param values Values to substitute.
    #  @returns False if the query fails to execute, lastErrMsg is also
    #  populated.  True if successful.
    def __ExecuteSql(self, query, values):
        try:
            self.__cursor.execute(query, values)

        except sqlite3.Error as ex:
            self.__lastErrMsg = f'SQL error: {ex}'
            return False

        return True
