"""
Handlers for the RPG commands.
"""

import guilds
from main import check_cooldown, server_registered, GUILDS, save_guilds
from . import rpg_instance
from command_parser import CommandParser

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


@parser.command(help_text="equip an item (weapon/armor) from your inventory",
                usage_text="?equip item_name")
async def equip(ctx, *, item_name):
    if rpg_instance.equip(ctx.player, item_name):
        await ctx.send(f"Equipped `{item_name}`!")
    else:
        await ctx.send(f"Failed to equip `{item_name}`")
    rpg_instance.save()


@parser.command(help_text="list all RPG areas")
async def areas(ctx):
    await ctx.send(rpg_instance.showareas())


@parser.command(help_text="travel to a different RPG area",
                usage_text="?travel area_name")
async def travel(ctx, *, area_name):
    if area_name.lower() in (name.lower() for name in rpg_instance.areas):
        area = rpg_instance.areas[area_name]
        if ctx.player.level >= area.requiredLevel:
            ctx.player.area = area
            await ctx.send(f"You are now in: `{ctx.player.showarea()}`")
        else:
            await ctx.send("Your level isn't high enough for that area!")
    else:
        await ctx.send("Travel failed.")


@parser.command(help_text="create an rpg item listing on the guild market",
                usage_text="?sell unit_price quantity item_name")
async def sell(ctx, price, quantity, *, item_name):
    quant = int(quantity)
    unitprice = float(price)
    if item_name.lower() in (item.lower() for item in ctx.player.inventory):
        g = server_registered(ctx.message.guild.id)
        if ctx.player.inventory[item_name][1] >= quant:
            ctx.player.deacquire(rpg_instance.finditem(item_name), quant)
            g.addlisting(guilds.Listing(rpg_instance.finditem(item_name), quant, unitprice, ctx.player))
            await ctx.send("Listing posted.")
            #save_guilds(GUILDS)
        else:
            await ctx.send("You can't sell what you don't have!")
    elif unitprice < 0.00001 or unitprice > 99999999999:
        await ctx.send("Bad price")
    else:
        await ctx.send("You can't sell what you don't have!")


#memory for which market a user was last browsing, used in ?buy
market_browsing = {} #userid: itemname


@parser.command(help_text="show listings for a specific rpg item",
                usage_text="?market item_name")
async def market(ctx, *, item_name):
    g = server_registered(ctx.message.guild.id)
    output = "```\n--Listings--\n"
    if g.settings["salestax"] != 0: output += "*Listings include sales tax*\n"
    output += "\n"
    item_name = item_name.lower()
    if item_name in g.listings:
        tax = g.settings["salestax"]
        for i, listing in enumerate(g.listings[item_name]):
            output += f"{i}: {listing.show(tax)}"
        output += f"```To buy a listing, do ?buy-#"
        market_browsing[ctx.message.author.id] = item_name
        await ctx.send(output)
    else:
        await ctx.send("That's not for sale here!")

@parser.command(help_text="works in tandem with ?market")
async def buy(ctx, number):
    g = server_registered(ctx.message.guild.id)
    name = market_browsing[ctx.message.author.id]
    if name:
        listing = g.listings[name][int(number)]
        if listing.author == ctx.player or ctx.player.gold >= listing.totalprice:
            if ctx.player.acquire(listing.item, listing.quantity):
                await ctx.send(f"`{ctx.player.name} gained {listing.item.name}`\n")
                g.listings[name].remove(listing)
                if listing.author != ctx.player:
                    #at this point, the transaction is successful, and between two different users
                    salestax = (g.settings["salestax"] + 1) * listing.totalprice
                    ctx.player.gold -= listing.totalprice + salestax
                    g.bal += salestax
                    listing.author.gold += listing.totalprice
                #save_guilds(GUILDS)
            else:
                await ctx.send("Your inventory isn't big enough!")
        else:
            await ctx.send("You don't have the money for that!")