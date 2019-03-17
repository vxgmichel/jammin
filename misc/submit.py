#!/usr/bin/env python3

import sys
import socket
import subprocess

# Unpack arguments
_, hostname, port, token, *command = sys.argv

# Initialize request connection
request_connection = socket.create_connection((hostname, port))
request_connection.send("request {}\n".format(token).encode())

# Initialize submit connection
submit_connection = socket.create_connection((hostname, port))
submit_connection.send("submit {}\n".format(token).encode())

# Run solver process
process = subprocess.run(
    command,
    stdin=request_connection,
    stdout=submit_connection,
    shell=True, check=True)

# Print status
with submit_connection.makefile("r", buffering=1) as f:
    for line in f:
        print(line, end='')
