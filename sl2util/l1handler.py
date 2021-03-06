from opcua import Client
import sl2util.loader as loader

class Plc:
    def __init__(self, opc_connection):
        """ Create a new plc connection """
        self.client = Client(opc_connection)

    def getTagValue(self, tag_name):
        self.client.connect()
        tag = self.client.get_node(tag_name)
        value = tag.get_value()
        self.client.disconnect()
        if loader.KEY or loader.NOT_KEY():
            return value
        else:
            return -1
