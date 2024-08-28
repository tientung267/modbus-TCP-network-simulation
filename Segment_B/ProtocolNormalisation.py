import struct
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

class ProtocolNormalisation:
    """this class simulates the protocol normalisation mechanism. The request from client to server and the response
        from server to client will be normalised. """
    @staticmethod
    def protocol_normalisation(mbap_header, pdu_body, client_to_server):
        """
        Scenario: ModbusServer start with transaction_id 0, meanwhile ModbusClient starts with transaction_id 1
        :param mbap_header: header of the modbus/TCP packet
        :param pdu_body: payload of the modbus/TCP packet
        :param client_to_server: flag to determine if this is a request or a response packet

        :returns: Normalized modbus/TCP packet.
        """
        (transaction_id, protocol_id, length, unit_id) = struct.unpack('>HHHB', mbap_header)
        logging.info("Protocol normalisation started")
        if client_to_server:
            new_mbap_header = struct.pack('>HHHB', transaction_id - 1, protocol_id, length, unit_id)
        else:
            new_mbap_header = struct.pack('>HHHB', transaction_id + 1, protocol_id, length, unit_id)

        return new_mbap_header + pdu_body
