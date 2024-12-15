import csv
import statistics

# Define the IPs to filter
client_ip_simulation = "172.20.0.12"
proxy_ip_simulation = "172.20.0.11"
server_ip_simulation = "172.20.0.10"
client_ip_praxis_experiment = "192.168.0.211"
server_ip_praxis_experiment = "192.168.0.212"
# Load the exported packets
file_path = "./NetworkWithProxyMechanismsNoSteganography/DelayOf0,07/SegmentC.csv"
with open(file_path, 'r') as file:
    reader = csv.DictReader(file)
    packets = list(reader)

# Find query-response pairs
pairs = []
rtts = []
for i in range(len(packets) - 1):
    query = packets[i]
    response = packets[i + 1]

    # Check if packets are from client to server and back
    if (query['Source'] == proxy_ip_simulation and
            query['Destination'] == server_ip_simulation and
            response['Source'] == server_ip_simulation and
            response['Destination'] == proxy_ip_simulation):
        # Append pair with response timestamp
        pairs.append((query, response, response['Time']))
        rtts.append(float(response['Time']))

# Output the pairs with response time
for query, response, response_time in pairs:
    print(f"Query No. {query['No.']} paired with Response No. {response['No.']}, Response Time: {response_time}")

print(f"Mean RTT: {statistics.mean(rtts)}")
print(f"Number of packets calculated for mean: {len(rtts)}")