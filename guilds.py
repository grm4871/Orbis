import discord
import emoji
import random

#emoji library stuff
emojis = []
with open('emojis.txt', encoding='utf-8-sig') as f:
    for line in f.readlines():
        emojis.append(line[0])

"""
checks if a member is in a guild (discord)
"""
def member_exists(member, guild):
    try:
        m = guild.get_member(int(member))
        return True
    except:
        return False

"""
Takes a guild and advances it to the next phase of its election.
Horribly complicated and has a lot of issues. Rewriting is probably a good idea.
I'd move this out of the main file but that seems to break it for some discord library reasons
"""
async def nextPhase(g, client):
    guild = client.get_guild(int(g.server))
    channel = guild.get_channel(int(g.electionChannel))

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
                    #pick an unused emoji
                    while(True):
                        e = random.choice(list(emojis))
                        if not e in c.values():
                            c[candidate] = e
                            break
                    s += member.mention + ' ' + c[candidate] + '\n'
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
            if oldpres and oldpres != member.id:
                await oldpres.remove_roles(presrole)
            g.current_pres = highest
            await channel.send("Your new president is: " + member.mention)
        await msg.delete()
        g.candidates = []
        g.phase = -1

    g.phase += 1

#classes & definitions
class Guild():
    def __init__(self, server, electionChannel=None, presidentRole=None, nation=True):
        if nation:
            self.server = int(server)
            self.parties = []
            self.current_pres = None
            self.current_vice = None

            #election
            self.candidates = []
            self.phase = 0 #0, 1, 2, 3
            self.electionMessage = None #message id or array of message ids, internal use
            self.settings = {"autoelections":False,"tax":0,"salestax":0}
            self.electionChannel = electionChannel
            self.presidentRole = presidentRole
            self.bal = 0
        self.listings = {} #key:name, value:listings[]
        self.currency = "Gold"
        self.color = None
        self.possessions = []


    def nextPhase(self):
        guild = client.get_guild(self.server)
        channel = guild.get_channel(self.electionChannel)
        loop.run_until_complete(nextPhase(this))

    def addlisting(self, listing):
        if listing.name.lower() in self.listings:
            self.listings[listing.name.lower()].append(listing)
        else:
            self.listings[listing.name.lower()] = [listing]
        self.listings[listing.name.lower()].sort(key=lambda listing: listing.price)
        listing.currency = self.currency


class Party():
    def __init__(self, name, color, members, role, desc):
        self.name = name
        self.color = color
        self.members = members
        self.role = role
        self.desc = ""


class Listing():
    def __init__(self, item, quantity, price, author):
        self.name = item.name
        self.item = item
        self.quantity = quantity
        self.price = price
        self.totalprice = price * quantity
        self.currency = "Gold"
        self.author = author

    def show(self, tax=0):
        return f"{self.quantity} {self.name}(s) for {self.price*(tax+1)} {self.currency} each\n"

