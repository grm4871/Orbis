import random
import numpy
import time

#planned additions

#planned attributes:
"""
regen
curse
bleed
cursed
some sort of magic
ranged
"""

class MonsterType:
    def __init__(self, name, drops, dmg, speed, armorpen, weaponrange, armorred, health, xp):
        self.name = name

        #process drops
        self.drops = {}
        for loot in drops.split("--"):
            arguments = loot.split(";") #item name;quantity;frequency
            self.drops[(arguments[0],arguments[1])] = float(arguments[2])
        self.dmg = int(dmg)
        self.speed = float(speed)
        self.armorpen = int(armorpen)
        self.weaponrange = int(weaponrange)
        self.armorred = int(armorred)
        self.health = int(health)
        self.xp = int(xp)



class Monster:
    def __init__(self, monstertype):
        self.name = monstertype.name
        self.drops = monstertype.drops #dictionary, (item,quant) keys with percent values
        self.dmg = monstertype.dmg
        self.speed = monstertype.speed
        self.armorpen = monstertype.armorpen
        self.weaponrange = monstertype.weaponrange
        self.armorred = monstertype.armorred
        self.health = monstertype.health
        self.maxhealth = monstertype.health #don't modify this
        self.status = []
        self.xp = monstertype.xp

    def getArmorRed(self):
        return self.armorred

    def getArmorPen(self):
        return self.armorpen

    def getAtkSpeed(self):
        return self.speed

    def getRange(self):
        return self.weaponrange

    def damage(self, damage):
        self.health -= damage

    def attack(self, other):
        damage = self.dmg
        reduction = other.getArmorRed() - self.getArmorPen()
        if reduction > 0:
            damage -= reduction
            if damage < 0: damage = 0
        other.damage(damage)
        #log this attack
        return f"{self.name} attacks {other.name} for {damage} damage ({other.health}/{other.maxhealth})\n"\

    def getdrop(self):
        s = sum(self.drops.values())
        d2 = {k: v/float(s) for k, v in self.drops.items()}
        return list(d2.keys())[numpy.random.choice(range(len(list(d2.keys()))), p=list(d2.values()))]



