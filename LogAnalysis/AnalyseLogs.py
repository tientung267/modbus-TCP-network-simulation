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
        # Regular expression to find all transaction_ids in the log
        transaction_ids_str = re.findall(r'transaction_id: (\d+)', self._log_data)
        transaction_ids_int = list(map(int, transaction_ids_str))
        # Convert to integers for further analysis
        transaction_ids = [int(tid) for tid in transaction_ids_int]

        # Print extracted transaction IDs
        logging.info(f"Extracted Transaction IDs:{transaction_ids}")
        transaction_ids_requests = transaction_ids[::2]

        is_transaction_id_matching = True  # Check if all transaction_id from request match transaction_id from response
        for i in range(0, len(transaction_ids) - 1, 2):
            if transaction_ids[i] != transaction_ids[i + 1]:
                is_transaction_id_matching = False
        if is_transaction_id_matching:
            logging.info("All transaction IDs match!")
        else:
            logging.error("Transaction ID mismatch")

        # Check if the transactionIDs increase by 1 for each new request
        is_tid_incremented_by_1 = True
        for i in range(0, len(transaction_ids_requests) - 1):
            if transaction_ids_requests[i] != transaction_ids_requests[i + 1] - 1:
                logging.warning(f"Transaction ID is not increased by 1: "
                                f"{transaction_ids_requests[i]} and "
                                f"{transaction_ids_requests[i + 1]}")
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
        # Regular expression to find all transaction_ids in the log
        transaction_ids_str = re.findall(r'transaction_id: (\d+)', self._log_data)
        transaction_ids_int = list(map(int, transaction_ids_str))
        # Convert to integers for further analysis
        transaction_ids = [int(tid) for tid in transaction_ids_int]

        # Print extracted transaction IDs
        logging.info(f"Extracted Transaction IDs:{transaction_ids}")
        transaction_ids_requests = transaction_ids[::2]
        logging.info(f"Extracted Transaction IDs in requests:{transaction_ids_requests}")
        is_transaction_id_matching = True
        # Check if all transaction_id from request match transaction_id from response before normalisation
        for i in range(0, len(transaction_ids) - 1, 2):
            if transaction_ids[i] != (transaction_ids[i + 1] + 1):
                is_transaction_id_matching = False
        if is_transaction_id_matching:
            logging.info("All transaction IDs match!")
        else:
            logging.error("Transaction ID mismatch")

        # Check if the transactionIDs increase by 1 for each new request
        is_tid_incremented_by_1 = True
        for i in range(0, len(transaction_ids_requests) - 1):
            if transaction_ids_requests[i] != (transaction_ids_requests[i + 1] - 1):
                logging.warning(f"Transaction ID is not increased by 1: "
                                f"{transaction_ids_requests[i]} and "
                                f"{transaction_ids_requests[i + 1]}")
                is_tid_incremented_by_1 = False

        if is_tid_incremented_by_1:
            logging.info("All TIDs are incremented by 1 from previous TID")
        else:
            logging.warning("Some TIDs are increased different from previous TID")

    def analyse_protocol_id(self):
        protocol_ids = re.findall(r'protocol_id: (\d+)', self._log_data)
        is_protocol_id_zero = True
        for i in range(len(protocol_ids)):
            if protocol_ids[i] != '0':
                logging.warning(f"Protocol ID is not 0 for tid {i}: PID {protocol_ids[i]}")
                is_protocol_id_zero = False

        if is_protocol_id_zero:
            logging.info("All protocol IDs are zero")
        else:
            logging.warning("Some protocol IDs are not zero")

    def analyse_unit_id(self):
        # In this experiment we only have one modbus-client, so that the unit_id will always be 1
        uni_ids = re.findall(r'uni_id: (\d+)', self._log_data)
        is_uni_id_one = True
        for i in range(len(uni_ids)):
            if uni_ids[i] != 1:
                is_uni_id_one = False
                logging.warning(f"Unit ID is not 1 for tid {i}: UID {uni_ids[i]}")
        if is_uni_id_one:
            logging.info("All unit IDs are one")
        else:
            logging.warning("Some unit IDs are not one")

    def analyse_payload_length(self):
        """
        calculate mean and standard deviation of lengths:

        mean: summing all the values and then dividing by the number of values.

        standard deviation: Standard deviation measures how spread out the values in a data set are from the mean.
        A low standard deviation means the data points are close to the mean, while a high standard deviation indicates
        they are spread out over a wider range.
        """
        payload_lengths = re.findall(r'length:\s*(\d+)', self._log_data)
        payload_length_requests = list(map(int, payload_lengths[::2]))
        payload_length_responses = list(map(int, payload_lengths[1::2]))

        mean_length_requests = round(statistics.mean(payload_length_requests), 4)
        logging.info(f"Mean of all payload length in requests: {mean_length_requests}")

        mean_length_responses = round(statistics.mean(payload_length_responses), 4)
        logging.info(f"Mean of all payload length in responses: {mean_length_responses}")

        stdev_length_requests = round(statistics.stdev(payload_length_requests), 4)
        logging.info(f"standard deviation of all payload lengths in requests: {stdev_length_requests}")

        stdev_length_responses = round(statistics.stdev(payload_length_responses), 4)
        logging.info(f"standard deviation of all payload lengths in responses: {stdev_length_responses}")

    def analysing_rtt(self):
        round_trip_times_str = re.findall(r'(?i)round-trip-time.*:\s*(\d+\.\d*)', self._log_data)
        print(len(round_trip_times_str))
        rtt_int_list = list(map(float, round_trip_times_str))
        mean_rtt = round(statistics.mean(rtt_int_list), 4)
        logging.info(f"Mean of all RTT values: {mean_rtt}")

        stdev_rtt = round(statistics.stdev(rtt_int_list), 4)
        logging.info(f"Standard deviation of all RTT values: {stdev_rtt}")

    def run_analysis_on_proxy_logs(self):
        """Run all analysis"""
        self.analyse_transaction_id_proxy()
        self.analyse_protocol_id()
        self.analyse_unit_id()
        self.analyse_payload_length()
        self.analysing_rtt()

    def run_analysis_on_endpoint_logs(self):
        self.analyse_transaction_id_endpoints()
        self.analyse_protocol_id()
        self.analyse_unit_id()
        self.analyse_payload_length()
        self.analysing_rtt()


proxyAnalyser = ModbusLogAnalyser("./NetworkCommunicationWithT1/proxy-server.log")
proxyAnalyser.run_analysis_on_proxy_logs()
