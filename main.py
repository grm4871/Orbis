import threading
import time
import discord
from datetime import datetime
import emoji
import asyncio
import jsonsave
import random
import webcolors
from guilds import Party
from guilds import Guild
from guilds import nextPhase

#emoji library stuff
emojis = []
with open('emojis.txt', encoding='utf-8-sig') as f:
    for line in f.readlines():
        emojis.append(line[0])

#per-instance bot state
GUILDS = [] #top-level, i think this is the only level actually (for now)
MEMBERS = {}

#helper functions
def fetch_guild(id):
    global GUILDS
    for guild in GUILDS:
        if guild.server == id:
            return guild
    return None

def member_exists(member, guild):
    try:
        m = guild.get_member(int(member))
        return True
    except:
        return False

def server_registered(id):
    global GUILDS
    for guild in GUILDS:
        if guild.server == id:
            return guild
    return False

#save guilds
def save_guilds(guilds):
    jsonsave.save_list(guilds, "data/guilds.txt")

#load guilds
def load_guilds():
    loads = jsonsave.load_list("data/guilds.txt")
    GUILDS = []
    for guild in loads:
        GUILDS.append(Guild(guild[0],guild[1],guild[2],guild[3],guild[4],
                            guild[5],guild[6],guild[7],guild[8],guild[9]))
    return GUILDS

GUILDS = load_guilds()
#run
client = discord.Client()


