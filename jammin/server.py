import signal
import asyncio
import argparse
from contextlib import contextmanager

from .tcp import start_tcp_server
from .ssh import start_ssh_server
from .configuration import set_configuration
from .db import DB


@contextmanager
def keyboard_interrupt_control(loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    try:
        loop.add_signal_handler(signal.SIGINT, loop.stop)
        yield
    finally:
        loop.remove_signal_handler(signal.SIGINT)


async def amain(namespace):
    db = await DB.init(challenges_dir=namespace.challenges, dburl=namespace.db)
    # b1 = await db.create_user('billy')
    # b2 = await db.create_user('bob')
    # # await db.create_user('billy')
    # b3 = await db.get_user('billy')
    # users = await db.get_users()
    # await db.create_attempt('billy', 'foo', False)
    # await db.create_attempt('billy', 'bar', True)
    # await db.create_attempt('bob', 'foo', False)
    # res = await db.get_user_attempts('billy')
    # res2 = await db.get_challenge_attempts('foo')
    # c = db.get_challenges()
    set_configuration(namespace)
    if not hasattr(namespace, "started"):
        namespace.started = asyncio.Event()

    # TCP interface
    tcp_server = await start_tcp_server(port=namespace.tcp_port)
    namespace.tcp_port = tcp_server.sockets[0].getsockname()[1]
    print(f'Serving TCP interface on port {namespace.tcp_port}...')

    # SSH interface
    ssh_server = await start_ssh_server(port=namespace.ssh_port)
    namespace.ssh_port = ssh_server.sockets[0].getsockname()[1]
    print(f'Serving SSH interface on port {namespace.ssh_port}...')

    # Tests
    # XXX: TODO

    with keyboard_interrupt_control():
        async with tcp_server, ssh_server:
            namespace.started.set()
            await tcp_server.serve_forever()


def main(args=None):

    parser = argparse.ArgumentParser(
        prog="jammin",
        description='Competitive programming over ssh')

    parser.add_argument('-s', '--ssh-port', type=int, default=8022,
                        help='port for the ssh interface')

    parser.add_argument('-t', '--tcp-port', type=int, default=8000,
                        help='port for the tcp interface')

    parser.add_argument('--db', default='sqlite:///db.sqlite',
                        help='Path to the database (default: sqlite:///db.sqlite)')

    parser.add_argument('--challenges', default='.',
                        help='Path to the directory containing the challenges (default: current directory)')

    namespace = parser.parse_args(args)
    return asyncio.run(amain(namespace))


if __name__ == "__main__":
    main()
