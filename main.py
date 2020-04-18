import threading
import time
import discord
from datetime import datetime
import emoji
import asyncio
import jsonsave
import random


#emoji library stuff
emojis = []
with open('emojis.txt', encoding='utf-8-sig') as f:
    for line in f.readlines():
        emojis.append(line[0])

async def nextPhase(g):
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
                        member = guild.get_member(c)
                        if party.name in candidatePairs: candidatePairs[party.name].append(c)
                        else: candidatePairs[party.name] = [c]
                    except:
                        pass
        #create and send each primary message
        for party in candidatePairs:
            c = {}
            s = party + ' Primary: \n'
            for candidate in candidatePairs[party]:
                #pick an unused emoji
                while(True):
                    e = random.choice(list(emojis))
                    if not e in c.values():
                        c[candidate] = e
                        break
                member = guild.get_member(candidate)
                s += member.mention + ' ' + c[candidate] + '\n'
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
            g.phase = -1
            await channel.send("No candidates to run primary with!")

    #end primary
    elif g.phase == 1:
        newCandidates = []
        for primary in g.electionMessage:
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
            if highest is not None:
                member = guild.get_member(highest)
            newCandidates.append(member.id)
            await msg.delete()
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
            outputs[idx] += "`" + guild.get_member(c).name + "`\n"
            num+=1
        for m in outputs:
            if m == "Winning candidates:":
                await channel.send("Primary finished with zero candidates.")
                await channel.send("Back to primary phase...")
            else:
                await channel.send(m)


        if g.candidates == []:
            g.phase = 3

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
                member = guild.get_member(candidate)
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
            pass
        else:
            #change the guard
            member = guild.get_member(highest)
            oldpres = guild.get_member(g.current_pres)
            presrole = guild.get_role(g.presidentRole)
            try:
                await member.add_roles(presrole)
            except:
                presrole = await message.guild.create_role(name="President",color=discord.Color.gold(),hoist=True)
                g.presidentRole = presrole.id
                await member.add_roles(presrole)
            if oldpres:
                await oldpres.remove_roles(presrole)
            g.current_pres = highest
            await channel.send("Your new president is: " + member.mention)
        await msg.delete()
        g.candidates = []
        g.phase = -1
    if g.phase == 3:
        g.phase = -1
    g.phase += 1
    global GUILDS
    save_guilds(GUILDS)

#classes & definitions
class Guild():
    def __init__(self, server, parties=[], current_pres=None, current_vice=None, 
                candidates=[], phase=0, electionMessage=None, electionTime=None,
                electionChannel=None, presidentRole=None):
        self.server = server
        self.parties = []
        for p in parties:
            self.parties.append(Party(p[0],p[1],p[2],p[3],p[4]))
        self.current_pres = None
        self.current_vice = None

        #election
        self.candidates = candidates
        self.phase = 0 #0, 1, 2, 3
        self.electionMessage = None #message id or array of message ids
        self.electionTime = electionTime
        if electionTime == None:
            self.electionTime = time.time() + 86400
        self.electionChannel = electionChannel
        self.presidentRole = presidentRole

    def nextPhase(self):
        guild = client.get_guild(self.server)
        channel = guild.get_channel(self.electionChannel)
        loop.run_until_complete(nextPhase(this))
        
    def noPres():
        pass

    def addCandidate():
        pass

    def remCandidate():
        pass

    def changePartyInfo(name=None, color=None, desc=None):
        pass

    def output_data(self): #for saving to file
        data = []
        data.append(self.server)
        p = []
        for party in self.parties:
            p.append(party.output_data())
        data.append(p)
        data.append(self.current_pres)
        data.append(self.current_vice)
        data.append(self.candidates)
        data.append(self.phase)
        data.append(self.electionMessage)
        data.append(self.electionTime)
        data.append(self.electionChannel)
        data.append(self.presidentRole)
        return data

class Party():
    def __init__(self, name, color, members, role, desc):
        self.name = name
        self.color = color
        self.members = members
        self.role = role
        self.desc = ""

    def output_data(self):
        data = []
        data.append(self.name)
        data.append(self.color)
        data.append(self.members)
        data.append(self.role)
        data.append(self.desc)
        return data

#per-instance bot state
GUILDS = [] #top-level, i think this is the only level actually (for now)

#helper functions
def fetch_guild(id):
    global GUILDS
    for guild in GUILDS:
        if guild.server == id:
            return guild
    return None

def member_exists(member, guild):
    try:
        m = guild.get_member(member)
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
    jsonsave.save_list(guilds, "guilds.txt")

#load guilds
def load_guilds():
    loads = jsonsave.load_list("guilds.txt")
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

        #create party
        if message.content.startswith("!createparty"):
            guild = message.guild
            args = message.content.split('-')
            if len(args) != 5:
                await message.channel.send('Usage: !createparty-partyname-red-green-blue, red green and blue being between 0 and 255')
            else:
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
                role = await message.guild.create_role(name=args[1],color=discord.Color.from_rgb(int(args[2]),int(args[3]),int(args[4])),hoist=True)
                await message.author.add_roles(role)
                g.parties.append(Party(args[1],(int(args[2]),int(args[3]),int(args[4])),[message.author.id],role.id,""))
                await message.channel.send('Party created successfully')
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
                    print(p.role)
                    if p.name == name:
                        party = p
                print(party.role)
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
                    print(party.role)
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

        if message.content.startswith('!parties'):
            outputs = []
            idx = 0
            num = 0
            outputs.append("")
            for party in g.parties:
                if num > 8:
                    idx+=1
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
                    outputs.append("")
                outputs[idx] += "`" + message.guild.get_member(c).name + "`\n"
                num+=1
            for m in outputs:
                if m == "":
                    await message.channel.send("No candidates!")
                else:
                    await message.channel.send(m)

        if message.content.startswith('!runforoffice'):
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

        if message.content.startswith('!help'):
            await message.channel.send(
                """Commands: 
                !createparty - creates a party
                !joinparty - joins a party
                !parties - lists the parties
                !runforoffice - adds you to the list of candidates
                !candidates - lists all candidates""")

        if message.author.id == message.guild.owner.id:
            if message.content.startswith('!forceelection'):
                await nextPhase(g)


print("started! uwu")



#clock that tests for election events
async def clock():
    await client.wait_until_ready()
    while(True):
        await asyncio.sleep(5)
        global GUILDS
        for guild in GUILDS:
            if guild.electionTime < time.time():
                await nextPhase(guild)
                #todo check for dead president TODO

#main function, just for threading stuff

if __name__ == '__main__':
    #client.loop.create_task(clock())
    client.run('MjUzNzE1NzQyMTg3MzIzNDA0.XaknFQ.hfmLsk_qqSwvjY27NxLvDCuo8zA')
