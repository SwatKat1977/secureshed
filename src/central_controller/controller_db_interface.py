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
    def database_name(self):
        return self._db_name

    ## Property getter : Is connected to database flag
    @property
    def is_connected(self):
        return self._is_connected

    ## Property getter : Last error message
    @property
    def last_error_msg(self):
        return self._last_err_msg


    ## Default constructor for ControllerDBInterface class instance.
    #  @param self The object pointer.
    def __init__(self):
        ## Internal variable for databaseName attribute.
        self._db_name = ''

        ## Internal variable for isConnected attribute.
        self._is_connected = ''

        ## Database object instance.
        self._db_obj = None

        ## Last error message in human-readable format.
        self._last_err_msg = ''

        ## Instance of the cursor object.
        self._cursor = ''


    ## Attempt to connect to the database.
    #  @param self The object pointer.
    #  @param dbName Name of the database to connect to.
    #  @returns False if connect fails, True if connection succeeded.
    def connect(self, db_name):

        try:
            dburi = 'file:{}?mode=rw'.format(pathname2url(db_name))
            self._db_obj = sqlite3.connect(dburi, uri=True,
                                           check_same_thread=False)

        except sqlite3.OperationalError:
            self._last_err_msg = f'Unable to connect to database {db_name}'
            return False

        self._db_name = db_name
        self._is_connected = True
        self._cursor = self._db_obj.cursor()

        return True


    ## Get the details for a keycode. based on the keycode passed in.
    #  @param self The object pointer.
    #  @param keycode Keycode to search on.
    def get_keycode_details(self, keycode):
        query = "SELECT IsMasterKey FROM KeyCodes WHERE KeyCode=?"
        details = self._execute_with_return(query, (keycode,), True)

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
    def _execute_without_return(self, query, values=(), commit=True):
        if not self._execute_sql(query, values):
            return False

        if commit:
            self._db_obj.commit()

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
    def _execute_with_return(self, query, values=(), fetch_only_one=False):
        if not self._execute_sql(query, values):
            return None

        column_names = list(map(lambda x: x[0], self._cursor.description))

        # Get the results from the query, either just one if the fetchOnlyOne
        # flag is set to true, otherwise get all of them.
        res = self._cursor.fetchone() if fetch_only_one \
            else self._cursor.fetchall()

        return None if not res else (column_names, res)


    ## Internal method to execute a SQL statement that doesn't return any data
    #  set, for example INSERT or DELETE.
    #  @param self The object pointer.
    #  @param query Query statement to be executed.
    #  @param values Values to substitute.
    #  @returns False if the query fails to execute, lastErrMsg is also
    #  populated.  True if successful.
    def _execute_sql(self, query, values):
        try:
            self._cursor.execute(query, values)

        except sqlite3.Error as ex:
            self._last_err_msg = f'SQL error: {ex}'
            return False

        return True
