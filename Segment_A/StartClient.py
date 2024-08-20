import os
import time
import random
import logging
import sys
from CustomModbusClient import CustomModbusClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

gateway_server = os.getenv('GATEWAY_SERVER_NAME', 'localhost')
SERVER_PORT = 500
REQUEST_DURATION = 600

client = CustomModbusClient(host=gateway_server, port=SERVER_PORT, auto_open=True)


def read_holding_register():
    """A random holding register will be read from Server. For this experiment, we will only consider reading single
        holding register. The result will be logged out when response arrives"""
    try:
        reading_address = random.randint(starting_address, starting_address + 99)

        result = client.read_holding_registers(reading_address, register_num_to_read)
        if result:
            logging.info(f"Read from address {reading_address}: {result} \n\n")
        else:
            logging.error(f"Failed to read from address {reading_address}")
    except Exception as e:
        logging.error(f"Error during reading registers: {e}")


def write_single_register():
    """writing a random value into a holding register. The result will be logged out when response arrives"""
    try:
        writing_address = random.randint(starting_address, starting_address + 99)
        random_writing_value = random.randint(0, 1000)
        success = client.write_single_register(writing_address, random_writing_value)
        if success:
            logging.info(f"Wrote value {random_writing_value} to address {writing_address} \n\n")
        else:
            logging.error(f"Failed to write to address {writing_address}")
    except Exception as e:
        logging.error(f"Error during writing registers: {e}")


try:
    # Check if client is opened for connection. If not, try to open a new connection
    if not client.is_open:
        if not client.open():
            logging.error(f"Failed to connect to {gateway_server}:{SERVER_PORT}")
            sys.exit(1)

    starting_address = 0  # There are 100 holding registers in databank at server. There index start with 0
    register_num_to_read = 1  # In this experiment we only consider reading single holding register
    start_time = time.time()  # Time when the connection starts
    counter = 0  # The read and write single holding register request will be sent interleaved to server

    while time.time() - start_time < REQUEST_DURATION:
        if client.is_open:
            if counter % 2 == 0:
                read_holding_register()
            elif counter % 2 == 1:
                write_single_register()
            else:
                logging.error("Invalid command value")
                continue

            counter += 1
            time.sleep(1)
        else:
            logging.error(f"Connection to {gateway_server}:{SERVER_PORT} is not open \n")
            logging.info(f"Try to connect again...")
            client.open()

finally:
    client.close()
    logging.info("Client connection closed.")
