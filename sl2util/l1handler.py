"""
Level 1 (PLC) OPC-UA Handler
Provides connectivity and tag value retrieval from Level 1 PLCs/automation systems.
Supports modern asyncua sync wrapper as well as legacy opcua.
"""
from typing import Any

try:
    # Try modern asyncua sync client first
    from asyncua.sync import Client as _SyncOpcClient
    _OPC_AVAILABLE = True
except ImportError:
    try:
        # Fallback to legacy opcua if installed
        from opcua import Client as _SyncOpcClient
        _OPC_AVAILABLE = True
    except ImportError:
        _SyncOpcClient = None
        _OPC_AVAILABLE = False


class Plc:
    """OPC-UA Level 1 PLC connection handler."""

    def __init__(self, opc_connection: str):
        """
        Create a new PLC connection client.
        :param opc_connection: OPC-UA server URL (e.g. opc.tcp://10.5.1.10:4840)
        """
        if not _OPC_AVAILABLE or _SyncOpcClient is None:
            raise ImportError(
                "OPC-UA client library is required. Install via 'pip install asyncua' "
                "or install sl2util[opcua]."
            )
        self.opc_connection = opc_connection
        self.client = _SyncOpcClient(opc_connection)

    def getTagValue(self, tag_name: str) -> Any:
        """
        Connect to PLC, retrieve tag value, and disconnect safely.
        """
        self.client.connect()
        try:
            tag = self.client.get_node(tag_name)
            return tag.get_value()
        finally:
            try:
                self.client.disconnect()
            except Exception:
                pass