#commands
@client.event
async def on_message(message):
    global GUILDS
    if message.author == client.user:
        return
    
    #ping command
    if message.content == "!ping":
        await message.channel.send("pong! uwu")


    if message.content.startswith("!registerserver"):
        if(fetch_guild(message.guild.id) == None):
            presrole = await message.guild.create_role(name="President",color=discord.Color.gold(),hoist=True)
            GUILDS.append(Guild(message.guild.id, electionChannel=message.channel.id, presidentRole=presrole.id))
            await message.channel.send("Guild registered!")
            save_guilds(GUILDS)


    #check if server is a nation
    if server_registered(message.guild.id):
        g = server_registered(message.guild.id)
        if message.content.startswith('!parties'):
            outputs = []
            idx = 0
            num = 0
            outputs.append("")
            for party in g.parties:
                if num > 8:
                    idx+=1
                    num=0
                    outputs.append("")
                outputs[idx] += "`!joinparty " + party.name + "`\n"
                num+=1
            for m in outputs:
                if m == "":
                    await message.channel.send("There are no parties!")
                else:
                    await message.channel.send(m)

        if message.content.startswith('!candidates'):
            outputs = []
            idx = 0
            num = 0
            outputs.append("")
            for c in g.candidates:
                if num > 8:
                    idx+=1
                    num=0
                    outputs.append("")
                outputs[idx] += "`" + message.guild.get_member(int(c)).name + "`\n"
                num+=1
            for m in outputs:
                if m == "":
                    await message.channel.send("No candidates!")
                else:
                    await message.channel.send(m)

        if message.content.startswith('!help'):
                    await message.channel.send(
                        """Commands: 
                        !createparty - creates a party
                        !joinparty - joins a party
                        !parties - lists the parties
                        !runforoffice - adds you to the list of candidates
                        !candidates - lists all candidates
                        !ownerhelp - lists all server owner commands""")

    if server_registered(message.guild.id):# and not (message.author.id == message.guild.owner.id):
        g = server_registered(message.guild.id)

        #create party
        if message.content.startswith("!createparty"):
            guild = message.guild
            args = message.content.split('-')
            if len(args) != 3:
                await message.channel.send('Usage: !createparty-partyname-color')
            else:

                #leave old party
                oldparty = None
                for party in g.parties:
                    partyrole = guild.get_role(party.role)
                    if partyrole in message.author.roles:
                        await message.author.remove_roles(partyrole)
                        oldparty = party
                        try:
                            oldparty.members.remove(message.author.id)
                        except:
                            pass
                if oldparty:
                    if oldparty.members == []:
                        partyrole = guild.get_role(oldparty.role)
                        await partyrole.delete()
                        g.parties.remove(oldparty)

                #check if name exists

                name = args[1]
                party = None
                for p in g.parties:
                    if p.name == name:
                        party = p
                if not party:

                    #get color
                    try:
                        color = webcolors.name_to_hex(args[2], spec='css3')[1:]
                    except:
                        try:
                            color = args[2][1:]
                            test = webcolors.hex_to_rgb("#" + color)
                        except:
                            await message.channel.send('Could not create party')
                            return
                    role = await message.guild.create_role(name=args[1],color=discord.Color(int(color,16)),hoist=True)
                    await message.author.add_roles(role)
                    colorrgb = webcolors.hex_to_rgb("#" + color)
                    g.parties.append(Party(args[1],(colorrgb[0],colorrgb[1],colorrgb[2]),[message.author.id],role.id,""))
                    await message.channel.send('Party created successfully')

                else:
                    await message.channel.send("That party already exists!")
            save_guilds(GUILDS)

        if message.content.startswith('!leaveparty'):
            guild = message.guild
            oldparty = None
            for party in g.parties:
                partyrole = guild.get_role(party.role)
                if partyrole in message.author.roles:
                    await message.author.remove_roles(partyrole)
                    oldparty = party
                    try:
                        oldparty.members.remove(message.author.id)
                    except:
                        pass
            if oldparty:
                if oldparty.members == []:
                    partyrole = guild.get_role(oldparty.role)
                    await partyrole.delete()
                    g.parties.remove(oldparty)

            await message.channel.send("Successfully left party")
            save_guilds(GUILDS)

        #join party
        if message.content.startswith('!joinparty'):
            guild = message.guild
            args = message.content.split(' ')
            if len(args) < 2:
                await message.channel.send('Usage: !joinparty partyname')
            else:
                name = message.content[11:]
                party = None
                for p in g.parties:
                    if p.name == name:
                        party = p
                if party:
                    party.members.append(message.author.id)
                    #find old party
                    oldparty = None
                    for p in g.parties:
                        partyrole = guild.get_role(p.role)
                        if partyrole in message.author.roles:
                            await message.author.remove_roles(partyrole)
                            oldparty = p
                            try:
                                oldparty.members.remove(message.author.id)
                            except:
                                pass
                    if oldparty and oldparty != party:
                        if oldparty.members == []:
                            partyrole = guild.get_role(oldparty.role)
                            await partyrole.delete()
                            g.parties.remove(oldparty)
                    partyrole = guild.get_role(party.role)
                    try:
                        await message.author.add_roles(partyrole)
                    except:
                        role = await message.guild.create_role(name=party.name,color=discord.Color.from_rgb(party.color[0],party.color[1],party.color[2]),hoist=True)
                        party.role = role.id
                        await message.author.add_roles(role)
                    await message.channel.send('Joined!')
                else:
                    await message.channel.send('This party doesn\'t exist!')
            save_guilds(GUILDS)


        if message.content.startswith('!runforoffice') and g.phase == 0:
            inParty = False
            for party in g.parties:
                if message.author.id in party.members:
                    inParty = True
            if (not message.author.id in g.candidates) and inParty:
                g.candidates.append(message.author.id)
                await message.channel.send('You are now a candidate!')
                save_guilds(GUILDS)
            elif inParty == False:
                await message.channel.send("Join a party first!")
            else:
                await message.channel.send("You are already a candidate!")
        elif message.content.startswith('!runforoffice'):
            await message.channel.send("Candidates are already locked in for this election!")

    if message.author.id == message.guild.owner.id:
        g = server_registered(message.guild.id)

        if message.content.startswith('!ownerhelp'):
            await message.channel.send(
                """Owner/Debug commands:
                !forceelection: forces the next phase of the election cycle
                !resetelection: goes back to the pre-primary phase of the election cycle
                !electionstate: shows which state of the election cycle this server is in
                !autoelections: toggles automatic primaries/elections on wednesday and saturday
                !deleteparty: deletes a party""")

        if message.content.startswith('!forceelection'):
            await nextPhase(g)

        if message.content.startswith('!resetelection'):
            g.phase = 0
            save_guilds(GUILDS)

        if message.content.startswith('!electionstate'):
            await message.channel.send(g.phase)

        if message.content.startswith('!autoelections'):
            g.settings["autoelections"] = not g.settings["autoelections"]
            if g.settings["autoelections"]: await message.channel.send("Automatic elections on!")
            else: await message.channel.send("Automatic elections off!")
            save_guilds(GUILDS)

        if message.content.startswith('!deleteparty'):
            args = message.content.split(' ')
            if len(args) < 2:
                await message.channel.send('Usage: !deleteparty partyname')
            name = message.content[13:]
            party = None
            for p in g.parties:
                if p.name == name:
                    party = p
            if party:
                partyrole = message.guild.get_role(party.role)
                await partyrole.delete()
                g.parties.remove(party)
                await message.channel.send('Party deleted successfully!')
            else:
                await message.channel.send('Party not found')

print("started! uwu")



#clock that tests for election times (wednesday/saturday 8pm)
days = {0:2,1:3,2:5,3:6}
async def clock():
    await client.wait_until_ready()
    while(True):
        await asyncio.sleep(5)
        global GUILDS
        for guild in GUILDS:
            if datetime.now().hour > 19 and guild.settings["autoelections"]:
                if days[guild.phase] == datetime.now().weekday():
                    await nextPhase(guild)

#main function, just for threading stuff

if __name__ == '__main__':
    client.loop.create_task(clock())
    with open("data/token.txt") as f:
        client.run(f.read())
