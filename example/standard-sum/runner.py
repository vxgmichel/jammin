#!/usr/bin/env python3

# Imports
import sys
import random

# Constants
N = 10
M = 10**9

# Command arguments
seed, send_path, recv_path = map(int, sys.argv[1:])

# Seed the RNG
random.seed(seed)

# Open send pipe
with open(send_path, 'w', buffering=1) as send:

    # Print number of test cases
    print(N, file=send)

    # Generate data in
    data_in = [0]
    for i in range(1, N):
        n = random.randint(i*10**(i-1), 10**i-1)
        data_in.append(n)
    assert len(data_in) == N

    # Print data in
    for n in data_in:
        print(n, file=send)


# Open recv pipe
with open(recv_path, 'r', buffering=1) as recv:

    # Loop over attempts
    for n in data_in:
        # Check output
        result = n * (n + 1) // 2
        line = recv.readline()
        try:
            assert result == int(line)
        except AssertionError:
            print('FAILED')
        except Exception:
            print('ERROR')
        else:
            print('PASSED')
