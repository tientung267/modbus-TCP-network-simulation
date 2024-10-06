import os
import time
import random
import logging
import sys
from CustomModbusClient import CustomModbusClient
from constants import STARTING_ADDRESS, REQUEST_DURATION, PROXY_SERVER_PORT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

proxy_server_name = os.getenv('PROXY_SERVER_NAME', 'localhost')

client = CustomModbusClient(host=proxy_server_name, port=PROXY_SERVER_PORT, auto_open=True)


def read_holding_register():
    """A random holding register will be read from Server. For this experiment, we will only consider reading single
        holding register. The result will be logged out when response arrives"""
    try:
        reading_address = random.randint(STARTING_ADDRESS, STARTING_ADDRESS + 99)
        logging.info(f"Request: Read {register_num_to_read} value(s) from register {reading_address}")
        result = client.read_holding_registers(reading_address, register_num_to_read)
        if result:
            logging.info(f"Response: value {result} is read from address {reading_address} \n\n")
        else:
            logging.error(f"Failed to read from address {reading_address}")
    except Exception as e:
        logging.error(f"Error during reading registers: {e}")


def write_single_register():
    """writing a random value into a holding register. The result will be logged out when response arrives"""
    try:
        writing_address = random.randint(STARTING_ADDRESS, STARTING_ADDRESS + 99)
        random_writing_value = random.randint(0, 1000)
        logging.info(f"Request: Write {random_writing_value} to register {writing_address}")
        success = client.write_single_register(writing_address, random_writing_value)
        if success:
            logging.info(f"Response: value {random_writing_value} is written to address {writing_address} \n\n")
        else:
            logging.error(f"Failed to write to address {writing_address}")
    except Exception as e:
        logging.error(f"Error during writing registers: {e}")


try:
    # Check if client is opened for connection. If not, try to open a new connection
    if not client.is_open:
        if not client.open():
            logging.error(f"Failed to connect to {proxy_server_name}:{PROXY_SERVER_PORT}")
            sys.exit(1)

    register_num_to_read = 1  # In this experiment we only consider reading single holding register
    start_time = time.time()  # Time when the connection starts
    counter = 0  # The read and write single holding register request will be sent interleaved to server

    while time.time() - start_time < REQUEST_DURATION:
        if not client.is_open:
            logging.error(f"Connection to {proxy_server_name}:{PROXY_SERVER_PORT} is not open \n")
            logging.info(f"Try to connect again...")
            client.open()
            continue

        if counter % 2 == 0:
            read_holding_register()
        else:
            write_single_register()

        counter += 1
        time.sleep(1)

finally:
    client.close()
    logging.info("Client connection closed.")
