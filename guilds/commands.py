"""
Handlers for the RPG commands.
"""
from guilds import guilds_instance
from command_parser import CommandParser

parser = CommandParser("!")
parser.add_custom_context("guild", lambda ctx: guilds_instance.fetch_guild(ctx.message.guild.id))


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

@parser.command(help_text="shows the guild's parties")
async def parties(ctx):
    #lists the guild's parties
    outputs = []
    idx = 0
    num = 0
    outputs.append("")
    for party in ctx.guild.parties:
        if num > 8:
            idx+=1
            num=0
            outputs.append("")
        outputs[idx] += "`!joinparty " + party.name + "`\n"
        num+=1
    for m in outputs:
        if m == "":
            await ctx.send("There are no parties!")
        else:
            await ctx.send(m)