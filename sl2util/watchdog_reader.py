# Import socket module
import datetime
import socket
import sl2util.dbhandler as db


_dbconn = ''
data = dict()


def get_services():
    global data
    watchdogdb = db.DbSQL(_dbconn)
    sql = "SELECT * FROM SL2_SERVICES_CONFIG WHERE USED > 0"
    # ID, SERVICE_NAME, SERVICE_DESCR, ADDRESS, PORT, USED, STATUS, TIME_STAMP
    data.clear()
    for row in watchdogdb.getrows(sql):
        res = call_service(row['ADDRESS'], row['PORT'])
        data[row['SERVICE_NAME']] = None if res is None else 'RUN'  # res  #  res
        status = 0 if res is None else 1
        update(status, row['SERVICE_NAME'])


def call_service(address, port):
    try:
        # Create a socket object
        s = socket.socket()
        # Define the port on which you want to connect
        # connect to the server on local computer
        s.connect((address, port))
        # receive data from the server
        result = s.recv(1024).decode()  # .split(';')
        # close the connection
        s.close()
    except:
        result = None
    return result


def register(watchdogdb):
    global _dbconn
    _dbconn = watchdogdb
    get_services()


def update(status, service_name):
    watchdogdb = db.DbSQL(_dbconn)
    sql = "UPDATE SL2_SERVICES_CONFIG SET STATUS = {}, TIME_STAMP = getdate() \
           WHERE  SERVICE_NAME = '{}'".format(status, service_name)
    watchdogdb.setrow(sql)

