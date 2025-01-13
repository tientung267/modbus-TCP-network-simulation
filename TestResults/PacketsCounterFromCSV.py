import csv
import statistics

# Define the IPs to filter
client_ip_simulation = "172.20.0.12"
proxy_ip_simulation = "172.20.0.11"
server_ip_simulation = "172.20.0.10"
client_ip_praxis_experiment = "192.168.0.211"
server_ip_praxis_experiment = "192.168.0.212"
# Load the exported packets
file_path = "./NetworkTrafficWithoutSteganography/SegmentB_.csv"
with open(file_path, 'r') as file:
    reader = csv.DictReader(file)
    packets = list(reader)

# Find query-response pairs
queries = []
responses = []
for i in range(len(packets) - 1):
    packet = packets[i]

    # Check if packets are from client to server and back
    if (packet['Source'] == proxy_ip_simulation and
            packet['Destination'] == server_ip_simulation):
        queries.append(packet)

    if (packet['Source'] == server_ip_simulation  and
            packet['Destination'] == proxy_ip_simulation):
        # Append pair with response timestamp
        responses.append(packet)

print(f"Number of queries found in this record: {len(queries)}\n"
      f"Number of responses found in this record: {len(responses)}")