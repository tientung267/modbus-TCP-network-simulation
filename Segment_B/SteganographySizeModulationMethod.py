import struct
import logging
import sys
from constants import DUMMY_EMBEDDED_BYTE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

def add_one_byte_response(mbap_header_tuple, function_code, pdu_body_raw):
    """Scenario: response is received at the gateway server and is added 1 byte at the end of the message"""

    (transaction_id, protocol_id, length, unit_id) = mbap_header_tuple

    new_mbap_header = struct.pack('>HHHB', transaction_id, protocol_id, length + 1, unit_id)

    if function_code == 3:
        (function_code, byte_count, value) = struct.unpack('>BBH', pdu_body_raw)

        new_pdu_body = struct.pack('>BBH', function_code, byte_count + 1, value)
        return new_mbap_header + new_pdu_body + struct.pack('B', 3)

    return new_mbap_header + pdu_body_raw + struct.pack('B', 3)

def add_one_byte_request(mbap_header_tuple, function_code, pdu_body_raw):
    """Scenario: request from client is received at the gateway server and is added 1 byte at the end of the message"""
    (transaction_id, protocol_id, length, unit_id) = mbap_header_tuple

    if function_code == 3 or function_code == 6:
        new_mbap_header = struct.pack('>HHHB', transaction_id, protocol_id, length + 1, unit_id)

        return new_mbap_header + pdu_body_raw + struct.pack('B', DUMMY_EMBEDDED_BYTE)


class S1SizeModulation:
    """This class represent steganography size modulation. It tries to hide a sequence of bits (e.g: 100101) in the
    modbus communication. Each bit will represent by the length(even or odd) of pdu payload of one modbus/TCP Paket"""

    def __init__(self):
        self._counter = 0
        self._embedded_message = ''

    def increment_after(func):
        """
        Decorator to increment the counter after executing the method.
        """

        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)  # Call the method
            self._counter += 1  # Increment the counter after the method call
            return result

        return wrapper

    @increment_after
    def s1_size_modulation(self, modbus_message, request):
        """
        This function modifies field length in MBAP header of modbus/TCP package. An odd length will
        represent an 1 and an even length will represent an 0. The pdu payload will also be adapted to match new
        length.

        :param modbus_message: the modbus/TCP packet to encoded bit of hidden message
        :param request: determine, if this modbus/TCP packet is a request from client

        :returns: modbus/TCP packet after modification
        """
        mbap_header = modbus_message[:7]
        pdu_body = modbus_message[7:]

        # header contains (transaction_id, protocol_id, length, unit_id)
        mbap_header_tuple = struct.unpack('>HHHB', mbap_header)

        function_code = struct.unpack('B', pdu_body[:1])[0]

        current_bit = self._embedded_message[self._counter]

        # If the length matches the representation of current bit in embedded message, do nothing
        if int(current_bit) == mbap_header_tuple[2] % 2 or not request:
            logging.info(f"current bit {current_bit}, payload length {mbap_header_tuple[2]}")
            return modbus_message
        else:
            # E.g: If the length is odd but current bit is 0 and need to be represented by even length, one dummy
            # byte will be added to payload and the length will be increased by 1 and vice versa
            logging.info(f"current bit {current_bit}, payload length {mbap_header_tuple[2]}, 1 byte will be added")
            return add_one_byte_request(mbap_header_tuple, function_code, pdu_body)

    def set_embedded_message(self, steganography_message):
        """The steganography message will be converted in a sequence of bits. Each Character of the message (
        including space character) will be converted in it corresponding number in ASCII table. After that this
        number will be represented by a sequence of 7 bits. The first 10 bits in the sequence represent the number of
        characters in the steganography message (including space character)."""

        # Calculate the number of characters in the message
        message_length = len(steganography_message) * 7
        logging.info(f"message length {message_length}")
        # Convert the length to an 10-bit binary representation
        length_binary = format(message_length, '010b')
        logging.info(f"length binary {length_binary}")
        # Convert each character in the text to its ASCII value and then to binary
        binary_representation = ''.join(format(ord(char), '07b') for char in steganography_message)
        self._embedded_message = length_binary + binary_representation
        logging.info(f"embedded message (without header) {binary_representation}")

    @property
    def embedded_message(self):
        return self._embedded_message
