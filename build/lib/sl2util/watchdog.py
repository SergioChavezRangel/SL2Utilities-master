# first of all import the socket library
import socket
import sys
import threading

# next create a socket object
from time import strftime, localtime

s = socket.socket()
print("Socket successfully created")

# reserve a port on your computer in our
# case it is 12345 but it can be anything
_port = 12345
_service_name = b'main_watchdog'


def start_watchdog(service_name, port):
    global _service_name
    global _port
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



def watchdog_job():
    # a forever loop until we interrupt it or
    # an error occurs
    while True:
        try:
            # Establish connection with client.
            c, addr = s.accept()
            # print('Got connection from', addr)

            # send a thank you message to the client.
            timestamp = strftime("%Y/%m/%d %H:%M:%S", localtime())
            message = _service_name + b';' + timestamp.encode()
            c.send(message)
        except:
            print("Unexpected error:", sys.exc_info()[0])
        finally:
            # Close the connection with the client
            c.close()
