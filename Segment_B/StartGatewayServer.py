import socket
import struct
import sys
import threading
from Caching import Caching
from ProtocolNormalisation import ProtocolNormalisation
from RateLimiting import RateLimiting
from SteganographySizeModulationMethod import S1SizeModulation
from SteganographyInterPacketTimesMethod import T1InterPacketTimes
from constants import (SOCKET_TIMEOUTS, NUM_CLIENT, S1_STEG_MESS, T1_STEG_MESS, SLEEP_DURATION, NUM_BITS_CHARACTER,
                       NUM_BITS_HEADER)
import logging
import time
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

def mbap_header_logging(transaction_id, protocol_id, length, unit_id, source):
    """Log out the header of a modbus/TCP packet"""
    logging.info(f"{source} header:")
    logging.info(f"transaction_id: {transaction_id}")
    logging.info(f"protocol_id: {protocol_id}")
    logging.info(f"length: {length}")
    logging.info(f"unit_id: {unit_id}")
    logging.info("----------------------------------")

def pdu_body_logging(function_code, pdu_body, request):
    """Log out the pdu payload of a modbus/TCP packet"""
    if function_code == 3:
        # Read holding Register, only one register is read each time
        if request:
            pdu_body_truncate = pdu_body[:4]
            logging.info("Request PDU:")
            (starting_address, quantity_to_read) = struct.unpack(">HH", pdu_body_truncate)
            logging.info(f"starting_address: {starting_address}")
            logging.info(f"quantity_to_read: {quantity_to_read}")
        else:
            pdu_body_truncate = pdu_body[:3]
            logging.info("Response PDU:")
            (num_bytes_to_read, read_value) = struct.unpack(">BH", pdu_body_truncate)
            logging.info(f"num_bytes_to_read: {num_bytes_to_read}")
            logging.info(f"read_value: {read_value}")
    elif function_code == 6:
        # write holding register, in this experiment, only one register value is written each time
        pdu_body_truncate = pdu_body[:4]
        if request:
            logging.info("Protocol Data Unit of Request:")
        else:
            logging.info("Protocol Data Unit of Response:")
        (writing_address, writing_value) = struct.unpack(">HH", pdu_body_truncate)
        logging.info(f"writing_address: {writing_address}")
        logging.info(f"writing_value: {writing_value}")
    logging.info(f"function_code: {function_code}")
    logging.info("----------------------------------")

def calculate_and_log_rtt(response_source, forward_response_time, receive_request_time):
    """ Utility for calculating RTT"""
    logging.info(f"Forward response from {response_source} to modbus-client")
    logging.info(f"Round-Trip-Time at gateway-server: {forward_response_time - receive_request_time}\n\n")

def connect_to_server(server_address):
    """Connect gateway server with modbus server"""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect(server_address)
        return server_socket
    except Exception as e:
        logging.error(f"Error: {e} while connecting to {server_address}")

def apply_size_modulation():
    if os.getenv('APPLY_SIZE_MODULATION', False):
        steg_s1 = S1SizeModulation()
        steg_s1.set_embedded_message(S1_STEG_MESS)
        logging.info("applying size modulation")
        # Each character in steganography will be encoded by 8 bits, which represent ASCII number of that character.
        # 8 first bits represent number of characters in the message
        num_bits_embed = len(S1_STEG_MESS) * NUM_BITS_CHARACTER + NUM_BITS_HEADER
        return steg_s1, num_bits_embed
    return None, 0

def apply_inter_packet_times():
    if os.getenv('APPLY_INTER_PACKET_TIMES', False):
        steg_t1 = T1InterPacketTimes(T1_STEG_MESS)
        logging.info("applying inter packet times")
        # Each character in steganography will be encoded by 8 bits, which represent ASCII number of that character.
        # 8 first bits represent number of characters in the message
        num_bits_embed = len(T1_STEG_MESS) * NUM_BITS_CHARACTER + NUM_BITS_HEADER
        return steg_t1, num_bits_embed
    return None, 0

def close_connection(client_socket, server_socket):
    """close connection from gateway server to modbus-client and modbus-server"""
    client_socket.close()
    logging.info("Client socket closed")
    server_socket.close()
    logging.info("Server socket closed")

