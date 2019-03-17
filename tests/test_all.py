
import asyncio

import pytest
from jammin.server import amain

RUNNER = """\
import sys
seed, send_fd, recv_fd = map(int, sys.argv[1:])

with open(send_fd, "w") as f:
    print(seed, file=f)

with open(recv_fd, "r") as f:
    line = f.readline()
    try:
        value = int(line)
    except ValueError:
        print("ERROR")
    else:
        print("PASSED" if value == seed ** 2 else "FAILED")
"""

SOLVER = """\
print(int(input()) ** 2)
"""


@pytest.fixture
@pytest.mark.asyncio
async def server():
    namespace = type("namespace", (), {})
    namespace.ssh_port = 0
    namespace.tcp_port = 0
    namespace.max_seed = 10
    namespace.ntests = None
    namespace.interactive = False
    namespace.runner = ["python", "-c", RUNNER]
    namespace.solver = ["python", "-c", SOLVER]
    namespace.started = asyncio.Event()

    # Wait for server to be started
    task = asyncio.create_task(amain(namespace))
    await namespace.started.wait()

    yield namespace

    # Stop the server
    try:
        task.cancel()
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_tcp_submission(server):

    # Claim user
    reader, writer = await asyncio.open_connection(
        "localhost", server.tcp_port)
    writer.write("claim test\n".encode())
    token = (await reader.read()).decode().strip()
    assert len(token) == 10

    # Request input data
    reader, writer = await asyncio.open_connection(
        "localhost", server.tcp_port)
    writer.write(f"request {token}\n".encode())
    data_in = (await reader.read()).decode().strip()

    # Solve
    data_out = f"{int(data_in) ** 2}\n"

    # Submit output data
    reader, writer = await asyncio.open_connection(
        "localhost", server.tcp_port)
    writer.write(f"submit {token}\n{data_out}".encode())
    status = (await reader.read()).decode().strip()

    # Check status
    assert status.endswith("1 / 1")
