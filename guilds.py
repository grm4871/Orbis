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
                        member = guild.get_member(int(c))
                        if party.name in candidatePairs: candidatePairs[party.name].append(c)
                        else: candidatePairs[party.name] = [c]
                    except:
                        pass
        #create and send each primary message
        for party in candidatePairs:
            c = {}
            s = "`" + party + '` Primary: \n'
            for candidate in candidatePairs[party]:
                #pick an unused emoji
                while(True):
                    e = random.choice(list(emojis))
                    if not e in c.values():
                        c[candidate] = e
                        break
                member = guild.get_member(int(candidate))
                try:
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
                outputs[idx] += "`" + guild.get_member(int(c)).name + "`\n"
            except:
                user = await client.fetch_user(c)
                outputs[idx] += "`" + user.name + "`\n"
            num+=1
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

#classes & definitions
class Guild():
    def __init__(self, server, parties=[], current_pres=None, current_vice=None, 
                candidates=[], phase=0, electionMessage=None, settings={"autoelections":False},
                electionChannel=None, presidentRole=None):

        self.server = int(server)
        self.parties = []
        for p in parties:
            self.parties.append(Party(p[0],p[1],p[2],p[3],p[4]))
        self.current_pres = current_pres
        self.current_vice = current_vice

        #election
        self.candidates = candidates
        self.phase = phase #0, 1, 2, 3
        self.electionMessage = electionMessage #message id or array of message ids

        if type(settings) is not dict:
            settings={"autoelections":False}
        self.settings = settings


        self.electionChannel = electionChannel
        self.presidentRole = presidentRole

    def nextPhase(self):
        guild = client.get_guild(self.server)
        channel = guild.get_channel(self.electionChannel)
        loop.run_until_complete(nextPhase(this))

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
        data.append(self.settings)
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
