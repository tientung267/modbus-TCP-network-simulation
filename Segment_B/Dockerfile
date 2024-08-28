## 1. Which base image do you want to use?
FROM python:3.11-slim

## 2. Set the working directory.
WORKDIR /app
## After step 2 every thing happen inside /app

## 3. copy content of current directory (Segment_B) directory into /app directory
COPY . .

## 4. Install the dependencies
RUN pip install -r  requirements.txt

## 5. Document and inform the developer that the application will use PORT 500 of the container.
EXPOSE 500

## 6. Set envrionment variables
ENV GATEWAY_SERVER_NAME=gateway-server
ENV MODBUS_SERVER_NAME=modbus-server

## 7. Define the command to run when the container starts.
CMD ["python", "-u", "StartGatewayServer.py"]

#-u option to force unbuffered output