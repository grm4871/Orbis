"""
Code for parsing/processing user commands.
"""

import math
from inspect import signature, Parameter
from typing import NamedTuple, Callable, Awaitable, List

CommandHandler = Callable[..., Awaitable[None]]


class Command(NamedTuple):
    """A registered command, including its handler and metadata."""
    handler_func: CommandHandler
    aliases: List[str]
    min_num_args: int
    max_num_args: int
    help_text: str


class BadCommandDefinition(Exception):
    """A command definition is invalid."""
    pass


class CommandContext:
    """Context passed to command handler functions.

    :param discord.Message message: the message instance
    """

    def __init__(self, message):
        self.message = message
        self.user = message.author

    async def send(self, *args, **kwargs):
        """Send a message back to the channel the command was sent to.

        Arguments are forwarded to ``discord.abc.Messageable.send``.
        """
        await self.message.channel.send(*args, **kwargs)


class CommandParser:
    """Parses commands and allows the registration of handler functions.

    :param str prefix: the command prefix to look for
    """

    def __init__(self, prefix):
        self.prefix = prefix
        self.commands = []
        self._command_map = {}

    async def on_message(self, message):
        """Attempt to parse and handle a user command.

        :param discord.Message message: the message that was sent
        :return: True if the command was recognized and processed; False otherwise
        :rtype: bool
        """
        content = message.content
        if not content.startswith(self.prefix):
            return False  # no prefix; ignore

        words = content[len(self.prefix):].split()
        if len(words) == 0:
            return False  # nothing after the prefix; ignore

        cmd_word, *args = words
        if cmd_word in self._command_map:
            cmd = self._command_map[cmd_word]
            if cmd.min_num_args <= len(args) <= cmd.max_num_args:
                # call the handler function
                await cmd.handler_func(CommandContext(message), *args)
            else:
                # either too few or too many arguments were given;
                # send an error message
                if cmd.min_num_args == cmd.max_num_args:
                    expected = cmd.min_num_args
                else:
                    expected = f"{cmd.min_num_args}-{cmd.max_num_args}"
                given = f"{len(args)} argument"
                if len(args) != 1:
                    given += "s"
                await message.channel.send(
                    f"Command `{self.prefix}{cmd_word}` was given {given}, but expects {expected}")

        return True

    def command(self, *, aliases=None, help_text):
        """Decorator to register a command handler function.

        :param str|list[str]|None aliases: any aliases to register in addition to the function's name
        :param str|None help_text: the command's help description, or ``None`` to hide it from help
        """
        # convert the alias(es) to a list
        if aliases is None:
            aliases = []
        elif isinstance(aliases, str):
            aliases = [aliases]
        else:
            aliases = list(aliases)

        def decorator(func: CommandHandler):
            params = list(signature(func).parameters.values())
            if len(params) == 0:
                raise BadCommandDefinition("Handler function must take at least one parameter")

            # determine the minimum and maximum number of arguments
            min_num_args = 0
            max_num_args = len(params) - 1
            for p in params[1:]:
                if p.kind == Parameter.VAR_POSITIONAL:
                    max_num_args = math.inf
                elif p.default == Parameter.empty:
                    min_num_args += 1

            # add an entry to the tables of commands
            aliases.insert(0, func.__name__)
            cmd_entry = Command(func, aliases, min_num_args, max_num_args, help_text)
            self.commands.append(cmd_entry)
            for alias in aliases:
                if alias in self._command_map:
                    raise BadCommandDefinition(f'Alias "{self.prefix}{alias}" registered more than once')
                self._command_map[alias] = cmd_entry
            return func

        return decorator
