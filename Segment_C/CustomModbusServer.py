import struct
from pyModbusTCP.constants import READ_HOLDING_REGISTERS, EXP_DATA_VALUE
from pyModbusTCP.server import ModbusServer as BaseModbusServer
import socket
import logging
import sys

logger = logging.getLogger('pyModbusTCP.server')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

HEADER_BITS_LENGTH = 10

class ReadMsgS1:
    """This class is used to extract hidden messages from Gateway Server embedded with size-modulation methods"""
    hidden_message_s1 = ''
    msg_bits = ''
    bits_message_counter = 0
    stop_read_msg = False

    @staticmethod
    def resolve_hidden_message_s1(length):
        """
        this method resolves and add bit to the result string `hidden_message_s1`. A modbus/TCP packet with even length
        represents a bit 1 and a modbus/TCP packet with odd length represents a bit 0.

        :param length: length of received modbus/TCP packet from client
        """
        # Read the header of hidden message
        if len(ReadMsgS1.msg_bits) < HEADER_BITS_LENGTH:
            ReadMsgS1.resolve_length_message(length)
        # Read the real hidden message
        else:
            if ReadMsgS1.bits_message_counter > 0:
                if length % 2 == 1:
                    ReadMsgS1.hidden_message_s1 += '1'
                else:
                    ReadMsgS1.hidden_message_s1 += '0'

                ReadMsgS1.bits_message_counter -= 1
                logging.info(f"read hidden message: {ReadMsgS1.hidden_message_s1}")
            else:
                logging.info(f"top read hidden message: {ReadMsgS1.hidden_message_s1}")
                ReadMsgS1.stop_read_msg = True

    @classmethod
    def resolve_length_message(cls, length):
        """
        The first 10 bits of hidden message represent the number of bits following. there will be maximum 1023 bits can
        be sent with 10 bits in header

        :param length: the length of current modbus/TCP packet
        """
        if length % 2 == 1:
            cls.msg_bits += '1'
        else:
            cls.msg_bits += '0'
        if len(cls.msg_bits) == HEADER_BITS_LENGTH:
            cls.bits_message_counter = int(cls.msg_bits, 2)
            logging.info(f"number of bits to read: {cls.bits_message_counter}")


