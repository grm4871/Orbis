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
import guilds
import _pickle as pickle
import rpg

#emoji library stuff
emojis = []
with open('emojis.txt', encoding='utf-8-sig') as f:
    for line in f.readlines():
        emojis.append(line[0])


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
            if oldpres and oldpres != member.id:
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
rpginstance = rpg.load()

#helper functions
"""
gets a guild (object) by id
"""
def fetch_guild(id):
    global GUILDS
    for guild in GUILDS:
        if guild.server == id:
            return guild
    return None


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
checks if a server is a registered orbis guild
"""
def server_registered(id):
    global GUILDS
    for guild in GUILDS:
        if guild.server == id:
            return guild
    return False

#save guilds
def save_guilds(guilds):
    with open("data/guilds.txt", "wb") as f:
        pickle.dump(guilds, f, -1)

#load guilds
def load_guilds():
    with open("data/guilds.txt", "rb") as f:
        return pickle.load(f)

#saves the rpg instance with pickle
def save_rpg(rpginstance):
    with open("data/rpginstance.txt", "wb") as f:
        pickle.dump(rpginstance, f, -1)

#loads the rpg instance with pickle
def load_rpg():
    with open("data/rpginstance.txt", "rb") as f:
        return pickle.load(f)

try:
    r = load_rpg()
    if r:
        rpginstance.players = r.players
        rpginstance.healthtime = r.healthtime
except:
    pass

try:
    GUILDS = load_guilds()
except:
    pass

#run
client = discord.Client()


#commands
@client.event
async def on_message(message):
    global GUILDS #list of guilds
    global rpginstance #all rpg state is contained in this class

    #ignore self
    if message.author == client.user:
        return
    
    #ping command
    if message.content == "!ping":
        await message.channel.send("pong!")

    #makes a Guild object for the server (serverowner only)
    if message.content == "!registerserver" and message.author == message.guild.owner:
        if(fetch_guild(message.guild.id) == None):
            presrole = await message.guild.create_role(name="President",color=discord.Color.gold(),hoist=True)
            GUILDS.append(Guild(message.guild.id, electionChannel=message.channel.id, presidentRole=presrole.id))
            await message.channel.send("Guild registered!")
            save_guilds(GUILDS)

    #creates a guild object for servers that aren't meant to participate in the map game (upcoming)
    if message.content.startswith("!registerservernonation"):
        GUILDS.append(Guild(message.guild.id, nation=False))
        print("registered")

    """
    RPG COMMANDS
    """
    #at some point this should be an actual help message
    if message.content.startswith("?help") or message.content == "?h":
        await message.channel.send("```RPG module is a work in progress. Please be patient.```")

    #shows your inventory
    if message.content.startswith("?inventory") or message.content == "?i":
        await message.channel.send(f"```{rpginstance.fetchplayer(message.author.id, message.author.name).showinventory()}```")
        save_rpg(rpginstance)

    #shows your rpg stats / equipment
    if message.content.startswith("?stats") or message.content == "?s":
        await message.channel.send(f"```{rpginstance.fetchplayer(message.author.id, message.author.name).showstats()}```")
        save_rpg(rpginstance)

    #shows your current area
    if message.content == "?area":
        await message.channel.send("You are in: `" + rpginstance.fetchplayer(message.author.id, message.author.name).showarea() + "`")
        save_rpg(rpginstance)

    #trigers a battle with a random monster from your current area
    if message.content.startswith("?adventure") or message.content == "?a":
        player = rpginstance.fetchplayer(message.author.id, message.author.name)
        if player.health > 0:
            await message.channel.send("```" + rpginstance.battle(player) + "```")
        else:
            await message.channel.send("You are tired and need to rest!")
        save_rpg(rpginstance)


    #equips an item (weapon/armor) from your inventory
    if message.content.startswith("?equip"):
        itemname = message.content[7:]
        player = rpginstance.fetchplayer(message.author.id, message.author.name)
        if rpginstance.equip(player, itemname):
            await message.channel.send(f"Equipped `{itemname}`!")
        else:
            await message.channel.send(f"Failed to equip `{itemname}`")

    #debug command please remove
    if message.content.startswith("?cheat12345"):
        player = rpginstance.fetchplayer(message.author.id, message.author.name)
        player.health = 10000
        player.maxhealth = 10000
        await message.channel.send("cheater")

    #lists all rpg areas
    if message.content.startswith("?areas"):
        await message.channel.send(rpginstance.showareas())

    #travel to a different rpg area
    if message.content.startswith("?travel"):
        areaname = message.content[8:]
        player = rpginstance.fetchplayer(message.author.id, message.author.name)
        if areaname in rpginstance.areas:
            area = rpginstance.areas[areaname]
            if player.level >= area.requiredLevel:
                player.area = area
                await message.channel.send("You are now in: `" + rpginstance.fetchplayer(message.author.id, message.author.name).showarea() + "`")
            else:
                await message.channel.send("Your level isn't high enough for that area!")
        else:
            await message.channel.send("Travel failed.")

    #creates an rpg item listing on the market
    if message.content.startswith("?sell"):
        args = message.content.split("-") #itemname, quant, unitprice
        if len(args) != 4:
            await message.channel.send("Usage: ?sell-item-quantity-price (per unit)")
        else:
            itemname = args[1]
            quant = int(args[2])
            unitprice = float(args[3])
            player = rpginstance.fetchplayer(message.author.id, message.author.name)
            if itemname in player.inventory:
                g = server_registered(message.guild.id)
                if player.inventory[itemname][1] >= quant and player.inventory[itemname][0].durability == player.inventory[itemname][0].maxdurability:
                    player.deacquire(rpginstance.finditem(itemname), quant)
                    g.addlisting(guilds.Listing(rpginstance.finditem(itemname), quant, unitprice, player))
                    await message.channel.send("Listing posted.")
                    save_guilds(GUILDS)
                else:
                    await message.channel.send("You can't sell what you don't have!")
            elif unitprice < 0.00001 or unitprice > 99999999999:
                await message.channel.send("Bad price")
            else:
                await message.channel.send("You can't sell what you don't have!")

    #shows a context menu for buying rpg items from the market
    if message.content.startswith("?buy"):
        g = server_registered(message.guild.id)
        if message.content.startswith("?buy-"):
            args = message.content.split("-")
            if len(args) == 3:
                name = args[1]
                number = args[2]
                if name in g.listings:
                    player = rpginstance.fetchplayer(message.author.id, message.author.name)
                    listing = g.listings[name][int(number)]
                    if listing.author == player or player.gold >= listing.totalprice:
                        if player.acquire(listing.item, listing.quantity):
                            await message.channel.send(f"`{player.name} gained {listing.item.name}`\n")
                            g.listings[name].remove(listing)
                            if listing.author != player:
                                player.gold -= listing.totalprice
                                listing.author.gold += listing.totalprice
                            save_guilds(GUILDS)
                        else:
                            await message.channel.send("Your inventory isn't big enough!")
                    else:
                        await message.channel.send("You don't have the money for that!")
        else: #view listings
            name = message.content[5:]
            output = "```\n--Listings--\n"
            if name in g.listings:
                for i, listing in enumerate(g.listings[name]):
                    output += f"{i}: {listing.show()}"
                output += f"```To buy a listing, do ?buy-{name}-#"
                await message.channel.send(output)
            else:
                await message.channel.send("That's not for sale here!")


    """
    NATIONSERVER COMMANDS
    """
    #check if server is a nation
    if server_registered(message.guild.id):
        g = server_registered(message.guild.id)

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

        #leaves your political party
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

        #join political party
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


        #adds you to the list of presidential candidates
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
            g = server_registered(message.guild.id)

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
            if message.content.startswith('!forceelection'):
                await nextPhase(g, client)
                save_guilds(GUILDS)

            #resets the guild's election cycle
            if message.content.startswith('!resetelection'):
                g.phase = 0
                save_guilds(GUILDS)

            #prints the current election state (pre-primary, primary, pre-general, general)
            if message.content.startswith('!electionstate'):
                await message.channel.send(g.phase)

            #toggles automatic elections (might be broken, i need to look into that)
            if message.content.startswith('!autoelections'):
                g.settings["autoelections"] = not g.settings["autoelections"]
                if g.settings["autoelections"]: await message.channel.send("Automatic elections on!")
                else: await message.channel.send("Automatic elections off!")
                save_guilds(GUILDS)

            #deletes a political party
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

            #Sets the current guild president to a given member
            if message.content.startswith('!setpresident'):
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
                        raise Exception("hi")
                except:
                    await message.channel.send("Usage: !setpresident member")


print("started!")


#clock that tests for election times and rpg events (elections: wednesday/saturday 8pm)
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
        rpginstance.updatehealth()
        save_rpg(rpginstance)

#main function, just for threading stuff
if __name__ == '__main__':
    client.loop.create_task(clock())
    with open("data/token.txt") as f:
        client.run(f.read())
