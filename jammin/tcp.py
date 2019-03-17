import asyncio

from .command import run_command
from .exception import log_exception
from .stream import create_raw_prompt


async def tcp_command_handler(reader, writer):
    aprint, aprompt = create_raw_prompt(reader, writer)
    try:
        command = await aprompt()
        await run_command(command, aprint, aprompt)
    except EOFError:
        pass
    except UnicodeDecodeError:
        await aprint("Please use UTF-8 encoding")
    except Exception:
        log_exception()
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except ConnectionResetError:
            pass


async def start_tcp_server(host="0.0.0.0", port=8000):
    return await asyncio.start_server(
        tcp_command_handler, host=host, port=port)
