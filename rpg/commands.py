"""
Handlers for the RPG commands.
"""

from main import check_cooldown, server_registered
from . import rpg_instance
from .command_parser import CommandParser

parser = CommandParser("?")
parser.add_custom_context("player", lambda ctx: rpg_instance.fetchplayer(ctx.user.id, ctx.user.name))


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
    await ctx.send(f"```{ctx.player.showinventory()}```")
    rpg_instance.save()


@parser.command(aliases="s", help_text="show your stats/equipment")
async def stats(ctx):
    await ctx.send(f"```{ctx.player.showstats()}```")
    rpg_instance.save()


@parser.command(help_text="show your current area")
async def area(ctx):
    await ctx.send(f"You are in: `{ctx.player.showarea()}`")
    rpg_instance.save()


@parser.command(aliases="a", help_text="battle a random monster in your current area")
async def adventure(ctx):
    if await check_cooldown(ctx.user.id, ctx.send):
        return

    if ctx.player.health > 0:
        # do the battle and record the gold earned
        initial_gold = ctx.player.gold
        output = rpg_instance.battle(ctx.player)
        gold_earned = ctx.player.gold - initial_gold

        # deduct income tax (if applicable)
        guild = server_registered(ctx.message.guild.id)
        if guild and gold_earned != 0:
            income_tax = gold_earned * guild.settings["tax"]
            output += f"\nThe guild takes {income_tax} gold from your earnings!"
            ctx.player.gold -= income_tax
            guild.bal += income_tax
        await ctx.send(f"```{output}```")
    else:
        await ctx.send("You are tired and need to rest!")
    rpg_instance.save()
