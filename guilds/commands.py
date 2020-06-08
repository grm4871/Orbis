"""
Handlers for the RPG commands.
"""
from guilds import guilds_instance
import guilds
from command_parser import CommandParser
import webcolors
import discord

"""
UTILITY FUNCTIONS
"""
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


"""
GUILD MODULE COMMANDS
"""
parser = CommandParser("!")
parser.add_custom_context("guild", lambda ctx: guilds_instance.fetch_guild(ctx.message.guild.id))

@parser.command(aliases="h", help_text="show this help message")
async def help(ctx):
    response = "**Commands:**\n"
    for command in parser.commands:
        help_text = parser.get_command_help(command)
        if help_text is not None:
            response += "\n" + help_text
    await ctx.send(response)

@parser.command(help_text="shows the guild's parties")
async def parties(ctx):
    #lists the guild's parties
    outputs = []
    idx = 0
    num = 0
    outputs.append("")
    for party in ctx.guild.parties:
        if num > 8:
            idx+=1
            num=0
            outputs.append("")
        outputs[idx] += "`!joinparty " + party.name + "`\n"
        num+=1
    for m in outputs:
        if m == "":
            await ctx.send("There are no parties!")
        else:
            await ctx.send(m)

@parser.command(help_text="lists presidential candidates")
async def candidates(ctx):
    outputs = []
    idx = 0
    num = 0
    outputs.append("")
    for c in ctx.guild.candidates:
        if num > 8:
            idx+=1
            num=0
            outputs.append("")
        try:
            outputs[idx] += "`" + ctx.message.guild.get_member(int(c)).name + "`\n"
        except:
            pass
        num+=1
    for m in outputs:
        if m == "":
            await ctx.send("No candidates!")
        else:
            await ctx.send(m)


@parser.command(help_text="creates a new political party",
                usage_text="!createparty color name")
async def createparty(ctx, color, *, party_name):
    server = ctx.message.guild
    #leave old party
    oldparty = None
    for party in ctx.guild.parties:
        partyrole = server.get_role(party.role)
        if partyrole in ctx.message.author.roles:
            await ctx.message.author.remove_roles(partyrole)
            oldparty = party
            try:
                oldparty.members.remove(ctx.message.author.id)
            except:
                pass
    if oldparty:
        if oldparty.members == []:
            partyrole = server.get_role(oldparty.role)
            await partyrole.delete()
            ctx.guild.parties.remove(oldparty)
    #check if name exists
    party = None
    for p in ctx.guild.parties:
        if p.name == party_name:
            party = p
    if not party:
        #get color
        _color = get_color(color)
        if not _color:
            await ctx.send("Party could not be created")
        else:
            role = await ctx.message.guild.create_role(name=party_name,color=discord.Color(int(_color,16)),hoist=True)
            await ctx.message.author.add_roles(role)
            colorrgb = webcolors.hex_to_rgb("#" + _color)
            ctx.guild.parties.append(guilds.Party(party_name,(colorrgb[0],colorrgb[1],colorrgb[2]),[ctx.message.author.id],role.id,""))
            await ctx.message.channel.send('Party created successfully')
    else:
        await ctx.message.channel.send("That party already exists!")
    guilds_instance.save()


@parser.command(help_text="leave your current political party")
async def leaveparty(ctx):
    server = ctx.message.guild
    oldparty = None
    for party in ctx.guild.parties:
        partyrole = server.get_role(party.role)
        if partyrole in ctx.message.author.roles:
            await ctx.message.author.remove_roles(partyrole)
            oldparty = party
            try:
                oldparty.members.remove(ctx.message.author.id)
            except:
                pass
    if oldparty:
        if oldparty.members == []:
            partyrole = server.get_role(oldparty.role)
            await partyrole.delete()
            ctx.guild.parties.remove(oldparty)
    await ctx.send("Successfully left party")
    guilds_instance.save()

@parser.command(help_text="run for the office of server president")
async def runforoffice(ctx):
    #adds you to the list of presidential candidates
    if ctx.guild.phase == 0:
        inParty = False
        for party in ctx.guild.parties:
            if ctx.message.author.id in party.members:
                inParty = True
        if (not ctx.message.author.id in ctx.guild.candidates) and inParty:
            ctx.guild.candidates.append(message.author.id)
            await ctx.send('You are now a candidate!')
            guilds_instance.save()
        elif inParty == False:
            await ctx.send("Join a party first!")
        else:
            await ctx.send("You are already a candidate!")
    else:
        await ctx.send("Candidates are already locked in for this election!")


@parser.command(help_text="join a political party",
                usage_text="!joinparty party_name")
