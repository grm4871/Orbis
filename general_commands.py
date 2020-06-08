from command_parser import CommandParser
from guilds import guilds_instance
import guilds
import discord

"""
Commands that can be used by anyone
"""
parser = CommandParser("!")

@parser.command(help_text="pings the bot")
async def ping(ctx):
    await ctx.send("pong!")

on_message = parser.on_message

"""
Commands for server owners only
"""
owner_parser = CommandParser("!")

@owner_parser.command(help_text="makes a guild object for this server")
async def registerserver(ctx):
    if(guilds_instance.fetch_guild(ctx.message.guild.id) == None):
        presrole = await ctx.message.guild.create_role(name="President",color=discord.Color.gold(),hoist=True)
        guilds_instance.guilds.append(guilds.Guild(ctx.message.guild.id, electionChannel=ctx.message.channel.id, presidentRole=presrole.id))
        await ctx.send("Guild registered!")
        guilds_instance.save()

@owner_parser.command(help_text="makes a guild object for a server that doesn't intend to participate in the map game")
async def registerserverwithoutnation(ctx):
        guilds_instance.guilds.append(guilds.Guild(message.guild.id, nation=False))
        await ctx.send("Guild registered!")

@owner_parser.command(help_text="deletes all roles")
async def deleteallroles(ctx):
    for role in ctx.message.guild.roles:
        try:
            await role.delete()
        except:
            pass

on_owner_message = owner_parser.on_message