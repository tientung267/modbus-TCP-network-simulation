import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

class T1InterPacketTimes:
    """This class represent steganography method inter-packet-time. It tries to hide a sequence of bits (e.g: 100101) in
        the modbus communication. Each bit will represent by a small delay of 250ms of modbus/TCP Paket"""

    def __init__(self, modbus_message=''):
        self._embedded_message = self.convert_steganography_message_to_bits(modbus_message)
        self._counter = 0

    @property
    def embedded_message(self):
        return self._embedded_message

    def apply_delay(self, function_code):
        """
        this function apply a small delay of 250ms on a Modbus/TCP packet. To encode bit 0, write single holding
        register Request (function code 6) will be delay for 250ms. To encode bit 1, read single holding register
        (function code 3) Request will be delay for 250ms.

        The _counter determines, which bit of the hidden message is currently encoded

        :param function_code: function_code of current modbus/TCP packet

        """
        bit = self._embedded_message[self._counter]
        delay_mapping = {'0': 6, '1': 3}

        if function_code == delay_mapping.get(bit):
            logging.info(f"Delaying 0.25ms for bit {bit}")
            time.sleep(0.25)
            self._counter += 1
            return True
        else:
            logging.warning(
                f"No delay for bit {self._embedded_message[self._counter]} and function code {function_code}")
            return False

    @staticmethod
    def convert_steganography_message_to_bits(steganography_message):
        """The steganography message will be converted in a sequence of bits. Each Character of the message (
                including space character) will be converted in it corresponding number in ASCII table. After that this
                number will be represented by a sequence of 7 bits. The first 10 bits in the sequence represent the number of
                characters in the steganography message (including space character)."""

        # Calculate the number of characters in the message
        message_length = len(steganography_message) * 7

        # Convert the length to an 8-bit binary representation
        length_binary = format(message_length, '010b')

        # Convert each character in the text to its ASCII value and then to binary
        binary_representation = ''.join(format(ord(char), '07b') for char in steganography_message)
        logging.info(f"binary embedded message (without header): {binary_representation}")
        return length_binary + binary_representation
