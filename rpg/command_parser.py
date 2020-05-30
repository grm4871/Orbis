"""
Code for parsing/processing user commands.
"""

import math
from inspect import signature, Parameter
from typing import NamedTuple, Callable, Awaitable, List, Optional

CommandHandler = Callable[..., Awaitable[None]]


class Command(NamedTuple):
    """A registered command, including its handler and metadata."""
    handler_func: CommandHandler
    aliases: List[str]
    min_num_args: int
    max_num_args: int
    rest_arg: Optional[str]
    help_text: Optional[str]
    usage_text: Optional[str]


class BadCommandDefinition(Exception):
    """A command definition is invalid."""
    pass


class CommandContext:
    """Context passed to command handler functions.

    :param discord.Message message: the message instance
    :param dict extra_attrs: extra attributes to be lazy-added
    """

    def __init__(self, message, extra_attrs):
        self.message = message
        self.user = message.author
        self._extra_attrs = extra_attrs

    def __getattr__(self, name):
        if name in self._extra_attrs:
            value = self._extra_attrs[name](self)
            setattr(self, name, value)
            return value
        else:
            raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    async def send(self, *args, **kwargs):
        """Send a message back to the channel the command was sent to.

        Arguments are forwarded to ``discord.abc.Messageable.send``.
        """
        return await self.message.channel.send(*args, **kwargs)


class CommandParser:
    """Parses commands and allows the registration of handler functions.

    :param str prefix: the command prefix to look for
    """

    def __init__(self, prefix):
        self.prefix = prefix
        self.commands = []
        self._command_map = {}
        self._context_attrs = {}

    def add_custom_context(self, attr_name, func):
        """Add a custom attribute to context objects passed to handlers.

        When a handler accesses the attribute, the specified function will be
        called to determine its value. (The function will only be called once
        per context; the result will be cached.)

        :param str attr_name: the name of the attribute to add
        :param (CommandContext) -> Any func: a function to generate the value
        """
        if attr_name in self._context_attrs:
            raise ValueError(f"Custom context attribute already added: {attr_name}")
        else:
            self._context_attrs[attr_name] = func

    async def on_message(self, message):
        """Attempt to parse and handle a user command.

        :param discord.Message message: the message that was sent
        :return: True if the command was recognized and processed; False otherwise
        :rtype: bool
        """
        content: str = message.content.strip()
        if not content.startswith(self.prefix):
            return False  # no prefix; ignore

        parts = content[len(self.prefix):].split(maxsplit=1)
        if len(parts) == 0:
            return False  # nothing after the prefix; ignore

        cmd_word = parts[0]
        args_str = parts[1] if len(parts) == 2 else ""
        if cmd_word in self._command_map:
            cmd: Command = self._command_map[cmd_word]
            if cmd.rest_arg is None:
                args = args_str.split()
            else:
                args = args_str.split(maxsplit=cmd.max_num_args-1)

            if cmd.min_num_args <= len(args) <= cmd.max_num_args:
                # call the handler function
                ctx = CommandContext(message, self._context_attrs)
                if cmd.rest_arg is not None and len(args) == cmd.max_num_args:
                    kwargs = {cmd.rest_arg: args.pop()}
                else:
                    kwargs = {}
                await cmd.handler_func(ctx, *args, **kwargs)
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
                    f"Command `{self.prefix}{cmd_word}` was given {given}, but expects {expected}\n" + cmd.usage_text)

        return True

    def command(self, *, aliases=None, help_text, usage_text=None):
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

        if usage_text: usage_text = "Usage: " + usage_text

        def decorator(func: CommandHandler):
            params = list(signature(func).parameters.values())

            # validate the first (context) parameter
            if len(params) == 0:
                raise BadCommandDefinition("Handler function must take at least one parameter")
            if params[0].kind not in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD):
                raise BadCommandDefinition("First parameter of handler function must be positional")

            # determine the number and kind of arguments
            min_num_args = 0
            max_num_args = 0
            rest_arg = None
            for p in params[1:]:
                if p.kind == Parameter.VAR_POSITIONAL:
                    max_num_args = math.inf
                else:
                    if p.kind == Parameter.KEYWORD_ONLY:
                        if max_num_args == math.inf:
                            raise BadCommandDefinition("Handler function must not have both types of rest parameter")
                        if rest_arg is not None:
                            raise BadCommandDefinition("Handler function must not have more than one keyword-only "
                                                       "parameter")
                        rest_arg = p.name
                    if p.default is Parameter.empty:
                        if min_num_args != max_num_args:
                            raise BadCommandDefinition("Handler function must not have a required parameter after an "
                                                       "optional one")
                        min_num_args += 1
                    max_num_args += 1

            # add an entry to the tables of commands
            aliases.insert(0, func.__name__)
            cmd_entry = Command(func, aliases, min_num_args, max_num_args, rest_arg, help_text, usage_text)
            self.commands.append(cmd_entry)
            for alias in aliases:
                if alias in self._command_map:
                    raise BadCommandDefinition(f'Alias "{self.prefix}{alias}" registered more than once')
                self._command_map[alias] = cmd_entry
            return func

        return decorator
