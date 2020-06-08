import threading
import time
import discord
from datetime import datetime
import asyncio
import random
import webcolors
import guilds
from guilds import guilds_instance
import _pickle as pickle
import rpg
import general_commands
from rpg import rpg_instance

"""
checks if a member is in a (discord) guild
"""
def member_exists(member, guild):
    try:
        m = guild.get_member(int(member))
        return True
    except:
        return False

#saves the rpg instance with pickle
def save_rpg(rpg_instance):
    with open("data/rpg_instance.txt", "wb") as f:
        pickle.dump(rpg_instance, f, -1)

def get_color(color_string):
    try:
        color = webcolors.name_to_hex(color_string, spec='css3')[1:]
        return color
    except:
        try:
            color = color_string[1:]
            test = webcolors.hex_to_rgb("#" + color)
            return color
        except:
            return False

#run
client = discord.Client()

#commands
@client.event
async def on_message(message):
    #ignore self
    if message.author.bot:
        return

    """
    GENERAL COMMANDS
    """
    await general_commands.on_message(message)

    """
    RPG COMMANDS
    """
    await rpg.on_message(message)

    """
    OWNER COMMANDS
    """
    if message.author.id == message.guild.owner.id: await general_commands.on_owner_message(message)
        

    """
    NATIONSERVER COMMANDS
    """
    if guilds_instance.fetch_guild(message.guild.id): 
        await guilds.on_message(message)

        """
        PRESIDENT COMMANDS
        """
        #currently none

        """
        GUILDOWNER NATIONSERVER COMMANDS
        """
        if message.author.id == message.guild.owner.id: await guilds.on_owner_message(message)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

#clock that tests for election times and rpg events (elections: wednesday/saturday 8pm)
"""
days = {0:2,1:3,2:5,3:6}
async def clock():
    await client.wait_until_ready()
    while(True):
        await asyncio.sleep(5)
        for guild in guilds_instance.guilds:
            if datetime.now().hour > 19 and guild.settings["autoelections"]:
                if days[guild.phase] == datetime.now().weekday():
                    await nextPhase(guild, client)
                    guilds_instance.save()
        rpg_instance.updatehealth()
        save_rpg(rpg_instance)
"""

#main function, just for threading stuff
if __name__ == '__main__':
    #client.loop.create_task(clock())
    with open("data/token.txt") as f:
        client.run(f.read())