def handle_client(client_socket, server_address):
    """Handle communication between client and server."""

    # Create a socket to communicate with the actual server
    server_socket = connect_to_server(server_address)

    # Network will be throttled every 30 seconds. The throttling last for 10 seconds.
    # In this ten seconds period, each request will be delayed for 1 seconds
    rate_limiting = RateLimiting()
    gateway_cache = Caching()
    # Object to apply steganography methode size modulation
    steg_s1, num_bits_embedded_s1 = apply_size_modulation()
    # Object to apply steganography methode inter-packet-times
    steg_t1, num_bits_embedded_t1 = apply_inter_packet_times()
    try:
        while True:
            # receive request from client
            modbus_client_request = client_socket.recv(1024)
            # Time when the Modbus/TCP request is received
            receive_request_time = time.time()
            logging.info(f"Request arrives gateway server at {receive_request_time}")

            request_mbap_header = modbus_client_request[:7]
            request_pdu_body = modbus_client_request[7:]

            (transaction_id, protocol_id, length, unit_id) = struct.unpack('>HHHB', request_mbap_header)
            function_code = struct.unpack('B', request_pdu_body[:1])[0]
            mbap_header_logging(transaction_id, protocol_id, length, unit_id, "Request")
            pdu_body_logging(function_code, request_pdu_body[1:], True)

            # Check in cache if register value is available
            if function_code == 3:
                response_from_cache = gateway_cache.check_if_value_in_cache(request_pdu_body,
                                                                            transaction_id,
                                                                            protocol_id,
                                                                            unit_id)
                if response_from_cache is not None:
                    receive_response_time = time.time()
                    calculate_and_log_rtt("cache",
                                          receive_response_time,
                                          receive_request_time)
                    client_socket.sendall(response_from_cache)
                    continue
            elif function_code == 6:
                # If an existing value in cache is overwritten, this value will be removed from cache
                function_code, writing_address, value = struct.unpack('>BHH', request_pdu_body)
                gateway_cache.clean_cache(writing_address)
                logging.info(f"cache after being cleaned {gateway_cache.cache}")

            if steg_s1 is not None and num_bits_embedded_s1 > 0:
                # embed steganography in request
                embedded_request = steg_s1.s1_size_modulation(modbus_client_request, True)
                num_bits_embedded_s1 -= 1
                request_mbap_header = embedded_request[:7]
                request_pdu_body = embedded_request[7:]

            if steg_t1 is not None and num_bits_embedded_t1 > 0:
                # Check if steganography delaying is applicable. Delaying is not always applied, only when (encoded
                # bit is 0 and function code of current packet is 6) or (encoded bit is 1 and function code of
                # current packet is 3)
                if steg_t1.apply_delay(function_code):
                    num_bits_embedded_t1 -= 1

            # Check if we should start the network throttling period
            if rate_limiting.check_in_delay_period():
                time.sleep(SLEEP_DURATION)

            # Protocol normalisation is applied. Example scenario: in Client the transaction id starts with 1 but in
            # Server the transaction_id starts with 0 -> Protocol must be normalised
            normalised_request = ProtocolNormalisation.protocol_normalisation(request_mbap_header,
                                                                              request_pdu_body,
                                                                              True)

            # Forwarding Request to Server
            server_socket.sendall(
                normalised_request
            )
            logging.info("Request is forwarded to server")

            # Receive response from server
            modbus_server_response = server_socket.recv(1024)

            response_mbap_header = modbus_server_response[:7]
            (transaction_id_res,
             protocol_id_res,
             length_res,
             unit_id_res) = struct.unpack('>HHHB', response_mbap_header)

            mbap_header_logging(transaction_id_res,
                                protocol_id_res,
                                length_res,
                                unit_id_res,
                                "Response")

            response_pdu_body = modbus_server_response[7:]
            function_code = struct.unpack('B', response_pdu_body[:1])[0]
            pdu_body_logging(function_code, response_pdu_body[1:], False)

            if function_code == 3:
                (_, read_address, _) = struct.unpack('>BHH', request_pdu_body[:5])
                (_, _, read_data) = struct.unpack('>BBH', modbus_server_response[7:11])
                gateway_cache.set_cache_data(read_address, read_data)
                logging.info(f"New value added to cache: {gateway_cache.cache}")

            # Protocol normalisation from response from server to request
            normalised_response = ProtocolNormalisation.protocol_normalisation(response_mbap_header,
                                                                               response_pdu_body,
                                                                               False)

            # Forward response from server to client
            client_socket.sendall(normalised_response)
            # Time when the Modbus/TCP response is received
            forward_response_time = time.time()
            calculate_and_log_rtt("modbus-server", forward_response_time, receive_request_time)
    except Exception as e:
        logging.error(f"Error: {e} \n...Connection will be terminated\n")
    finally:
        close_connection(client_socket, server_socket)

def start_gateway(host='localhost', port=500, server_address=('localhost', 502)):
    """Start the gateway server. Gateway server is a socket, which receives request from Modbus-Client and forwards it
        to the Modbus-Server. The Response from Server back to Client also has to go through gateway server. On the
        Server three mechanism will be applied: Caching, Network throttling in routine and protocol normalisation."""

    # Create a TCP/IP socket for the gateway server
    gateway_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gateway_socket.bind((host, port))
    gateway_socket.listen(NUM_CLIENT)
    gateway_socket.settimeout(SOCKET_TIMEOUTS)
    logging.info(f"Gateway server running on {host}:{port}, forwarding to server at {server_address}")

    try:
        while True:
            try:
                # Wait for a connection from a client
                client_socket, client_address = gateway_socket.accept()
                logging.info(f"Connection from client {client_address}")

                # Start a new thread to handle the client
                client_handler = threading.Thread(target=handle_client, args=(client_socket, server_address))
                client_handler.start()
            except socket.timeout:
                # Timeout occurs every 1.1 second, continue the loop and check for interrupt
                continue
    except KeyboardInterrupt:
        logging.info("Gateway server shutting down.")
    finally:
        gateway_socket.close()
        logging.info("Gateway server socket closed.")


# the environment variables will be set in docker-compose file
modbus_server_name = os.getenv('MODBUS_SERVER_NAME', 'localhost')
gateway_server_name = os.getenv('GATEWAY_SERVER_NAME', 'localhost')

# Start the gateway server
start_gateway(host=gateway_server_name, port=500, server_address=(modbus_server_name, 502))
