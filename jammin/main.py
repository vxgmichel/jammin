
import asyncio
import argparse

from .checklist import run_checklist
from .config import set_configuration
from .server import start_tcp_server, start_ssh_server


async def amain(namespace):
    set_configuration(namespace)

    await run_checklist(namespace.checks, namespace.maxseed)

    # TCP interface
    tcp_server = await start_tcp_server(namespace.tcp_port)
    tcp_addr = tcp_server.sockets[0].getsockname()
    print(f'Serving TCP interface on port {tcp_addr[1]}...')

    # SSH interface
    ssh_server = await start_ssh_server(namespace.ssh_port)
    ssh_addr = ssh_server.sockets[0].getsockname()
    print(f'Serving SSH interface on port {ssh_addr[1]}...')

    async with tcp_server, ssh_server:
        await tcp_server.serve_forever()


def main(args=None):

    parser = argparse.ArgumentParser(
        description='Competitive programming over ssh')

    parser.add_argument('-s', '--ssh-port', int, default=8022,
                        help='the maximum seed value')

    parser.add_argument('-t', '--tcp-port', int, default=8000,
                        help='the maximum seed value')

    parser.add_argument('-m', '--maxseed', int, default=1000,
                        help='the maximum seed value')

    parser.add_argument('-c', '--checks', int,
                        help='the number of seeds to check, defaults to all')

    parser.add_argument('-i', '--interactive', action="store_true",
                        help='indicates an interactive problem')

    parser.add_argument('runner', metavar='RUNNER', type=str,
                        help='the problem runner program')

    parser.add_argument('solver', metavar='SOLVER', type=str,
                        help='a valid solution')

    namespace = parser.parse_args(args)
    return asyncio.run(amain(namespace))
