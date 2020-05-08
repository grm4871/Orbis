import threading
import time
import discord
from datetime import datetime
import asyncio
import jsonsave
import emoji
import random
import webcolors
from guilds import Party
from guilds import Guild

#emoji library stuff
emojis = []
with open('emojis.txt', encoding='utf-8-sig') as f:
    for line in f.readlines():
        emojis.append(line[0])

async def nextPhase(g, client):
    guild = client.get_guild(g.server)
    channel = guild.get_channel(g.electionChannel)

    #primary
    if g.phase == 0:
        g.electionMessage = [] #there are now multiple elections (possibly)
        candidatePairs = {}
        #build list of candidates / parties
        for c in g.candidates:
            for party in g.parties:
                if c in party.members:
                    try:
                        if party.name in candidatePairs: candidatePairs[party.name].append(c)
                        else: candidatePairs[party.name] = [c]
                    except:
                        pass
        #create and send each primary message
        for party in candidatePairs:
            c = {}
            s = "`" + party + '` Primary: \n'
            for candidate in candidatePairs[party]:
                member = guild.get_member(int(candidate))
                try:
                    s += member.mention + ' ' + c[candidate] + '\n'
                    #pick an unused emoji
                    while(True):
                        e = random.choice(list(emojis))
                        if not e in c.values():
                            c[candidate] = e
                            break
                except:
                    pass
            m = await channel.send(s)
            for cand in c:
                await m.add_reaction(emoji.emojize(c[cand]))
            g.electionMessage.append([m.id,c])
        for party in g.parties:
            if not party.name in candidatePairs:
                partyrole = guild.get_role(party.role)
                try:
                    await partyrole.delete()
                except:
                    pass
                g.parties.remove(party)
        if g.candidates == []:
            await channel.send("No candidates to run primary with!")

    #end primary
    elif g.phase == 1:
        newCandidates = []
        for primary in g.electionMessage:
            try:
                msg = await channel.fetch_message(primary[0])
                results = {}
                for reaction in msg.reactions:
                    if str(reaction.emoji) in primary[1].values():
                        for key in primary[1]:
                            if primary[1][key] == str(reaction.emoji):
                                candidate = key
                        results[candidate] = reaction.count
                highest = None
                for candidate in results:
                    if member_exists(candidate, guild):
                        if highest == None:
                            highest = candidate
                        elif results[highest] < results[candidate]:
                            highest = candidate
                        elif results[highest] == results[candidate]:
                            if random.randint(1,2) == 2:
                                highest = candidate
                newCandidates.append(highest)
                await msg.delete()
            except:
                pass
        g.candidates = newCandidates

        #print winners
        outputs = []
        idx = 0
        num = 0
        outputs.append("Winning candidates:")
        for c in newCandidates:
            if num > 8:
                idx+=1
                outputs.append("")
            try:
                if c:
                    outputs[idx] += "`" + guild.get_member(int(c)).name + "`\n"
                    num+=1
            except: pass
        for m in outputs:
            if m == "Winning candidates:\n":
                await channel.send("Primary finished with zero candidates.")
                await channel.send("The current President will remain in power.")
            else:
                await channel.send(m)

    #election
    elif g.phase == 2:
        c = {}
        s = 'General Election: \n'
        for candidate in g.candidates:
            try:
                #pick an unused emoji
                while(True):
                    e = random.choice(list(emojis))
                    if not e in c.values():
                        c[candidate] = e
                        break
                member = guild.get_member(int(candidate))
                s += member.mention + ' ' + c[candidate] + '\n'
            except:
                pass
        m = await channel.send(s)
        for cand in c:
            await m.add_reaction(c[cand])
        g.electionMessage = [m.id,c]

    #end election
    elif g.phase == 3:
        msg = await channel.fetch_message(g.electionMessage[0])
        results = {}
        for reaction in msg.reactions:
            if str(reaction.emoji) in g.electionMessage[1].values():
                for key in g.electionMessage[1]:
                    if g.electionMessage[1][key] == str(reaction.emoji):
                        candidate = key
                results[candidate] = reaction.count
        highest = None
        for candidate in results:
            if member_exists(candidate, guild):
                if highest == None:
                    highest = candidate
                elif results[highest] < results[candidate]:
                    highest = candidate
                elif results[highest] == results[candidate]:
                    if random.randint(1,2) == 2:
                        highest = candidate
        if highest == None:
            #keep sitting pres
            await channel.send("A president could not be chosen.")
            pass
        else:
            #change the guard
            member = guild.get_member(int(highest))
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
            if oldpres:
                await oldpres.remove_roles(presrole)
            g.current_pres = highest
            await channel.send("Your new president is: " + member.mention)
        await msg.delete()
        g.candidates = []
        g.phase = -1

    g.phase += 1
    global GUILDS
    save_guilds(GUILDS)

