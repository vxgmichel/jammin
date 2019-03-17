import pathlib
import asyncssh


from .command import run_command
from .exception import log_exception
from .stream import create_raw_prompt, create_full_prompt


async def ssh_handler(process):
    # Make sure the process is closed before exiting
    async with process:

        # Get terminal info
        command = process.get_command()
        term = process.get_terminal_type()
        interactive = term is not None

        try:

            # Get the prompt functions
            if interactive:
                aprint, aprompt = await create_full_prompt(process)
            else:
                aprint, aprompt = create_raw_prompt(
                    process.stdin, process.stdout)

            # Run the handler
            status = await run_command(
                command, aprint, aprompt)
            process.exit(status or 0)

        # Exit cleanly
        except EOFError:
            pass
        except Exception:
            log_exception()
            process.exit(-1)


# AsyncSSH server

class NoAuthSSHServer(asyncssh.SSHServer):
    """An ssh server without authentification."""

    def begin_auth(self, username):
        return False


def ensure_key(filename="ssh_host_key"):
    path = pathlib.Path(filename)
    if not path.exists():
        rsa_key = asyncssh.generate_private_key("ssh-rsa")
        path.write_bytes(rsa_key.export_private_key())
    return str(path)


async def start_ssh_server(host="0.0.0.0", port=0):
    return await asyncssh.create_server(
        NoAuthSSHServer,
        host,
        port,
        encoding=None,
        line_editor=False,
        server_host_keys=[ensure_key()],
        process_factory=ssh_handler,
    )
