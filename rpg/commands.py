"""
Handlers for the RPG commands.
"""

from . import rpg_instance
from .command_parser import CommandParser

parser = CommandParser("?")


@parser.command(aliases="h", help_text="show this help message")
async def help(ctx):
    response = "**Commands:**\n"
    for command in parser.commands:
        help_text = get_command_help(command)
        if help_text is not None:
            response += "\n" + help_text
    await ctx.send(response)


def get_command_help(command):
    """Make the help text for a given command.

    :param rpg.command_parser.Command command: the command
    :return: the help text, or ``None`` if this command has no help
    :rtype: str|None
    """
    if command.help_text is None:
        return None

    text = ' or '.join(f"`{parser.prefix}{a}`" for a in command.aliases)
    text += ":  " + command.help_text
    return text


@parser.command(aliases="i", help_text="show your inventory")
async def inventory(ctx):
    player = rpg_instance.fetchplayer(ctx.user.id, ctx.user.name)
    await ctx.send(f"```{player.showinventory()}```")
    rpg_instance.save()
