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


@parser.command(help_text="equip an item (weapon/armor) from your inventory", usage_text="?equip item_name")
async def equip(ctx, *, item_name):
    if rpg_instance.equip(ctx.player, item_name):
        await ctx.send(f"Equipped `{item_name}`!")
    else:
        await ctx.send(f"Failed to equip `{item_name}`")
    rpg_instance.save()


@parser.command(help_text="list all RPG areas")
async def areas(ctx):
    await ctx.send(rpg_instance.showareas())


@parser.command(help_text="travel to a different RPG area", usage_text="?travel area_name")
async def travel(ctx, *, area_name):
    if area_name.upper() in (name.upper() for name in rpg_instance.areas):
        area = rpg_instance.areas[area_name]
        if ctx.player.level >= area.requiredLevel:
            ctx.player.area = area
            await ctx.send(f"You are now in: `{ctx.player.showarea()}`")
        else:
            await ctx.send("Your level isn't high enough for that area!")
    else:
        await ctx.send("Travel failed.")


@parser.command(help_text="create an rpg item listing on the guild market", usage_text="?sell unit_price quantity item_name")
async def sell(ctx, price, quantity, *, item_name):
    quant = int(quantity)
    unitprice = float(price)
    if item_name.upper() in (item.upper() for item in ctx.player.inventory):
        g = server_registered(ctx.message.guild.id)
        if player.inventory[itemname][1] >= quant:
            player.deacquire(rpginstance.finditem(itemname), quant)
            g.addlisting(guilds.Listing(rpginstance.finditem(itemname), quant, unitprice, player))
            await ctx.send("Listing posted.")
            save_guilds(GUILDS)
        else:
            await ctx.send("You can't sell what you don't have!")
    elif unitprice < 0.00001 or unitprice > 99999999999:
        await ctx.send("Bad price")
    else:
        await ctx.send("You can't sell what you don't have!")