class Player:
    def __init__(self, name, area):
        self.level = 1
        self.name = name
        self.weapon = None #stat: dmg
        self.hat = None 
        self.shirt = None
        self.pants = None
        self.shoes = None
        self.acc1 = None
        self.acc2 = None
        self.inventorySize = 5
        self.inventory = {} #name:[item, quantity]
        self.gold = 0
        self.status = []
        self.health = 10
        self.maxhealth = 10
        self.area = area
        self.xp = 0

    def getRange(self):
        if self.weapon:
            return self.weapon.weaponrange
        else: #default range (fists)
            return 1

    def getDmg(self):
        if self.weapon:
            return self.weapon.dmg
        else:
            return 1

    def getArmorRed(self):
        reduction = 0
        if self.hat:
            reduction += self.hat.reduction
        if self.shirt:
            reduction += self.shirt.reduction
        if self.pants:
            reduction += self.pants.reduction
        if self.shoes:
            reduction += self.shoes.reduction
        return reduction

    def getArmorPen(self):
        if self.weapon:
            return self.weapon.armorpen
        else:
            return 0

    def getAtkSpeed(self):
        if self.weapon:
            return self.weapon.speed
        else:
            return .1

    """
    attacks another entity (player or monster)
    """
    def attack(self, other):
        #figure out how much damage to do
        output = ""
        if self.weapon: 
            damage = self.weapon.dmg
            self.weapon.durability -= 1
            if self.weapon.durability == 0:
                output += f"{self.name}'s {self.weapon.name} broke!\n"
                self.weapon = None
        else:
            damage = 1
        reduction = other.getArmorRed() - self.getArmorPen()
        if reduction > 0:
            damage -= reduction
            if damage < 0: damage = 0
        #do that amount of damage
        other.damage(damage)
        #log this attack
        output += f"{self.name} attacks {other.name} for {damage} damage ({other.health}/{other.maxhealth})\n"
        return output

    """
    damages the player and reduces armor durability
    called by an attacking enemy
    """
    def damage(self, damage):
        self.health -= damage
        #pick a random armor piece and reduce its durability
        armor = []
        armor.append(self.hat)
        armor.append(self.shirt)
        armor.append(self.pants)
        armor.append(self.shoes)
        try: random.choice(armor).durability -= 1
        except: pass #excepts if no armor equipped

    """
    equips an item to the player
    must be armor or weapon
    """
    def equip(self, item):
        if item.name in self.inventory:
            if isinstance(item, Weapon):
                if self.weapon:
                    self.acquire(self.weapon)
                self.weapon = item
                self.deacquire(item)
                return True
            if isinstance(item, Armor):
                if item.armortype == "hat":
                    if self.hat:
                        self.acquire(self.hat)
                    self.hat = item
                    self.deacquire(item)
                    return True
                if item.armortype == "shirt":
                    if self.shirt:
                        self.acquire(self.shirt)
                    self.shirt = item
                    self.deacquire(item)
                    return True
                if item.armortype == "pants":
                    if self.pants:
                        self.acquire(self.pants)
                    self.pants = item
                    self.deacquire(item)
                    return True
                if item.armortype == "shoes":
                    if self.shoes:
                        self.acquire(self.shoes)
                    self.shoes = item
                    self.deacquire(item)
                    return True
        return False

    """
    Heals player x health
    """
    def heal(self, health):
        self.health += health
        if self.health > self.maxhealth:
            self.health = self.maxhealth            

    """
    outputs player's gear in string format
    """
    def showstats(self):
        output = f"{self.name}, health: {self.health}/{self.maxhealth} \n"
        output += f"level {self.level} - {self.xp}/{int(10 * (1.05**self.level))} xp\n"
        if self.weapon:
            output += f"weapon: {self.weapon.name} - {self.weapon.durability} durability left\n"
        else:
            output += 'no weapon equipped!\n'
        if self.hat:
            output += f"hat: {self.hat.name} - {self.hat.durability} durability left\n"
        else:
            output += 'no hat equipped!\n'
        if self.shirt:
            output += f"shirt: {self.shirt.name}\n - {self.shirt.durability} durability left"
        else:
            output += 'no shirt equipped!\n'
        if self.pants:
            output += f"pants: {self.pants.name}\n - {self.pants.durability} durability left"
        else:
            output += 'no pants equipped!\n'
        if self.shoes:
            output += f"shoes: {self.shoes.name}\n - {self.shoes.durability} durability left"
        else:
            output += 'no shoes equipped!\n'
        return output

    def showinventory(self):
        output = "Inventory:\n"
        output += f"Gold: {self.gold}\n"
        for item in self.inventory:
            output += item + ": " + str(self.inventory[item][1]) + "\n"
        return output

    def showarea(self):
        return self.area.name

    def acquire(self, item, quantity=1):
        if self.inventorySize >= len(self.inventory):
            if item.name in self.inventory:
                self.inventory[item.name][1] += quantity
            else:
                self.inventory[item.name] = [item, quantity]
            return True
        else:
            return False
    
    def deacquire(self, item, quantity=1):
        if item.name in self.inventory:
            if self.inventory[item.name][1] > quantity:
                self.inventory[item.name][1] -= quantity
            else:
                self.inventory.pop(item.name)
            return True
        return False

    def gainxp(self, xp):
        xpgoal = int(10 * (1.05**self.level))
        self.xp += xp
        if self.xp >= xpgoal:
            self.xp -= xpgoal
            self.level += 1
            self.maxhealth += 1
            self.health = self.maxhealth
            return f"{self.name} leveled up to level {self.level}!"
        return f"{self.name} gained {xp} xp - {self.xp}/{xpgoal}"

