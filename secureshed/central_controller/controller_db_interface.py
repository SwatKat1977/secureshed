"""
Copyright 2019-2024 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
import os
import sqlite3
import urllib

class ControllerDBInterface:
    """ Database interface """
    __slots__ = ["_cursor", "_db_file", "_db_obj", "_logger", "_is_connected"]

    @property
    def database_file(self):
        """ Property getter : Database file """
        return self._db_file

    @property
    def is_connected(self):
        """ Property getter : Is connected to database flag """
        return self._is_connected

    def __init__(self, logger: logging.Logger):
        """ Default constructor for ControllerDBInterface class instance."""

        self._logger = logger.getChild(__name__)

        # Internal variable for databaseName attribute.
        self._db_file: str = ''

        # Internal variable for is_connected attribute.
        self._is_connected: bool = False

        # Database object instance.
        self._db_obj: sqlite3.Connection | None = None

        # Instance of the cursor object.
        self._cursor: sqlite3.Cursor | None = None

    def connect(self, db_file: str) -> bool:
        """
        Connect to A sqlite3 database.

        Arguments:
            db_file (str): Database file to connect to.

        Return:
            Boolean representing if connect was successful or not.
        """

        file_stats = os.stat(db_file)
        if not file_stats.st_size:
            self._logger.critical("Database '%s' is invalid : empty file",
                                  db_file)
            return False

        try:
            uri: str = f"file:{urllib.request.pathname2url(db_file)}?mode=rw"
            self._db_obj = sqlite3.connect(uri, uri=True,
                                           check_same_thread=False)

        except sqlite3.OperationalError:
            self._logger.critical("Unable to connect to database '%s'",
                                  db_file)
            return False

        self._cursor = self._db_obj.cursor()

        try:
            self._cursor.execute("PRAGMA integrity_check")

        except sqlite3.DatabaseError:
            self._logger.critical("'%s' Isn't a valid database",
                                  db_file)
            self._db_obj.close()
            return False


        self._db_file = db_file
        self._is_connected = True

        return True

    def get_keycode_details(self, keycode: str):
        """
        Get the details for a keycode. based on the keycode passed in.

        Arguments:
            keycode (str): Keycode to search on.
        """
        query = "SELECT IsMasterKey FROM KeyCodes WHERE KeyCode=?"
        details = self._execute_with_return(query, (keycode,), True)
        print("::get_keycode_details:: details: ", details)

        if not details:
            return None

        cols, vals = details
        return dict(zip(cols, vals))

    def _execute_without_return(self, query, values: list | None = None,
                                commit=True):
        """
        Internal method to execute a SQL statement that doesn't return any data
        set, for example INSERT or DELETE.

        Arguments:
            query (str): Query statement to be executed.
            values (lidy | None): Values to substitute.  Default is empty.
            commit (bool): Flag if to try and commit the SQL call.  Default is
                           True.
        Returns:
            returns False if the query fails to execute, True if successful.
        """
        query_params = [] if not values else values
        self._execute_sql(query, query_params)

        if commit:
            self._db_obj.commit()

        return True

    def _execute_with_return(self, query: str, values: list | None = None,
                             fetch_only_one: bool = False):
        """
        Internal method to execute a SQL statement that returns a data set,
        e.g. SELECT.

        Arguments:
            query (str): Query statement to be executed.
            values (list|None)@ Values to substitute, default is None.
            fetch_only_one (bool): Fetch only one entry flag.

        Returns:
            Dataset is returned if successful, if fetch_only_one is set then
            only a single row is returned otherwise all rows are returned. If
            the query failed then None is returned.
        """

        query_params = [] if not values else values
        print("::_execute_with_return:: Query Params", query_params)

        self._execute_sql(query, query_params)

        column_names = list(map(lambda x: x[0], self._cursor.description))

        # Get the results from the query, either just one if the fetchOnlyOne
        # flag is set to true, otherwise get all of them.
        res = self._cursor.fetchone() if fetch_only_one \
            else self._cursor.fetchall()

        return None if not res else (column_names, res)

    def _execute_sql(self, query: str, values: list) -> None:
        """
        Internal method to execute a SQL statement that doesn't return any data
        set, for example INSERT or DELETE. Values for the query are passed in
        separately, they are escaped to avoid bad query values.

        Arguments:
            query (str): SQL query string
            values (list): List of values
        """
        try:
            self._cursor.execute(query, values)

        except sqlite3.Error as ex:
            raise RuntimeError("SQL error: {ex}") from ex
