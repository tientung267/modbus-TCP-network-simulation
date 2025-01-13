import re
import logging
import statistics
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

class ModbusLogAnalyser:
    def __init__(self, file_path):
        # Open and read the log file
        self._log_data = self._read_log_file(file_path)

    @staticmethod
    def _read_log_file(file_path):
        with open(file_path, 'r') as file:
            return file.read()

    def PacketCounter(self):
        """
        At endpoints(client and server) the transaction id of request, and it's corresponding response must be the same

        """
        # Regular expression to find all transaction_ids of requests in the log
        transaction_ids_req_str = re.findall(r'Request_TID: (\d+)', self._log_data)
        # Convert to integers for further analysis
        logging.info(f"Number of Packet found: {len (transaction_ids_req_str)}" )


proxyAnalyser = ModbusLogAnalyser("NetworktrafficWithInterPacketTimes/proxy-server.log")
proxyAnalyser.PacketCounter()
logging.info("------------------------------------------------------------------")
clientAnalyser = ModbusLogAnalyser("NetworktrafficWithInterPacketTimes/modbus-client.log")
clientAnalyser.PacketCounter()
logging.info("------------------------------------------------------------------")
serverAnalyser = ModbusLogAnalyser("NetworktrafficWithInterPacketTimes/modbus-server.log")
serverAnalyser.PacketCounter()