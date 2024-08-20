import struct
import time
import logging
import sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])


class Caching:
    """This class simulates caching mechanism. when response from read single holding register arrives at gateway server
        , its value will be saved in cache. After an amount of time (10 seconds) this value will be removed, or when new
        value is written to this holding register."""

    # Dictionary to store cache data
    cache = {}

    # Time-to-live of a cached value in the cache
    CACHE_TTL = 10

    @staticmethod
    def get_cached_data(register_index):
        """Retrieve data from cache if it exists and is still valid."""
        current_time = time.time()
        if register_index in Caching.cache:
            timestamp, data = Caching.cache[register_index]
            if current_time - timestamp < Caching.CACHE_TTL:
                return data
        return None

    @staticmethod
    def set_cache_data(register_index, data):
        """Store data in cache."""
        Caching.cache[register_index] = (time.time(), data)

    @staticmethod
    def clean_cache(register_rewritten):
        """cleaning cache by removing expired data or rewritten data"""
        logging.info("Cache cleaning...")
        current_time = time.time()

        # Create a list of keys to delete
        keys_to_delete = []

        # Cache will be cleaned if the stored register value is expired or the value overwritten by write single
        # register request
        for register_index in Caching.cache.keys():
            (timestamp, data) = Caching.cache[register_index]
            if current_time - timestamp > Caching.CACHE_TTL or register_index == register_rewritten:
                keys_to_delete.append(register_index)

        # Deleting chosen keys
        for key in keys_to_delete:
            del Caching.cache[key]

    @staticmethod
    def check_if_value_in_cache(pdu_body, transaction_id, protocol_id, unit_id):
        """If the value to read is in cache and valid, a response will be created and send back to client"""
        # Parse the address and quantity from the request
        function_code, start_address, quantity = struct.unpack('>BHH', pdu_body)

        # Check cache for the requested register
        if Caching.get_cached_data(start_address) is not None:
            cache_data = Caching.get_cached_data(start_address)
            # Build the Modbus response with cached data

            # length of pdu_body in response is 5 bytes: 1 byte function_code,
            # 2 byte length of read data, 2 byte for read data from 1 register
            length_pdu_response = 5
            response = (struct.pack('>HHHB', transaction_id, protocol_id, length_pdu_response, unit_id)
                        + struct.pack('>BBH', function_code, quantity * 2, cache_data))

            logging.info(f"cache hit: response from Cache {response} \n\n" )
            return response
        else:
            return None
