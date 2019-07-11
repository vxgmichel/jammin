import os
import random
import asyncio
from datetime import datetime
from asyncio.subprocess import PIPE
from asyncio.streams import FlowControlMixin
from contextlib import asynccontextmanager

SEED_RANGE = 1000
RUNNERS = {}


@asynccontextmanager
async def prompt_to_pipe(first_line, aprompt, runner):

    async def target():
        line = first_line
        while True:
            runner.last_received_line = datetime.now()
            runner.pipe_writer.write((line + os.linesep).encode())
            await runner.pipe_writer.drain()
            try:
                line = await aprompt()
            except EOFError:
                return

    try:
        task = asyncio.create_task(target())
        yield task
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def create_pipe_reader(path):
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    pipe = open(path, "r")
    await loop.connect_read_pipe(lambda: protocol, pipe)
    return reader


async def create_pipe_writer(path):
    loop = asyncio.get_event_loop()
    protocol = FlowControlMixin()
    pipe = open(path, "w")
    transport, _ = await loop.connect_write_pipe(lambda: protocol, pipe)
    writer = asyncio.StreamWriter(transport, protocol, None, loop)
    # Return reader and writers
    return writer


async def create_runner(user, runner_program):
    runner = RUNNERS.get(user)
    if runner:
        try:
            runner.terminate()
        except ProcessLookupError:
            pass
        else:
            await runner.wait()

    # Generate a seed
    seed = random.randrange(0, SEED_RANGE)

    # Create pipe for input data
    input_read, input_write = os.pipe()
    os.set_inheritable(input_write, True)

    # Create pipe for output data
    output_read, output_write = os.pipe()
    os.set_inheritable(output_read, True)

    # Start the runner process
    runner = await asyncio.create_subprocess_exec(
        str(runner_program),
        f"{seed}",
        f"{input_write}",
        f"{output_read}",
        stdin=PIPE,
        stdout=PIPE,
        close_fds=False)

    # Close file descriptors
    os.close(input_write)
    os.close(output_read)

    # Connect to pipes
    runner.pipe_reader = await create_pipe_reader(input_read)
    runner.pipe_writer = await create_pipe_writer(output_write)

    # Set and return
    RUNNERS[user] = runner
    return runner


async def get_runner(user):
    return RUNNERS[user]
