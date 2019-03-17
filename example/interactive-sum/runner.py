#!/usr/bin/env python3

# Imports
import sys
import random

# Constants
N = 10
M = 100

# Command arguments
seed, send_fd, recv_fd = map(int, sys.argv[1:])

# Seed the RNG
random.seed(seed)

# Open send pipe
with open(send_fd, 'w', buffering=1) as send:

    # Print number of test cases
    print(N, file=send)

    # Open recv pipe
    with open(recv_fd, 'r', buffering=1) as recv:

        # Loop over attempts
        for _ in range(N):

            # Send input
            a = random.randint(0, M)
            b = random.randint(0, M)
            print(a, b, file=send)

            # Check output
            line = recv.readline()
            try:
                assert a + b == int(line)
            except AssertionError:
                print('FAILED')
            except Exception:
                print('ERROR')
            else:
                print('PASSED')
