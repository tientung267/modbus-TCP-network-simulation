## 1. Which base image do you want to use?
FROM python:3.11-slim

## 2. Set the working directory.
WORKDIR /app
## After step 2 every thing happen inside /app

## 3. copy content of current directory(Segment_c) folder into /app directory
COPY . .

# 4. Install nftables
RUN apt-get update && apt-get install -y nftables && apt-get clean && rm -rf /var/lib/apt/lists/*

## 5. Install the dependencies
RUN pip install -r requirements.txt

## 6. Apply firewall rules
RUN chmod +x firewall-rules.sh

## 6. Set Environment variable
ENV MODBUS_CLIENT_NAME=modbus-client
ENV MODBUS_CLIENT_PORT=3000

## 8. Expose Port to other applications
# EXPOSE 3000

## 9. Define the command to run when the container starts.
CMD ["python", "-u", "StartClient.py"]

#-u option to force unbuffered output