class ItemInstance:
    def __init__(self, item):
        self.item = item
        self.durability = item.durability

class Item:
    def __init__(self, name, durability, attributes):
        self.name = name
        self.durability = int(durability) #when this reaches zero the item breaks
        self.maxdurability = self.durability
        self.attributes = attributes #list of special attributes (like minecraft enchantments)
        self.forsale = False

class Weapon(Item):
    def __init__(self, name, durability, attributes, dmg, speed, armorpen, weaponrange):
        super().__init__(name, durability, attributes)
        self.dmg = int(dmg) #the raw damage output
        self.speed = float(speed) #speed
        self.armorpen = int(armorpen) #reduction of armor damage reduction
        self.weaponrange = int(weaponrange) #distance weapon is effective at

class Armor(Item):
    def __init__(self, name, durability, attributes, reduction, armortype):
        super().__init__(name, durability, attributes)
        self.reduction = int(reduction) #damage reduction power
        self.armortype = armortype #the type of armor (string) eg shirt, pants, hat, shoes

class Accessory(Item):
    def __init__(self, name, durability, attributes):
        super().__init__(name, durability, attributes)


class Area():
    def __init__(self, monsterfreq, attributes, requiredLevel, name):
        self.monsterfreq = monsterfreq #dictionary of monsters with name keys, frequency values
        self.attributes = attributes
        self.requiredLevel = requiredLevel
        self.name = name

    """
    returns a random enemy from the area's monsters
    """
    def get_random_enemy(self):
        #thank you stackoverflow
        s = sum(self.monsterfreq.values())
        d2 = {k: v/float(s) for k, v in self.monsterfreq.items()}
        return numpy.random.choice(list(d2.keys()), p=list(d2.values()))

"""
conducts a battle between two fighters (monster / player) until either dies or time runs out

fighter1: the first fighter
fighter2: the second fighter
dist: how far apart they start (farther means ranged weapons get a head start)
areaEffects: list of special battle arena attributes that are in effect (not yet implemented)
"""
def battle(fighter1, fighter2, dist, areaEffects):
    f1time = 1
    f2time = 1
    output = ""
    #figure out (randomly) who attacks first
    if bool(random.getrandbits(1)):
        fighter1, fighter2 = fighter2, fighter1
    #combat loop
    timer = 0
    while(True):
        #one step of combat
        if f1time >= 1 and fighter1.getRange() <= dist:
            output += fighter1.attack(fighter2)
            f1time -= 1
            timer += 1
        if f2time >= 1 and fighter2.getRange() <= dist and fighter2.health != 0:
            output += fighter2.attack(fighter1)
            f2time -= 1
            timer += 1
        f1time += fighter1.getAtkSpeed()
        f2time += fighter2.getAtkSpeed()
        dist -= 1
        if timer > 20 or fighter1.health == 0 or fighter2.health == 0:
            if fighter1.health == 0:
                output += f"{fighter1.name} is dead!\n"
            elif fighter2.health == 0:
                output += f"{fighter2.name} is dead!\n"
            else:
                output += "Both combatants are tired and can no longer fight!\n" #fight went on too long (needs to fit in a discord message)
            break
    return output

