import shlex
import argparse
from datetime import datetime
from dataclasses import dataclass, field

import mdv

from prompt_toolkit import HTML, ANSI
from prompt_toolkit.styles import Style
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter

from pygments.lexers.shell import BashLexer
from prompt_toolkit.lexers import PygmentsLexer

from .timing import format_attempt
from .exception import log_exception
from .user import get_user, claim_user
from .configuration import get_configuration
from .runner import create_runner, get_runner, prompt_to_pipe


@dataclass
class Session:
    aprint: object
    aprompt: object
    interactive: bool = False
    configuration: object = field(default_factory=get_configuration)


def get_command_dict():
    return {
        "help": (help_command, help_parser),
        "show": (show_command, show_parser),
        "claim": (claim_command, claim_parser),
        "request": (request_command, request_parser),
        "submit": (submit_command, submit_parser),
        "interact": (interact_command, interact_parser),
    }


def get_command(name, aprint):
    command, get_parser = get_command_dict()[name]
    parser = get_parser()

    # Patch print_message so the parser prints to our console
    parser._print_message = lambda message, file=None: \
        message and aprint.sprint(message, end="")

    return command, parser


async def run_command(command, aprint, aprompt, interactive=False):

    # Interact by default
    if not command:
        command = "interact"

    # Shell-like parsing
    try:
        name, *args = shlex.split(command)
    except ValueError:
        await aprint("Invalid shell-like syntax")
        return

    # Get corresponding command
    try:
        corofn, parser = get_command(name, aprint)
    except KeyError:
        await aprint(f"Unknown command {name}")
        return

    # Parse arguments
    try:
        namespace = parser.parse_args(args)
    except SystemExit:
        return

    # Run command
    try:
        session = Session(aprint, aprompt, interactive)
        status = await corofn(session, **vars(namespace))
    except EOFError:
        raise
    except Exception as exc:
        await aprint(f"Command {name} failed: {exc}")
        log_exception()
        return 1

    # Return status
    return status


# Help command

def help_parser():
    parser = argparse.ArgumentParser(
        prog="help",
        description='Show the help message')
    return parser


async def help_command(session):

    await session.aprint(HTML(
        "<skyblue>Welcome this SSH problem solving interface! :)</skyblue>"))
    await session.aprint()
    await session.aprint("""Here the list of commands:""")
    for name, (_, get_parser) in get_command_dict().items():
        await session.aprint(f" - {name:9s}: {get_parser().description}")
    await session.aprint()


# Show command

def show_parser():
    parser = argparse.ArgumentParser(
        prog="show",
        description='Show the problem description')
    return parser


async def show_command(session):
    columns = session.aprompt.get_size().columns
    with open(session.configuration.description) as f:
        data = mdv.main(f.read(), cols=columns)
    await session.aprint(ANSI(data))


# Claim command

def claim_parser():
    parser = argparse.ArgumentParser(
        prog="claim",
        description='Request new input data')
    parser.add_argument(
        'username', metavar='USER', type=str,
        help='Claim a username and receive a token')
    return parser


async def claim_command(session, username):
    # Get user
    try:
        token = claim_user(username)
    except ValueError:
        await session.aprint(
            "This user name is already taken :)")
        return 1

    if not session.interactive:
        await session.aprint(token)
        return

    await session.aprint(
        "Here's your token :)\n"
        "\n"
        f"    {token}"
        "\n")


# Request command

def request_parser():
    parser = argparse.ArgumentParser(
        prog="request",
        description='Request a new input dataset')
    parser.add_argument(
        'token', metavar='TOKEN', type=str, help='User token')
    return parser


async def request_command(session, token):

    # Check session
    if session.configuration.interactive and session.interactive:
        await session.aprint(
            "This is an interative problem, "
            "there is no dataset to request")
        return 3

    # Get user
    try:
        user = get_user(token)
    except KeyError:
        await session.aprint(
            "Authentification failed: this token is not valid :(")
        return 2

    # Get input data
    runner = await create_runner(user, session.configuration.runner)

    # Get timestamp for the first sent line
    first_line = await runner.pipe_reader.readline()
    runner.first_sent_line = datetime.now()
    await session.aprint(first_line.decode(), end='')

    # Loop over lines
    async for line in runner.pipe_reader:
        await session.aprint(line.decode(), end='')


# Submit

def submit_parser():
    parser = argparse.ArgumentParser(
        prog="submit",
        description='Submit output data for latest request input data')
    parser.add_argument(
        'token', metavar='TOKEN', type=str, help='User token')
    return parser


async def submit_command(session, token):
    # Char dict
    char_dict = {
        "passed": ".",
        "failed": "F",
        "error": "E",
        "skip": "S"}

    # Get user
    try:
        user = get_user(token)
    except KeyError:
        await session.aprint(
            "Authentification failed: this token is not valid :(")
        return 2

    # Interactive mode on interactive problem
    if session.configuration.interactive and session.interactive:
        await session.aprint("Not implemented at the moment!")

    # Allow for early abort
    first_line = await session.aprompt()

    # Get runner
    runner = await get_runner(user)

    # Pipe output data
    async with prompt_to_pipe(first_line, session.aprompt, runner):

        # Count the tests
        passed_tests = 0
        total_tests = 0

        # Get results
        async for line in runner.stdout:
            result = line.decode().strip().lower()
            char = char_dict.get(result, '?')
            await session.aprint(char, end='')

            # Count the tests
            total_tests += 1
            if char == '.':
                passed_tests += 1

    status = format_attempt(runner.first_sent_line, runner.last_received_line)
    status += f" {passed_tests} / {total_tests}"
    await session.aprint("\n" + status)

    # Signal failure
    if passed_tests != total_tests:
        return 1

    # All good!
    return 0


# Interact

def interact_parser():
    parser = argparse.ArgumentParser(
        prog="interact",
        description='Run an interactive session')
    return parser


async def interact_command(session):
    # Show help
    await help_command(session)

    # Already an interactive session
    if session.interactive:
        return

    history = InMemoryHistory()
    lexer = PygmentsLexer(BashLexer)
    completer = WordCompleter(
        ["claim", "request", "submit", "interact"], sentence=True)
    style = Style.from_dict({
        'completion-menu.completion': 'bg:#008888 #ffffff',
        'completion-menu.completion.current': 'bg:#00aaaa #000000',
        'scrollbar.background': 'bg:#88aaaa',
        'scrollbar.button': 'bg:#222222',
    })

    def bottom_toolbar():
        return HTML('This is a <b><style bg="ansired">Toolbar</style></b>!')

    while True:
        try:
            command = await session.aprompt(
                HTML("<b>>>> </b>"),
                history=history,
                lexer=lexer,
                completer=completer,
                style=style,
                bottom_toolbar=bottom_toolbar,
                complete_while_typing=True)
            await run_command(
                command, session.aprint, session.aprompt, interactive=True)
        except KeyboardInterrupt:
            pass
