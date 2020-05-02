

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
            settings={"autoelections":False, "tax":0}
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