async def joinparty(ctx, *, party_name):
    server = ctx.message.guild
    name = ctx.message.content[11:]
    party = None
    for p in ctx.guild.parties:
        if p.name == name:
            party = p
    if party:
        party.members.append(ctx.message.author.id)
        #find old party
        oldparty = None
        for p in ctx.guild.parties:
            partyrole = server.get_role(p.role)
            if partyrole in ctx.message.author.roles:
                await ctx.message.author.remove_roles(partyrole)
                oldparty = p
                try:
                    oldparty.members.remove(ctx.message.author.id)
                except:
                    pass
        if oldparty and oldparty != party:
            if oldparty.members == []:
                partyrole = server.get_role(oldparty.role)
                await partyrole.delete()
                ctx.guild.parties.remove(oldparty)
        partyrole = server.get_role(party.role)
        try:
            await ctx.message.author.add_roles(partyrole)
        except:
            role = await server.create_role(name=party.name,color=discord.Color.from_rgb(party.color[0],party.color[1],party.color[2]),hoist=True)
            party.role = role.id
            await ctx.message.author.add_roles(role)
        await ctx.send('Joined!')
    else:
        await ctx.send('This party doesn\'t exist!')
    guilds_instance.save()

"""
SERVER OWNER COMMANDS
"""
owner_parser = CommandParser("!!")
owner_parser.add_custom_context("guild", lambda ctx: guilds_instance.fetch_guild(ctx.message.guild.id))

@owner_parser.command(help_text="show this help message")
async def help(ctx):
    response = "**Guild Owner Commands:**\n"
    for command in owner_parser.commands:
        help_text = owner_parser.get_command_help(command)
        if help_text is not None:
            response += "\n" + help_text
    await ctx.send(response)

@owner_parser.command(help_text="forces the guild's election cycle to the next phase")
async def forceelection(ctx):
    await ctx.guild.nextPhase(ctx.message.guild)
    guilds_instance.save()

@owner_parser.command(help_text="resets the guild's election cycle to phase zero")
async def resetelection(ctx):
    ctx.guild.phase = 0
    guilds_instance.save()

@owner_parser.command(help_text="sends the guild's current election cycle state")
async def electionstate(ctx):
    await ctx.send(ctx.guild.phase)

@owner_parser.command(help_text="toggles automatic elections")
async def autoelections(ctx):
    ctx.guild.settings["autoelections"] = not ctx.guild.settings["autoelections"]
    if ctx.guild.settings["autoelections"]: await ctx.send("Automatic elections on!")
    else: await ctx.send("Automatic elections off!")
    guilds_instance.save()

@owner_parser.command(help_text="deletes a political party")
async def deleteparty(ctx, *, party_name):
    party = None
    for p in ctx.guild.parties:
        if p.name == party_name:
            party = p
    if party:
        partyrole = ctx.message.guild.get_role(party.role)
        await partyrole.delete()
        ctx.guild.parties.remove(party)
        await ctx.send('Party deleted successfully!')
    else:
        await ctx.send('Party not found')

@owner_parser.command(help_text="sets the current guild president to any member")
async def setpresident(ctx, *, member_name):
    try:
        if len(ctx.message.mentions) > 0:
            member = ctx.message.mentions[0]
            if ctx.message.guild.current_pres:
                oldpres = ctx.message.guild.get_member(int(ctx.guild.current_pres))
            else:
                oldpres = None
            try:
                presrole = ctx.message.guild.get_role(int(ctx.guild.presidentRole))
                await member.add_roles(presrole)
            except:
                presrole = await ctx.guild.create_role(name="President",color=discord.Color.gold(),hoist=True)
                ctx.guild.presidentRole = presrole.id
                await member.add_roles(presrole)
            if oldpres and oldpres != member.id:
                await oldpres.remove_roles(presrole)
            ctx.guild.current_pres = member.id
            await message.channel.send("Your new president is: " + member.mention)
        else:
            raise Exception("no args")
    except:
        await message.channel.send("Usage: !setpresident member")

@owner_parser.command(help_text="sets the election channel to the one this message was sent in")
async def setelectionchannel(ctx):
    ctx.guild.electionChannel = ctx.message.channel
    await ctx.message.channel.send("Election channel set!")

@owner_parser.command(help_text="sets the guild's map color")
async def setcolor(ctx, color_name):
    color = get_color(color_name)
    if color:
        guild.color = color
        await message.channel.send("Color set!")
    else:
        await message.channel.send("Invalid color")

@owner_parser.command(help_text="sets the nation's income tax rate")
async def settax(ctx, rate):
    rate = float(rate)
    if rate >= 0 and rate < 1:
        guild.settings["tax"] = rate
        await message.channel.send("Tax rate set!")
    else:
        await message.channel.send("Tax rate must be between zero and one")

@owner_parser.command(help_text="sets the nation's sales tax rate")
async def setsalestax(ctx, rate):
    rate = float(rate)
    if rate >= 0 and rate < 1:
        guild.settings["salestax"] = rate
        await message.channel.send("Tax rate set!")
    else:
        await message.channel.send("Tax rate must be between zero and one")