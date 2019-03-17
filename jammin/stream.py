

from prompt_toolkit.input.posix_pipe import PosixPipeInput
from prompt_toolkit.layout.screen import Size
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText, to_formatted_text


def to_text(val):
    if isinstance(val, list) and not isinstance(val, FormattedText):
        return to_formatted_text('{0}'.format(val))
    return to_formatted_text(val, auto_convert=True)


def to_fragments(values, sep, end):
    fragments = []
    for i, value in enumerate(values):
        fragments.extend(to_text(value))

        if sep and i != len(values) - 1:
            fragments.extend(to_text(sep))

    fragments.extend(to_text(end))
    return fragments


def create_raw_prompt(reader, writer):
    writer.flush = lambda: None

    def sprint(*values, sep=' ', end='\n', **kwargs):
        kwargs.setdefault("file", writer)
        fragments = to_fragments(values, sep, end)
        raw_text = ''.join(raw for _, raw in fragments)
        writer.write(raw_text.encode())

    async def aprint(*args, **kwargs):
        sprint(*args, **kwargs)
        await writer.drain()

    async def aprompt(prompt=None, **kwargs):
        if prompt:
            await aprint(prompt, end="")
        data = (await reader.readline()).decode()
        # Return or raise EOF
        if not data.endswith('\n'):
            raise EOFError
        return data.rstrip('\n')

    aprint.sprint = sprint
    return aprint, aprompt


async def create_full_prompt(process):
    # Mandatory from prompt_toolkit
    app = None
    use_asyncio_event_loop()

    # Size getter
    def get_size():
        width, height, _, _ = process.get_terminal_size()
        return Size(rows=height, columns=width)

    # Set up resize event
    def size_changed(*_):
        if app is not None:
            app.invalidate()
    process.terminal_size_changed = size_changed

    # Prepare input stream
    vt100_input = PosixPipeInput()
    await process.redirect_stdin(vt100_input._w)

    # Prepare output stream
    process.stdout.encoding = "utf-8"
    process.stdout.flush = lambda: None
    vt100_output = Vt100_Output(
        process.stdout,
        get_size,
        term=process.get_terminal_type())

    # Define local print

    def sprint(*args, **kwargs):
        kwargs.setdefault("output", vt100_output)
        print_formatted_text(*args, **kwargs)

    async def aprint(*args, **kwargs):
        sprint(*args, **kwargs)
        await process.stdout.drain()

    # Define local prompt

    async def aprompt(*args, **kwargs):
        nonlocal app
        kwargs['async_'] = True
        history = kwargs.pop('history', None)
        input = kwargs.pop('input', vt100_input)
        output = kwargs.pop('output', vt100_output)
        session = PromptSession(input=input, output=output, history=history)
        try:
            app = session.app
            return await session.prompt(*args, **kwargs)
        finally:
            app = None

    aprint.sprint = sprint
    return aprint, aprompt