#per-instance bot state
GUILDS = [] 
MEMBERS = {} #dictionary: key= member id, value= inventory dict

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

#save members
def save_members(members):
    jsonsave.save_dict(members, "data/members.txt")

def load_members():
    return jsonsave.load_dict("data/members.txt")

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
MEMBERS = load_members()
print(MEMBERS)
#run
client = discord.Client()


#commands
@client.event
async def on_message(message):
    global GUILDS
    global MEMBERS
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

        if message.content.startswith('!help'):
                    await message.channel.send(
                        """Commands: 
                        !createparty - creates a party
                        !joinparty - joins a party
                        !parties - lists the parties
                        !runforoffice - adds you to the list of candidates
                        !candidates - lists all candidates
                        !ownerhelp - lists all server owner commands""")
                    
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


        if message.content.startswith('!gold'):
            t = 0
            if str(message.guild.id) in MEMBERS:
                if "Gtime" in MEMBERS[str(message.guild.id)]:
                    t = MEMBERS[str(message.guild.id)]["Gtime"]
            if time.time() - (20*60*60) > t: 
                gold = 1
                #add gold to the member's inventory
                if "tax" in g.settings:
                    gold = round(1 - g.settings["tax"],2)
                if str(message.author.id) in MEMBERS:
                    if "G" in MEMBERS[str(message.author.id)]:
                        MEMBERS[str(message.author.id)]["G"] += gold
                        print(MEMBERS[str(message.author.id)]["G"])
                    else:
                        print("hi")
                        MEMBERS[str(message.author.id)]["G"] = gold
                else:
                    print("here")
                    MEMBERS[str(message.author.id)] = {"G":gold}
                await message.channel.send("Earned " + str(gold) + " gold!")
                MEMBERS[str(message.author.id)]["Gtime"] = time.time()
                #add taxed gold to the nation's inventory
                if gold != 1:
                    if str(message.guild.id) in MEMBERS:
                        if "G" in MEMBERS[str(message.guild.id)]:
                            MEMBERS[str(message.guild.id)]["G"] += round(g.settings["tax"],2)
                        else:
                            MEMBERS[str(message.guild.id)]["G"] = round(g.settings["tax"],2)
                    else:
                        MEMBERS[str(message.guild.id)] = {"G":round(g.settings["tax"],2)}
            else:
                await message.channel.send("You can only collect gold once a day!")
            save_members(MEMBERS)

        if message.content.startswith("!bal"):
            if str(message.author.id) in MEMBERS:
                if "G" in MEMBERS[str(message.author.id)]:
                    await message.channel.send("You have " + str(MEMBERS[str(message.author.id)]["G"]) + " gold!") 
                else:
                    await message.channel.send("You don't have any gold!")
            else:
                await message.channel.send("You don't have any gold!")


        """
        PRESIDENT COMMANDS
        """
        if message.author.id == g.current_pres:
            #preshelp
            if message.content.startswith("!preshelp"):
                await message.channel.send(
                """President-specific commands:
                !nationbal: check your nation's gold reserves
                !settax: set your nation's tax rate """)


            #check country's gold
            if message.content.startswith("!nationbal"):
                if message.guild.id in MEMBERS:
                    if "G" in MEMBERS[message.guild.id]:
                        await message.channel.send("Your nation has " + str(MEMBERS[message.guild.id]["G"]) + " gold!") 
                    else:
                        await message.channel.send("Your nation doesn't have any gold!")
                else:
                    await message.channel.send("Your nation doesn't have any gold!")


            if message.content.startswith("!settax"):
                args = message.content.split(" ");
                if len(args) != 2:
                    await message.channel.send("Usage: !settax percent (between 0 and 100)")
                else:
                    try:
                        newtax = int(args[1])
                        if newtax >= 0 and newtax <= 100:
                            g.settings["tax"] = newtax * .01
                            await message.channel.send("Tax rate set to " + str(newtax) + " percent!")
                        else:
                            await message.channel.send("Tax rate must be between 0 and 100 percent!")
                    except:
                        await message.channel.send("Usage: !settax percent (between 0 and 100)")
                save_guilds(GUILDS)

    """
    GUILD OWNER COMMANDS
    """
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
            await nextPhase(g, client)
            save_guilds(GUILDS)

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

        #currently broken
        if message.content.startswith('!setpresident'):
                guild = message.guild
            #try:
                member = guild.get_member_named(message.content.split(" ")[1])
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
                if oldpres:
                    await oldpres.remove_roles(presrole)
                g.current_pres = highest
                await message.channel.send("Your new president is: " + member.mention)
            #except:
                #await message.channel.send("Usage: !setpresident member")




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
                    await nextPhase(guild, client)

#main function, just for threading stuff

if __name__ == '__main__':
    client.loop.create_task(clock())
    with open("data/token.txt") as f:
        client.run(f.read())
