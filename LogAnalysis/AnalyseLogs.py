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

    def analyse_transaction_id_endpoints(self):
        """
        At endpoints(client and server) the transaction id of request, and it's corresponding response must be the same

        """
        # Regular expression to find all transaction_ids of requests in the log
        transaction_ids_req_str = re.findall(r'Request_TID: (\d+)', self._log_data)
        # Convert to integers for further analysis
        transaction_ids_req_int = list(map(int, transaction_ids_req_str))
        print(transaction_ids_req_int)

        # Regular expression to find all transaction_ids of responses in the log
        transaction_ids_resp_str = re.findall(r'Response_TID: (\d+)', self._log_data)
        # Convert to integers for further analysis
        transaction_ids_resp_int = list(map(int, transaction_ids_resp_str))

        is_transaction_id_matching = True  # Check if all transaction_id from request match transaction_id from response
        for i in range(0, len(transaction_ids_req_int) - 1, 1):
            if transaction_ids_req_int[i] != transaction_ids_resp_int[i]:
                is_transaction_id_matching = False
        if is_transaction_id_matching:
            logging.info("All transaction IDs match!")
        else:
            logging.error("Transaction ID mismatch")

        # Check if the transactionIDs increase by 1 for each new request
        is_tid_incremented_by_1 = True
        for i in range(0, len(transaction_ids_req_int) - 1):
            if transaction_ids_req_int[i] != transaction_ids_req_int[i + 1] - 1:
                logging.warning(f"Transaction ID is not increased by 1: "
                                f"{transaction_ids_req_int[i]} and "
                                f"{transaction_ids_req_int[i + 1]}")
                is_tid_incremented_by_1 = False

        if is_tid_incremented_by_1:
            logging.info("All TIDs are incremented by 1 from previous TID")
        else:
            logging.warning("Some TIDs are increased different from previous TID")

    def analyse_transaction_id_server(self):
        """
        At endpoints(client and server) the transaction id of request, and it's corresponding response must be the same

        """
        # Regular expression to find all transaction_ids of requests in the log
        transaction_ids_req_str = re.findall(r'Request_TID: (\d+)', self._log_data)

        # Convert to integers for further analysis
        transaction_ids_req_int = list(map(int, transaction_ids_req_str))

        # Check if the transactionIDs increase by 1 for each new request
        is_tid_incremented_by_1 = True
        for i in range(0, len(transaction_ids_req_int) - 1):
            if transaction_ids_req_int[i] != transaction_ids_req_int[i + 1] - 1:
                logging.warning(f"Transaction ID is not increased by 1: "
                                f"{transaction_ids_req_int[i]} and "
                                f"{transaction_ids_req_int[i + 1]}")
                is_tid_incremented_by_1 = False

        if is_tid_incremented_by_1:
            logging.info("All TIDs are incremented by 1 from previous TID")
        else:
            logging.warning("Some TIDs are increased different from previous TID")

    def analyse_transaction_id_proxy(self):
        """
        At proxy-server the transaction id will be normalised, it will be decreased by 1 if the packet travel from client
        to server and increased by 1 if the packet travel from server to client.
        """
        # Regular expression to find all transaction_ids of req in the log
        transaction_ids_req_str = re.findall(r'Request_TID: (\d+)', self._log_data)

        # Convert to integers for further analysis
        transaction_ids_req_int = list(map(int, transaction_ids_req_str))

        # Check if the transactionIDs increase by 1 for each new request
        is_tid_incremented_by_1 = True
        for i in range(0, len(transaction_ids_req_int) - 1):
            if transaction_ids_req_int[i] != (transaction_ids_req_int[i + 1] - 1):
                logging.warning(f"Transaction ID is not increased by 1: "
                                f"{transaction_ids_req_int[i]} and "
                                f"{transaction_ids_req_int[i + 1]}")
                is_tid_incremented_by_1 = False

        if is_tid_incremented_by_1:
            logging.info("All TIDs are incremented by 1 from previous TID")
        else:
            logging.warning("Some TIDs are increased different from previous TID")

    def analyse_protocol_id(self, check_response):
        protocol_ids_request = list(map(int, re.findall(r'Request_PID: (\d+)', self._log_data)))

        protocol_ids_response = []
        if check_response:
            protocol_ids_response = list(map(int, re.findall(r'Response_PID: (\d+)', self._log_data)))

        is_protocol_id_zero = True
        for i in range(len(protocol_ids_request)):
            if protocol_ids_request[i] != 0:
                logging.warning(f"Protocol ID in Request is not 0 for tid {i}: PID {protocol_ids_request[i]}")
                is_protocol_id_zero = False
            if check_response:
                if protocol_ids_response[i] != 0:
                    logging.warning(f"Protocol ID in Request is not 0 for tid {i}: PID {protocol_ids_response[i]}")
                    is_protocol_id_zero = False

        if is_protocol_id_zero:
            logging.info("All protocol IDs are zero")
        else:
            logging.warning("Some protocol IDs are not zero")

    def analyse_unit_id(self, check_response):
        # In this experiment we only have one modbus-client, so that the unit_id will always be 1
        unit_ids_request = list(map(int, re.findall(r'Request_UID: (\d+)', self._log_data)))

        unit_ids_response=[]
        if check_response:
            unit_ids_response = list(map(int, re.findall(r'Response_UID: (\d+)', self._log_data)))

        is_uni_id_one = True
        for i in range(len(unit_ids_request)):
            if unit_ids_request[i] != 1:
                is_uni_id_one = False
                logging.warning(f"Unit ID is not 1 for tid {i}: UID {unit_ids_request[i]}")
            if check_response:
                if unit_ids_response[i] != 1:
                    is_uni_id_one = False
                    logging.warning(f"Unit ID is not 1 for tid {i}: UID {unit_ids_response[i]}")
        if is_uni_id_one:
            logging.info("All unit IDs are one")
        else:
            logging.warning("Some unit IDs are not one")

    def analyse_payload_length(self, check_response):
        """
        calculate mean and standard deviation of lengths:

        mean: summing all the values and then dividing by the number of values.

        standard deviation: Standard deviation measures how spread out the values in a data set are from the mean.
        A low standard deviation means the data points are close to the mean, while a high standard deviation indicates
        they are spread out over a wider range.
        """
        payload_length_requests = list(map(int, re.findall(r'Request_LF:\s*(\d+)', self._log_data)))

        mean_length_requests = round(statistics.mean(payload_length_requests), 4)
        logging.info(f"Mean of all payload length in requests: {mean_length_requests}")

        stdev_length_requests = round(statistics.stdev(payload_length_requests), 9)
        logging.info(f"standard deviation of all payload lengths in requests: {stdev_length_requests}")

        if check_response:
            payload_length_responses = list(map(int, re.findall(r'Response_LF:\s*(\d+)', self._log_data)))

            mean_length_responses = round(statistics.mean(payload_length_responses), 4)
            logging.info(f"Mean of all payload length in responses: {mean_length_responses}")

            stdev_length_responses = round(statistics.stdev(payload_length_responses), 4)
            logging.info(f"standard deviation of all payload lengths in responses: {stdev_length_responses}")

    def analysing_rtt(self):
        round_trip_times_str = re.findall(r'(?i)round-trip-time.*:\s*(\d+\.\d*)', self._log_data)

        rtt_int_list = list(map(float, round_trip_times_str))
        print(rtt_int_list)
        mean_rtt = round(statistics.mean(rtt_int_list), 4)
        logging.info(f"Mean of all RTT values: {mean_rtt}")

        stdev_rtt = round(statistics.stdev(rtt_int_list), 4)
        logging.info(f"Standard deviation of all RTT values: {stdev_rtt}")

    def run_analysis_on_proxy_logs(self):
        """Run all analysis"""
        self.analyse_transaction_id_proxy()
        self.analyse_protocol_id(True)
        self.analyse_unit_id(True)
        self.analyse_payload_length(True)
        self.analysing_rtt()

    def run_analysis_on_client_logs(self):
        self.analyse_transaction_id_endpoints()
        self.analyse_protocol_id(True)
        self.analyse_unit_id(True)
        self.analyse_payload_length(True)
        self.analysing_rtt()

    def run_analysis_on_server_logs(self):
        # On server transaction_id isn't checked, because of caching, some packet will not arrive server at all.
        self.analyse_protocol_id(False)
        self.analyse_unit_id(False)
        self.analyse_payload_length(False)
        self.analysing_rtt()


proxyAnalyser = ModbusLogAnalyser("./NetworkCommunicationWithT1/proxy-server.log")
proxyAnalyser.run_analysis_on_proxy_logs()
logging.info("------------------------------------------------------------------")
clientAnalyser = ModbusLogAnalyser("./NetworkCommunicationWithT1/modbus-client.log")
clientAnalyser.run_analysis_on_client_logs()
logging.info("------------------------------------------------------------------")
serverAnalyser = ModbusLogAnalyser("./NetworkCommunicationWithT1/modbus-server.log")
serverAnalyser.run_analysis_on_server_logs()