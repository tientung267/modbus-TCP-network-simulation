import os
import socket
import time
import struct
from socket import AF_UNSPEC, SOCK_STREAM
from pyModbusTCP.client import ModbusClient as BaseModbusClient
from constants import HEADER_BITS_LENGTH
from pyModbusTCP.constants import MB_CONNECT_ERR,MB_SOCK_CLOSE_ERR, MB_SEND_ERR, MB_TIMEOUT_ERR
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

class ReadMsgT1:
    """This class extract hidden message from proxy server embedded with inter-packet-time methods"""
    hidden_message_t1 = ''
    msg_bits = ''
    bits_message_counter = 0
    stop_read_msg = False
    request_send_time = None
    response_receive_time = None

    @staticmethod
    def resolve_hidden_message_s1(function_code, collapsed_time):
        """
            this method resolves and add bit to the result string `hidden_message_s1`. A modbus/TCP packet with even length
            represents a bit 1 and a modbus/TCP packet with odd length represents a bit 0.

            :param function_code: function code of current modbus/TCP packet
            :param collapsed_time: round trip time from sending time of a modbus/TCP request
                                   to receiving time of a modbus/TCP response
        """
        if len(ReadMsgT1.msg_bits) < HEADER_BITS_LENGTH:
            ReadMsgT1.resolve_length_message(function_code, collapsed_time)
        else:
            if ReadMsgT1.bits_message_counter > 0:
                msg_changed, temp_hidden_message = ReadMsgT1.delay_logic(
                    collapsed_time,
                    function_code,
                    ReadMsgT1.hidden_message_t1
                )

                if msg_changed:
                    ReadMsgT1.hidden_message_t1 = temp_hidden_message
                    ReadMsgT1.bits_message_counter -= 1

                logging.info(f"Reading hidden message: {ReadMsgT1.hidden_message_t1}")
            else:
                logging.info(f"Read hidden message complete. Full message: {ReadMsgT1.hidden_message_t1}")
                ReadMsgT1.stop_read_msg = True

    @classmethod
    def resolve_length_message(cls, function_code, collapsed_time):
        _, cls.msg_bits = cls.delay_logic(collapsed_time,function_code, cls.msg_bits)
        logging.info(f"hidden message header in bits: {cls.msg_bits}")
        if len(cls.msg_bits) == HEADER_BITS_LENGTH:
            cls.bits_message_counter = int(cls.msg_bits, 2)
            logging.info(f"number of bits to read: {cls.bits_message_counter}")

    @staticmethod
    def delay_logic(rtt, function_code, bit_sequence):
        read_msg_changed = False
        rtt_without_delay = round((rtt - int(rtt)) + 0.005, 2)

        if 0.25 <= rtt_without_delay < 0.5 and function_code == 3:
            bit_sequence += '1'
            read_msg_changed = True

        if 0.25 <= rtt_without_delay < 0.5 and function_code == 6:
            bit_sequence += '0'
            read_msg_changed = True

        return read_msg_changed, bit_sequence
