import csv
import statistics

# Define the IPs to filter
client_ip = "192.168.0.211"
server_ip = "192.168.0.212"

# Load the exported packets
file_path = "./NetworktrafficWaterBoilingExperiment/experiment1.csv"
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
    if (query['Source'] == client_ip and query['Destination'] == server_ip and
        response['Source'] == server_ip and response['Destination'] == client_ip):
        if int(response['No.']) - int(query['No.']) == 1:
            # Append pair with response timestamp
            pairs.append((query, response, response['Time']))
            rtts.append(float(response['Time']))

# Output the pairs with response time
for query, response, response_time in pairs:
    print(f"Query No. {query['No.']} paired with Response No. {response['No.']}, Response Time: {response_time}")

print(f"Mean RTT: {statistics.mean(rtts)}")