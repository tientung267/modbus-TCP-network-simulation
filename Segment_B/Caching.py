import struct
import time
import logging
import sys
from constants import CACHE_TTL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])


class Caching:
    """This class simulates caching mechanism. when response from read single holding register arrives at proxy server
        , its value will be saved in cache. After an amount of time (10 seconds) this value will be removed, or when new
        value is written to this holding register."""

    def __init__(self):
        self._cache = {}  # Dictionary to store cache data

    @property
    def cache(self):
        return self._cache

    def _get_cached_data(self, register_index):
        """
        Retrieve data from cache if it exists and is still valid.

        :param register_index: address of read register

        :returns: Register value if the value exists in cache, otherwise None
        """
        current_time = time.time()
        if register_index in self._cache:
            initial_time, data = self._cache[register_index]
            if current_time - initial_time < CACHE_TTL:
                return data
        return None

    def set_cache_data(self, register_index, data):
        """Store data in cache."""
        self._cache[register_index] = (time.time(), data)

    def clean_cache(self, register_rewritten):
        """cleaning cache by removing expired data or rewritten data"""
        logging.info("Cache cleaning...")
        current_time = time.time()

        # Create a list of keys to delete
        keys_to_delete = []

        # Cache will be cleaned if the stored register value is expired or the value overwritten by write single
        # register request
        for register_index in self._cache.keys():
            (initial_time, data) = self._cache[register_index]
            if current_time - initial_time > CACHE_TTL or register_index == register_rewritten:
                logging.info(f"{register_index} is removed from Cache ")
                keys_to_delete.append(register_index)

        # Deleting chosen keys
        for key in keys_to_delete:
            del self._cache[key]

    def check_if_value_in_cache(self, pdu_body, transaction_id, protocol_id, unit_id):
        """If the value to read is in cache and valid, a response will be created and send back to client"""
        # Parse the address and quantity from the request
        function_code, start_address, quantity = struct.unpack('>BHH', pdu_body)

        # Check cache for the requested register
        if self._get_cached_data(start_address) is not None:
            cache_data = self._get_cached_data(start_address)
            # Build the Modbus response with cached data
            # length of pdu_body in response is 5 bytes: 1 byte function_code,
            # 2 byte length of read data, 2 byte for read data from 1 register
            length_pdu_response = 5
            response = (struct.pack('>HHHB', transaction_id, protocol_id, length_pdu_response, unit_id)
                        + struct.pack('>BBH', function_code, quantity * 2, cache_data))

            logging.info(f"cache hit, response from Cache:")
            logging.info(f"function_code: {function_code}")
            logging.info(f"register_address: {start_address}")
            logging.info(f"cache_value: {cache_data}")
            return response
        else:
            return None
