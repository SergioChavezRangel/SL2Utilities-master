# first of all import the socket library
import datetime
import socket
import sys
import threading
from dateutil import tz
import sl2util.dbhandler as db
from time import strftime


# next create a socket object
s = socket.socket()
print("Socket successfully created")

# reserve a port on your computer in our
# case it is 12345 but it can be anything
_port = 12345
_service_name = b'main_watchdog'
_dbconn = ''
autoset = False

def start_watchdog(service_name, port):
    global _service_name
    global _port
    global autoset
    _service_name = service_name
    _port = port

    # Next bind to the port
    # we have not typed any ip in the ip field
    # instead we have inputted an empty string
    # this makes the server listen to requests
    # coming from other computers on the network
    s.bind(('', _port))
    print("socket binded to %s" % _port)

    # put the socket into listening mode
    s.listen(5)
    # print("socket is listening")
    print('watchdog running...')
    wdjob = threading.Thread(target=watchdog_job, args=())
    wdjob.start()
    if autoset:
        update()


def watchdog_job():
    # a forever loop until we interrupt it or
    # an error occurs
    while True:
        try:
            # Establish connection with client.
            c, addr = s.accept()
            # print('Got connection from', addr)
            # send a thank you message to the client.

            to_zone = tz.tzlocal()
            from_zone = tz.tzutc()
            utc = datetime.utcnow()
            utc = utc.replace(tzinfo=from_zone)
            central = utc.astimezone(to_zone)
            timestamp = central.strftime("%Y/%m/%d %H:%M:%S")  # localtime())
            message = 'RUN'  # _service_name + b';' + timestamp.encode()
            c.send(message)
        except:
            print("Unexpected error:", sys.exc_info()[0])
        finally:
            # Close the connection with the client
            c.close()


def register(service_name, address, port, dbconn):
    global _service_name
    global _port
    global _dbconn
    global autoset
    autoset = True
    _service_name = service_name
    _port = port
    _dbconn = dbconn
    watchdogdb = db.DbSQL(_dbconn)
    sql = "PROC_SL2_SET_SERVICE '{}', '{}', {}".format(service_name.decode(), address, port)
    # print(sql)
    watchdogdb.setrow(sql)
    pass


def update():
    watchdogdb = db.DbSQL(_dbconn)
    sql = "UPDATE SL2_SERVICES_CONFIG SET STATUS = 1, TIME_STAMP = getdate() \
           WHERE  SERVICE_NAME = '{}'".format(_service_name.decode())
    # print(sql)
    watchdogdb.setrow(sql)