class CustomModbusServer(BaseModbusServer):
    class SessionData:
        """ Container class for server session data. """

        def __init__(self):
            self.client = CustomModbusServer.ClientInfo()
            self.request = CustomModbusServer.Frame()
            self.response = CustomModbusServer.Frame()

        @property
        def srv_info(self):
            info = CustomModbusServer.ServerInfo()
            info.client = self.client
            info.recv_frame = self.request
            return info

        def new_request(self):
            self.request = CustomModbusServer.Frame()
            self.response = CustomModbusServer.Frame()

        def set_response_mbap(self):
            self.response.mbap.transaction_id = self.request.mbap.transaction_id
            self.response.mbap.protocol_id = self.request.mbap.protocol_id
            self.response.mbap.unit_id = self.request.mbap.unit_id

    class Frame(BaseModbusServer.Frame):
        def __init__(self):
            """ Modbus Frame container. """
            self.mbap = CustomModbusServer.MBAP()
            self.pdu = CustomModbusServer.PDU()

        @property
        def raw(self):
            self.mbap.length = len(self.pdu) + 1
            return self.mbap.raw + self.pdu.raw

    class ModbusService(BaseModbusServer.ModbusService):
        @property
        def server_running(self):
            return self.server.evt_running.is_set()

        def _send_all(self, data):  # Override this method in gateway to send request to the next server
            try:
                self.request.sendall(data)
                return True
            except socket.timeout:
                return False

        def _recv_all(self, size):
            data = b''
            while len(data) < size:
                try:
                    # avoid keeping this TCP thread run after server.stop() on main server
                    if not self.server_running:
                        raise BaseModbusServer.NetworkError('main server is not running')
                    # recv all data or a chunk of it
                    data_chunk = self.request.recv(size - len(data))
                    # check data chunk
                    if data_chunk:
                        data += data_chunk
                    else:
                        raise BaseModbusServer.NetworkError('recv return null')
                except socket.timeout:
                    # just redo main server run test and recv operations on timeout
                    pass
            return data

        def setup(self):
            # set a socket timeout of 1s on blocking operations (like send/recv)
            # this avoids hang thread deletion when main server exit (see _recv_all method)
            self.request.settimeout(1.0)

        def handle(self):
            # try/except end current thread on ModbusServer._InternalError or socket.error
            # this also close the current TCP session associated with it
            # init and update server info structure
            session_data = CustomModbusServer.SessionData()
            (session_data.client.address, session_data.client.port) = self.request.getpeername()
            # debug message
            logger.debug('Accept new connection from %r', session_data.client)
            try:
                # main processing loop
                while True:
                    # init session data for new request
                    session_data.new_request()

                    # Application-layer filtering: Check and set mbap header if valid @raw.setter from MBAP class
                    session_data.request.mbap.raw = self._recv_all(7)

                    # receive mbap from client
                    logger.info("A request is received")

                    request_pdu = self._recv_all(session_data.request.mbap.length - 1)

                    # Application-layer filtering: Check and set pdu header if valid @raw.setter from PDU class
                    self.request_pdu_filter(request_pdu)

                    session_data.request.pdu.raw = request_pdu

                    # update response MBAP fields with request data
                    session_data.set_response_mbap()
                    # pass the current session data to request engine
                    self.server.engine(session_data)
                    # send the tx pdu with the last rx mbap (only length field change)
                    self._send_all(session_data.response.raw)
                    logger.info("-----------------------------------------\n\n")
            except (BaseModbusServer.Error, socket.error) as e:
                # debug message
                logger.debug('Exception during request handling: %r', e)
                # on main loop except: exit from it and cleanly close the current socket
                self.request.close()

        @staticmethod
        def request_pdu_filter(request_pdu_body):
            function_code = struct.unpack('B', request_pdu_body[:1])[0]
            # logging.info(f"function code in response: {function_code}")
            if function_code != 3 and function_code != 6:
                raise BaseModbusServer.NetworkError(4, 'Function code is not 3 or 6')

            # check PDU length for global minimal frame (an except frame: func code + exp code)
            if len(request_pdu_body) < 4:
                raise BaseModbusServer.NetworkError(4, 'PDU length is too short')

    class MBAP(BaseModbusServer.MBAP):
        @property
        def raw(self):
            try:
                return struct.pack('>HHHB', self.transaction_id,
                                   self.protocol_id, self.length,
                                   self.unit_id)
            except struct.error as e:
                raise BaseModbusServer.DataFormatError('MBAP raw encode pack error: %s' % e)

        @raw.setter
        def raw(self, value):
            # close connection if no standard 7 bytes mbap header
            if not (value and len(value) == 7):
                raise BaseModbusServer.DataFormatError('MBAP must have a length of 7 bytes')
            # decode header
            (self.transaction_id, self.protocol_id,
             self.length, self.unit_id) = struct.unpack('>HHHB', value)
            self.mbap_header_logging(self.transaction_id,
                                     self.protocol_id,
                                     self.length,
                                     self.unit_id,
                                     "request header: ")
            if not ReadMsgS1.stop_read_msg:
                ReadMsgS1.resolve_hidden_message_s1(self.length)
            # check frame header content inconsistency
            if self.protocol_id != 0:
                raise BaseModbusServer.DataFormatError('MBAP protocol ID must be 0')
            if not 2 < self.length < 256:
                raise BaseModbusServer.DataFormatError('MBAP length must be between 2 and 256')

        @staticmethod
        def mbap_header_logging(transaction_id, protocol_id, length, unit_id, message):
            logging.info(message)
            logging.info(f"transaction_id: {transaction_id}")
            logging.info(f"protocol_id: {protocol_id}")
            logging.info(f"length: {length}")
            logging.info(f"unit_id: {unit_id}")

    def _read_words(self, session_data):
        """
        Functions Read Holding Registers (0x03) or Read Input Registers (0x04).

        :param session_data: server engine data
        :type session_data: ModbusServer.SessionData
        """
        # pdu alias,
        # Alias meaning when send_pdu is changed, session_data.response.pdu is changed
        recv_pdu = session_data.request.pdu
        send_pdu = session_data.response.pdu
        # print("recv_pdu ", recv_pdu.raw)
        # print("send_pdu", type(send_pdu))
        # decode pdu
        (start_addr, quantity_regs) = recv_pdu.unpack('>HH', from_byte=1, to_byte=5)
        self.pdu_body_logging(recv_pdu.func_code,
                              start_addr,
                              "read from register: ",
                              quantity_regs,
                              "number of register: ",
                              "pdu body of request to read holding registers")
        # check quantity of requested words
        if 0x0001 <= quantity_regs <= 0x007D:
            # data handler read request: for holding or input registers space
            if recv_pdu.func_code == READ_HOLDING_REGISTERS:
                ret_hdl = self.data_hdl.read_h_regs(start_addr, quantity_regs, session_data.srv_info)
            else:
                ret_hdl = self.data_hdl.read_i_regs(start_addr, quantity_regs, session_data.srv_info)
            # format regular or except response
            if ret_hdl.ok:
                # build pdu
                send_pdu.add_pack('BB', recv_pdu.func_code, quantity_regs * 2)
                # add_pack requested words
                send_pdu.add_pack('>%dH' % len(ret_hdl.data), *ret_hdl.data)
                self.pdu_body_logging(recv_pdu.func_code,
                                      ret_hdl.data[0],
                                      "read value: ",
                                      quantity_regs,
                                      "number of register: ",
                                      "response from read single register request")
            else:
                send_pdu.build_except(recv_pdu.func_code, ret_hdl.exp_code)
        else:
            send_pdu.build_except(recv_pdu.func_code, EXP_DATA_VALUE)
        # print("send_pdu ", send_pdu.raw)

    def _write_single_register(self, session_data):
        """
        Functions Write Single Register (0x06).

        :param session_data: server engine data
        :type session_data: ModbusServer.SessionData
        """
        # pdu alias
        recv_pdu = session_data.request.pdu
        send_pdu = session_data.response.pdu
        # decode pdu
        (reg_addr, reg_value) = recv_pdu.unpack('>HH', from_byte=1, to_byte=5)
        self.pdu_body_logging(recv_pdu.func_code,
                              reg_addr,
                              "write to register ",
                              reg_value,
                              "written value ",
                              "pdu body of request to write single register")
        # data handler update request
        ret_hdl = self.data_hdl.write_h_regs(reg_addr, [reg_value], session_data.srv_info)
        # format regular or except response
        if ret_hdl.ok:
            send_pdu.add_pack('>BHH', recv_pdu.func_code, reg_addr, reg_value)
            self.pdu_body_logging(recv_pdu.func_code,
                                  reg_addr,
                                  "register address ",
                                  reg_value,
                                  "writen value ",
                                  "response from write single register request")
        else:
            send_pdu.build_except(recv_pdu.func_code, ret_hdl.exp_code)

    @staticmethod
    def pdu_body_logging(function_code, value_1, msg_value_1, value_2, msg_value_2, msg_pdu_body):
        logging.info(msg_pdu_body)
        logging.info(f"function_code: {function_code}")
        logging.info(f"{msg_value_1}: {value_1}")
        logging.info(f"{msg_value_2}: {value_2}")