def load():
    #load sets of items from files

    #weapons
    weapons = {}
    with open("data/rpg/weapons.txt") as f:
        for line in f.readlines():
            if not line[0] == "#":
                spl = line.split('"')
                weapons[spl[1]] = (Weapon(spl[1], spl[3], spl[5], spl[7], spl[9], spl[11], spl[13]))

    #armor
    armor = {}
    with open("data/rpg/hats.txt") as f:
        for line in f.readlines():
            if not line[0] == "#":
                spl = line.split('"')
                armor[spl[1]] = (Armor(spl[1], spl[3], spl[5], spl[7], "hat"))
    with open("data/rpg/shirts.txt") as f:
        for line in f.readlines():
            if not line[0] == "#":
                spl = line.split('"')
                armor[spl[1]] = (Armor(spl[1], spl[3], spl[5], spl[7], "shirts"))
    with open("data/rpg/pants.txt") as f:
        for line in f.readlines():
            if not line[0] == "#":
                spl = line.split('"')
                armor[spl[1]] = (Armor(spl[1], spl[3], spl[5], spl[7], "pants"))
    with open("data/rpg/shoes.txt") as f:
        for line in f.readlines():
            if not line[0] == "#":
                spl = line.split('"')
                armor[spl[1]] = (Armor(spl[1], spl[3], spl[5], spl[7], "shoes"))

    #monsters
    monsters = {}
    with open("data/rpg/monsters.txt") as f:
        for line in f.readlines():
            if not line[0] == '#':
                spl = line.split('"')
                monsters[spl[1]] = MonsterType(spl[1], spl[3], spl[5], spl[7], spl[9], spl[11], spl[13], spl[15], spl[17])

    #areas
    areas = {}
    currentarea = ""
    currentareafreq = {}
    currentlevel = 0

    with open("data/rpg/areas.txt") as f:
        for line in f.readlines():
            if line[:5] == "AREA ":
                #save last area
                if currentarea != "":
                    areas[currentarea] = Area(currentareafreq, [], currentlevel, currentarea)
                #new area
                currentarea = line.split(" ")[1]
                currentareafreq = {}
                currentlevel = int(line.split(" ")[2])
            elif line[0] != "#":
                #add monster to area
                currentareafreq[line.split('"')[1]] = int(line.split('"')[3])
        areas[currentarea] = Area(currentareafreq, [], currentlevel, currentarea)

    return GameInstance(areas, weapons, armor, monsters)


class GameInstance():
    def __init__(self, areas, weapons, armor, monsters):
        self.players = {}
        self.areas = areas
        self.weapons = weapons
        self.armor = armor
        self.monsters = monsters
        self.healthtime = time.time()

    """
    conducts a battle between the player and a random monster from the area
    """
    def battle(self, player):
        #get monster
        monster = Monster(self.monsters[player.area.get_random_enemy()])
        #get output from the fight
        output = battle(player, monster, 10, [])
        if monster.health == 0 and player.health != 0: #player won the fight
            drop = monster.getdrop()
            output += self.giveitem(drop[0], drop[1], player)
            output += player.gainxp(monster.xp)
        return output

    """
    update players health, healing by 1 health per hour
    """
    def updatehealth(self):
        newhealth = int((time.time() - self.healthtime) / 3600)
        self.healthtime = self.healthtime + newhealth * 3600
        for p in self.players.values():
            p.heal(newhealth)

    """
    gets a player by id (discord) and if doesn't exist, creates
    also includes name so that the player has a name
    """
    def fetchplayer(self, playerid, name):
        if playerid in self.players:
            return self.players[playerid]
        else:
            self.players[playerid] = Player(name, self.areas["Plains"])
            return self.players[playerid]

    """
    gets an item object from a name, gives it to a player
    todo: let function interact with guilds
    """
    def giveitem(self, itemname, quantity, player):
        if itemname == "Gold":
            player.gold += int(quantity)
            return f"{player.name} gained {quantity} gold!\n"
        item = self.finditem(itemname)
        if item:
            if player.acquire(item):
                return f"{player.name} gained {itemname}\n"
            else:
                return f"{player.name}'s inventory is full!\n"
        #else, can't find item

    """
    finds an item object based on its name
    """
    def finditem(self, itemname):
        if itemname in self.weapons:
            return self.weapons[itemname]
        if itemname in self.armor:
            return self.armor[itemname]
        return False

    def equip(self, player, itemname):
        item = self.finditem(itemname)
        if item:
            if player.equip(item):
                return True
        return False

    def showareas(self):
        output = "Areas:\n"
        for area in self.areas:
            output += f"`{area}`: Level {self.areas[area].requiredLevel}\n"
        return output

if __name__ == "__main__":
    #load()
    pass
