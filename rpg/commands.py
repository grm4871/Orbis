"""
Handlers for the RPG commands.
"""

from .command_parser import CommandParser

parser = CommandParser("?")


@parser.command(aliases="h", help_text="show this help message")
async def help(ctx, command=None):
    ...
