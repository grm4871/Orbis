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

    #makes a Guild object for the server (serverowner only)
    elif message.content == "!registerserver" and message.author == message.guild.owner:
        if(guilds_instance.fetch_guild(message.guild.id) == None):
            presrole = await message.guild.create_role(name="President",color=discord.Color.gold(),hoist=True)
            guilds_instance.guilds.append(guilds.Guild(message.guild.id, electionChannel=message.channel.id, presidentRole=presrole.id))
            await message.channel.send("Guild registered!")
            guilds_instance.save()

    #creates a guild object for servers that aren't meant to participate in the map game (upcoming)
    elif message.content.startswith("!registerservernonation"):
        guilds_instance.guilds.append(Guild(message.guild.id, nation=False))
        print("registered")

    """
    RPG COMMANDS
    """
    await rpg.on_message(message)


    """
    NATIONSERVER COMMANDS
    """


    #check if server is a nation
    if guilds_instance.fetch_guild(message.guild.id):
        g = guilds_instance.fetch_guild(message.guild.id)

        await guilds.on_message(message)

        """
        #lists the guild's parties
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
        """

        #lists the guild's candidates
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
                try:
                    outputs[idx] += "`" + message.guild.get_member(int(c)).name + "`\n"
                except:
                    pass
                num+=1
            for m in outputs:
                if m == "":
                    await message.channel.send("No candidates!")
                else:
                    await message.channel.send(m)

        #sends a help message
        elif message.content.startswith('!help'):
                    await message.channel.send(
                        """Commands: 
                        !createparty - creates a party
                        !joinparty - joins a party
                        !parties - lists the parties
                        !runforoffice - adds you to the list of candidates
                        !candidates - lists all candidates
                        !ownerhelp - lists all server owner commands""")

        #create party
        elif message.content.startswith("!createparty"):
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
                    color = get_color(args[2])
                    if not color:
                        await message.channel.send("Party could not be created")
                    else:
                        role = await message.guild.create_role(name=args[1],color=discord.Color(int(color,16)),hoist=True)
                        await message.author.add_roles(role)
                        colorrgb = webcolors.hex_to_rgb("#" + color)
                        g.parties.append(guilds.Party(args[1],(colorrgb[0],colorrgb[1],colorrgb[2]),[message.author.id],role.id,""))
                        await message.channel.send('Party created successfully')
                else:
                    await message.channel.send("That party already exists!")
            guilds_instance.save()

        #leaves your political party
        elif message.content.startswith('!leaveparty'):
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
            guilds_instance.save()

        #join political party
        elif message.content.startswith('!joinparty'):
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
            guilds_instance.save()


        #adds you to the list of presidential candidates
        elif message.content.startswith('!runforoffice') and g.phase == 0:
            inParty = False
            for party in g.parties:
                if message.author.id in party.members:
                    inParty = True
            if (not message.author.id in g.candidates) and inParty:
                g.candidates.append(message.author.id)
                await message.channel.send('You are now a candidate!')
                guilds_instance.save()
            elif inParty == False:
                await message.channel.send("Join a party first!")
            else:
                await message.channel.send("You are already a candidate!")
        elif message.content.startswith('!runforoffice'):
            await message.channel.send("Candidates are already locked in for this election!")

        """
        PRESIDENT COMMANDS
        """
        if message.author.id == g.current_pres:
            
            #preshelp
            if message.content.startswith("!preshelp"):
                await message.channel.send(
                """President-specific commands:
                there are none lol
                 """)

        """
        GUILD OWNER COMMANDS
        """
        if message.author.id == message.guild.owner.id:
            g = guilds_instance.fetch_guild(message.guild.id)

            #delete all roles (very handy for bot testing)
            if message.content.startswith('!deleteallroles'):
                for role in message.guild.roles:
                    try:
                        await role.delete()
                    except:
                        pass

            #help command for guild owners
            if message.content.startswith('!ownerhelp'):
                await message.channel.send(
                    """Owner/Debug commands:
                    !forceelection: forces the next phase of the election cycle
                    !resetelection: goes back to the pre-primary phase of the election cycle
                    !electionstate: shows which state of the election cycle this server is in
                    !autoelections: toggles automatic primaries/elections on wednesday and saturday
                    !deleteparty: deletes a party""")

            #forces the election cycle to the next phase
            elif message.content.startswith('!forceelection'):
                await nextPhase(g, client)
                guilds_instance.save()

            #resets the guild's election cycle
            elif message.content.startswith('!resetelection'):
                g.phase = 0
                guilds_instance.save()

            #prints the current election state (pre-primary, primary, pre-general, general)
            elif message.content.startswith('!electionstate'):
                await message.channel.send(g.phase)

            #toggles automatic elections (might be broken, i need to look into that)
            elif message.content.startswith('!autoelections'):
                g.settings["autoelections"] = not g.settings["autoelections"]
                if g.settings["autoelections"]: await message.channel.send("Automatic elections on!")
                else: await message.channel.send("Automatic elections off!")
                guilds_instance.save()

            #deletes a political party
            elif message.content.startswith('!deleteparty'):
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

            #Sets the current guild president to a given member
            elif message.content.startswith('!setpresident'):
                guild = message.guild
                try:
                    if len(message.mentions) > 0:
                        member = message.mentions[0]
                        if g.current_pres:
                            oldpres = guild.get_member(int(g.current_pres))
                        else:
                            oldpres = None
                        try:
                            presrole = guild.get_role(int(g.presidentRole))
                            await member.add_roles(presrole)
                        except:
                            presrole = await guild.create_role(name="President",color=discord.Color.gold(),hoist=True)
                            g.presidentRole = presrole.id
                            await member.add_roles(presrole)
                        if oldpres and oldpres != member.id:
                            await oldpres.remove_roles(presrole)
                        g.current_pres = member.id
                        await message.channel.send("Your new president is: " + member.mention)
                    else:
                        raise Exception("no args")
                except:
                    await message.channel.send("Usage: !setpresident member")

            elif message.content.startswith('!setelectionchannel'):
                g.electionChannel = message.channel
                await message.channel.send("Election channel set!")
                await message.delete()

            elif message.content.startswith('!setcolor'):
                color = get_color(message.content.split(" ")[1])
                if color:
                    g.color = color
                    await message.channel.send("Color set!")
                else:
                    await message.channel.send("Invalid color")

            elif message.content.startswith('!settax') or message.content.startswith('!setsalestax'):
                rate = float(message.content.split(" ")[1])
                if rate >= 0 and rate < 1:
                    if message.content.startswith('!settax'):
                        g.settings["tax"] = rate
                    else:
                        g.settings["salestax"] = rate
                    await message.channel.send("Tax rate set!")
                else:
                    await message.channel.send("Tax rate must be between zero and one")

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
