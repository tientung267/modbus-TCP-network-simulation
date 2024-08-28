## 1. Which base image do you want to use?
FROM python:3.11-slim

## 2. Set the working directory.
WORKDIR /app
## After step 2 every thing happen inside /app

## 3. copy content of current directory(Segment_c) directory into /app directory
COPY . .

## 4. Install the dependencies
RUN pip install -r  requirements.txt

## 5. Set envrionment variables
ENV MODBUS_SERVER_NAME=modbus-server

## 6. Document and inform the developer that the application will use PORT 502 of the container.
EXPOSE 502

## 7. Define the command to run when the container starts.
CMD ["python", "-u", "StartServer.py"]

#-u option to force unbuffered output