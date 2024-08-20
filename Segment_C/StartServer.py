# segment_c: server
import os
import time
import random
from pyModbusTCP.server import DataBank, DataHandler
from CustomModbusServer import CustomModbusServer, ReadMsgS1
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

# Initialize DataBank to manage Modbus data space
data_bank = DataBank(
    coils_size=0, coils_default_value=False,
    d_inputs_size=0, d_inputs_default_value=False,
    h_regs_size=100, h_regs_default_value=0,
    i_regs_size=0, i_regs_default_value=0
)
print("DataBank is initialized")

# Generate initial random values for holding registers
initial_values = [random.randint(0, 1000) for _ in range(100)]
data_bank.set_holding_registers(0, initial_values)

# Initialize Modbus servers
modbus_server_name = os.getenv('MODBUS_SERVER_NAME', 'localhost')
server = CustomModbusServer(host=modbus_server_name, port=502, data_bank=data_bank, no_block=True)
request_handler = DataHandler(data_bank=data_bank)

try:
    print("Modbus TCP Server is starting up")
    server.start()
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping Modbus TCP Server...")
    server.stop()
    logging.info(f"Hidden Message {ReadMsgS1.hidden_message_s1}")
    print("Modbus TCP Server is stopped")