class CustomModbusClient(BaseModbusClient):
    def open(self):
        """Connect to modbus server (open TCP connection).

        :returns: connect status (True on success)
        :rtype: bool
        """
        try:
            self._open()
            return True
        except BaseModbusClient._NetworkError as e:
            self._req_except_handler(e)
            return False

    def _open(self):
        """Connect to modbus server (open TCP connection)."""
        # open an already open socket -> reset it
        if self.is_open:
            self.close()
        # init socket and connect
        # list available sockets on the target host/port
        # AF_xxx : AF_INET -> IPv4, AF_INET6 -> IPv6,
        #          AF_UNSPEC -> IPv6 (priority on some system) or 4
        # list available socket on target host
        for res in socket.getaddrinfo(self.host, self.port, AF_UNSPEC, SOCK_STREAM):
            af, sock_type, proto, canon_name, sa = res
            try:
                self._sock = socket.socket(af, sock_type, proto)
                modbus_client_name = os.getenv('MODBUS_CLIENT_NAME', 'localhost')
                modbus_client_port = int(os.getenv('MODBUS_CLIENT_PORT', 3000))

                logging.info(f"From {modbus_client_name}:{modbus_client_port}")
                self._sock.bind((modbus_client_name, modbus_client_port))
            except socket.error:
                continue
            try:
                self._sock.settimeout(self.timeout)

                logging.info(f"Attempting to connect to: {sa} \n")
                self._sock.connect(sa)
            except socket.error:
                self._sock.close()
                continue
            break
        # check connect status
        if not self.is_open:
            raise BaseModbusClient._NetworkError(MB_CONNECT_ERR, 'connection refused')

    def _send(self, frame):
        """Send frame over current socket.

        :param frame: modbus frame to send (MBAP + PDU)
        :type frame: bytes
        """
        # check socket
        if not self.is_open:
            raise BaseModbusClient._NetworkError(MB_SOCK_CLOSE_ERR, 'try to send on a close socket')
        # send
        try:
            self._sock.send(frame)
            # Record the time when the Modbus/TCP response is sent
            ReadMsgT1.request_send_time = time.time()
            logging.info(f"Request sent at: {ReadMsgT1.request_send_time}")

        except socket.timeout:
            self._sock.close()
            raise BaseModbusClient._NetworkError(MB_TIMEOUT_ERR, 'timeout error')
        except socket.error:
            self._sock.close()
            raise BaseModbusClient._NetworkError(MB_SEND_ERR, 'send error')

    def _add_mbap(self, pdu):
        """Return full modbus frame with MBAP (modbus application protocol header) append to PDU.

        :param pdu: modbus PDU (protocol data unit)
        :type pdu: bytes
        :returns: full modbus frame
        :rtype: bytes
        """

        # build MBAP
        # transaction_id should start with 0 and increase by 1 after each request
        self._transaction_id += 1
        protocol_id = 0
        length = len(pdu) + 1
        mbap = struct.pack('>HHHB', self._transaction_id, protocol_id, length, self.unit_id)

        self.mbap_header_logging(self._transaction_id, protocol_id, length, self.unit_id, "Request")
        self.pdu_body_logging(pdu, "Request")
        # full modbus/TCP frame = [MBAP]PDU

        return mbap + pdu

    def _recv_pdu(self, min_len=2):
        """Receive the modbus PDU (Protocol Data Unit).

        :param min_len: minimal length of the PDU
        :type min_len: int
        :returns: modbus frame PDU or None if error
        :rtype: bytes or None
        """
        # receive 7 bytes header (MBAP)
        rx_mbap = self._recv_all(7)
        # print("rx_mbap", rx_mbap)
        # decode MBAP
        (f_transaction_id, f_protocol_id, f_length, f_unit_id) = struct.unpack('>HHHB', rx_mbap)

        # Application-Layer Filtering: Check mbap header
        self.check_response_mbap_header(f_transaction_id, f_protocol_id, f_length, f_unit_id, rx_mbap)

        # recv PDU
        rx_pdu = self._recv_all(f_length - 1)

        # check pdu body. If no error, return PDU
        self.check_response_pdu_body(rx_pdu, min_len)

        # Record the time when the Modbus/TCP response is received
        ReadMsgT1.response_receive_time = time.time()
        logging.info(f"Response received at: {ReadMsgT1.response_receive_time}")
        collapsed_time = ReadMsgT1.response_receive_time - ReadMsgT1.request_send_time
        logging.info(f"Round-trip-time: {collapsed_time}")
        function_code = struct.unpack('>B', rx_pdu[0:1])[0]

        # Check if there is hidden message to read
        if os.getenv('APPLY_INTER_PACKET_TIMES', False):
            if not ReadMsgT1.stop_read_msg:
                ReadMsgT1.resolve_hidden_message_s1(function_code, collapsed_time)

        # for auto_close mode, close socket after each request
        if self.auto_close:
            self.close()
        # dump frame
        self._debug_dump('Rx', rx_mbap + rx_pdu)

        return rx_pdu

    def check_response_mbap_header(self, f_transaction_id, f_protocol_id, f_length, f_unit_id, rx_mbap):
        # print out Response header
        self.mbap_header_logging(f_transaction_id, f_protocol_id, f_length, f_unit_id, "Response")

        # check MBAP fields
        f_transaction_err = f_transaction_id != self._transaction_id
        f_protocol_err = f_protocol_id != 0
        f_length_err = f_length >= 256
        f_unit_id_err = f_unit_id != self.unit_id

        # checking error status of fields
        if f_transaction_err or f_protocol_err or f_length_err or f_unit_id_err:
            self.close()
            self._debug_dump('Rx', rx_mbap)
            raise BaseModbusClient._NetworkError(4, 'MBAP checking error')

    def check_response_pdu_body(self, rx_pdu, min_len):
        # check function code from recv PDU
        rx_function_code = struct.unpack('B', rx_pdu[0:1])[0]
        self.pdu_body_logging(rx_pdu, "Response")
        if rx_function_code != 3 and rx_function_code != 6:
            raise BaseModbusClient._NetworkError(4, 'Function code is not 3 or 6')

        # check PDU length for global minimal frame (an except frame: func code + exp code)
        if len(rx_pdu) < 2:
            raise BaseModbusClient._NetworkError(4, 'PDU length is too short')
        # extract function code
        rx_fc = rx_pdu[0]
        # check except status
        if rx_fc >= 0x80:
            exp_code = rx_pdu[1]
            raise BaseModbusClient._ModbusExcept(exp_code)
        # check PDU length for specific request set in min_len (keep this after except checking)
        if len(rx_pdu) < min_len:
            raise BaseModbusClient._NetworkError(4, 'PDU length is too short for current request')

    @staticmethod
    def mbap_header_logging(transaction_id, protocol_id, length, unit_id, packet_type):
        logging.info(f"{packet_type} header:")
        logging.info(f"{packet_type}_TID: {transaction_id}")
        logging.info(f"{packet_type}_PID: {protocol_id}")
        logging.info(f"{packet_type}_LF: {length}")
        logging.info(f"{packet_type}_UID: {unit_id}")
        logging.info("----------------------------------")

    @staticmethod
    def pdu_body_logging(pdu_body, packet_type):
        function_code = struct.unpack('B', pdu_body[0:1])[0]
        logging.info(f"{packet_type} PDU:")
        logging.info(f"{packet_type}_FC: {function_code}")
        logging.info("---------------------------------")
