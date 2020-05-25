
#classes & definitions
class Guild():
    def __init__(self, server, electionChannel=None, presidentRole=None, nation=True):
        if not nation:
            self.server = int(server)
            self.parties = []
            self.current_pres = None
            self.current_vice = None

            #election
            self.candidates = []
            self.phase = 0 #0, 1, 2, 3
            self.electionMessage = None #message id or array of message ids, internal use
            self.settings = {"autoelections":False}
            self.electionChannel = electionChannel
            self.presidentRole = presidentRole
        self.listings = {} #key:name, value:listings[]
        self.currency = "Gold"

    def nextPhase(self):
        guild = client.get_guild(self.server)
        channel = guild.get_channel(self.electionChannel)
        loop.run_until_complete(nextPhase(this))

    def addlisting(self, listing):
        if listing.name in self.listings:
            self.listings[listing.name].append(listing)
        else:
            self.listings[listing.name] = [listing]
        self.listings[listing.name].sort(key=lambda listing: listing.price)
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

    def show(self):
        return f"{self.quantity} {self.name}(s) for {self.price} {self.currency} each\n"

