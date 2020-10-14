"""
DataBase Handler

* define access to Oracle/MSSQL
* Get Table, Row and Updates
"""

import cx_Oracle
import pyodbc


class DbSQL:
    """ Create a new SQLServer type DB """

    def __init__(self, dbconn):
        """ Create a new db connection """
        self.dbconn = dbconn
        self.dbSQL = pyodbc.connect(dbconn)

    def getrows(self, query):
        cursorSQL = self.dbSQL.cursor()
        cursorSQL.execute(query)
        columns = [column[0] for column in cursorSQL.description]
        results = []
        for row in cursorSQL.fetchall():
            results.append(dict(zip(columns, row)))
        return results

    def getrow(self, query):
        cursorSQL = self.dbSQL.cursor()
        cursorSQL.execute(query)
        columns = [column[0] for column in cursorSQL.description]
        results = [dict(zip(columns, cursorSQL.fetchone()))]
        return results[0]

    def setrow(self, query):
        cursorSQL = self.dbSQL.cursor()
        cursorSQL.execute(query)
        self.dbSQL.commit()



class DbOra:
    """ Create a new OracleServer type DB """

    def __init__(self, dbconn):
        """ Create a new db connection """
        self.dbconn = dbconn
        self.dbOra = cx_Oracle.Connection(dbconn)

    def getrows(self, query):
        cursorOra = self.dbOra.cursor()
        rs = cursorOra.execute(query)
        return rows_to_dict_list(cursorOra)

    def getrow(self, query):
        cursorOra = self.dbOra.cursor()
        rs = cursorOra.execute(query)
        return rows_to_dict_list(cursorOra)[0]

    def setrow(self, query):
        cursorOra = self.dbOra.cursor()
        cursorOra.execute(query)


def rows_to_dict_list(cursor):
    columns = [i[0] for i in cursor.description]
    return [dict(zip(columns, row)) for row in cursor]
