import discord
from datetime import datetime
import pytz
import asyncio
import os
from db import Db


#import logging
#logging.basicConfig(filename='log.txt', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

from  dotenv import load_dotenv
load_dotenv()


database = Db()
#database.request("DELETE FROM birthdays", 'change')
#database.request (("ALTER TABLE birthdays ADD timezone TEXT;"), 'change')
#database.connection.commit()

client = discord.Client()
class Bday():
    def __init__(self, closestDateInfo = []):
        self.closestDateInfo = closestDateInfo
        self.currentDate = datetime.now(pytz.utc)
        self.closestDate = None
        self.task = asyncio.ensure_future(self.bdayTimer())
    async def refreshTimer(self):
        self.task.cancel()
        if len(self.closestDateInfo) == 0:
            self.__init__() 
            await self.check()
        else:     
            self.currentDate = datetime.now(pytz.utc)
            self.task = asyncio.ensure_future(self.bdayTimer())
    async def check(self):
        self.task.cancel()
        self.checkGuild()
        allBdays =  database.request("SELECT * FROM birthdays", "fetchall")
        self.removedChannels = []
        for i in allBdays:
            if self.checkUserChannel(i):
                continue

            elif i in self.closestDateInfo:
                self.closestDateInfo.remove(i)
                newDate = i[1].replace(year = i[1].year + 1)
                if i[3] != None:
                    database.request(("UPDATE birthdays SET date = %s, channel = %s WHERE userId =%s AND guild = %s", (newDate, i[2], i[0], i[3])), "change")
                else:
                    database.request(("UPDATE birthdays SET date = %s WHERE userId =%s AND channel = %s", (newDate, i[0], i[2])), "change")
                allBdays.append((i[0],newDate,i[2],i[3]))
            elif self.closestDate == None and i[1] > self.currentDate:
                self.closestDate = i[1]
                self.closestDateInfo.append(i)
            elif i[1] < self.currentDate:
                try:
                    self.closestDateInfo.remove(i)
                except:
                    pass
                newDate = i[1].replace(year = i[1].year + 1)
                if i[3] != None:
                    database.request(("UPDATE birthdays SET date = %s, channel = %s WHERE userId =%s AND guild = %s", (newDate, i[2], i[0], i[3])), "change")
                else:
                    database.request(("UPDATE birthdays SET date = %s WHERE userId =%s AND channel = %s", (newDate, i[0], i[2])), "change")
                #utc = pytz.timezone("UTC")
                #utcTimestamp = utc.localize(i[1])
                tz = pytz.timezone(i[4])
                localizedTimestamp = i[1].astimezone(tz)
                print(localizedTimestamp)
                print(localizedTimestamp.tzname())
                print(localizedTimestamp.date())
                try:
                    await client.get_channel(i[2]).send("While I was offline, we missed " + client.get_user(i[0]).mention + "'s Bday on " + str(localizedTimestamp.date()) + ' ' + i[4].upper())
                except AttributeError:
                    try:
                        await client.get_user(i[0]).send("While I was offline, we missed " +client.get_user(i[0]).mention + "'s Bday on " + str(localizedTimestamp.date()) + ' ' + i[4].upper())
                    except AttributeError:
                        self.deleteUser(i[0])
                allBdays.append((i[0],newDate,i[2],i[3]))

            elif i[1] < self.closestDate:
                self.closestDate = i[1]
                self.closestDateInfo.clear()
                self.closestDateInfo.append(i)
            elif i[1] == self.closestDate:
                self.closestDateInfo.append(i)

        database.connection.commit()
        self.task = asyncio.ensure_future(self.bdayTimer())
    def checkGuild(self):
        database.request(("DELETE FROM birthdays WHERE guild NOT IN %s AND guild IS NOT NULL ",(tuple(i.id for i in client.guilds),)), "change")
        database.connection.commit()
        self.closestDateInfo = [j for j in self.closestDateInfo if j[3] in [i.id for i in client.guilds] or j[3] == None]
    def checkUserChannel(self, entry):
        if entry[3] != None and client.get_guild(entry[3]).get_member(entry[0]) == None:
            database.request(("DELETE FROM birthdays WHERE guild = %s AND userId = %s", (entry[3],entry[0])), "change")
            try:
                self.closestDateInfo.remove(entry)
            except ValueError:
                pass
            return True
        elif entry[3] != None and client.get_channel(entry[2]) == None and entry[2] not in self.removedChannels:
            database.request(("DELETE FROM birthdays WHERE channel = %s", (entry[2],)), "change")
            self.closestDateInfo = [j for j in self.closestDateInfo if j[2] != entry[2]]
            self.removedChannels.append(entry[2])
            return True
        else:
            return False
    def deleteUser(self, user):
        database.request(("DELETE FROM birthdays WHERE userId = %s", (user,)), "change")
        self.closestDateInfo = [j for j in self.closestDateInfo if j[0] != user]
    async def bdayTimer(self): 
        if self.closestDate != None:
            print(self.closestDateInfo)
            await asyncio.sleep((self.closestDate - self.currentDate).total_seconds())
            self.checkGuild()
            self.removedChannels = []
            for i in self.closestDateInfo[:]:
                if self.checkUserChannel(i):
                    continue
                try:
                    await client.get_channel(i[2]).send("It's " +client.get_user(i[0]).mention + "'s Bday!" )
                except AttributeError:
                    try:
                        await client.get_user(i[0]).send("It's " +client.get_user(i[0]).mention + "'s Bday!")
                    except AttributeError:
                        self.deleteUser(i[0])

            database.connection.commit()
            self.__init__(self.closestDateInfo) 
            await self.check()

    async def update(self,new, existing):
        if self.closestDate == None: 
            self.closestDate = new[1]
            self.closestDateInfo.append(new)
        elif new[1] == self.closestDate:
            self.closestDateInfo.append(new)
        elif new[1] < self.closestDate:
            self.closestDate = new[1]
            self.closestDateInfo.clear()
            self.closestDateInfo.append(new)
        try:
            self.closestDateInfo.remove(existing)
        except:
            pass
        await self.refreshTimer()


global birthday
async def createBday(): #Can't call async functions from constructor, so I have to do this
    global birthday
    birthday = Bday()
    await birthday.check()              


@client.event
async def on_ready():
    await client.change_presence(activity = discord.Game(name = "$help"))
    await createBday()
    print("ready")

@client.event # essentially:  on_message = client.event(on_message), takes the function as its parameter and creates a new method on the client itself = func
#now, when client recieves a message, it creates a message obj and passes it into its attribute
async def on_message(message):
    if message.author == client.user:
        return
    
    if "rosie" in message.content.lower():
        await message.channel.send("woof") #async stuff allows program to work on other stuff while some processes are waiting to finish i.e work on stuff while message is still sending?
    
    if message.content.lower().startswith("$help"):
        embed = discord.Embed(
            #description = 'tests',
            colour = discord.Color(0xFF57C4)
        )
        embed.set_author(name = 'Commands', icon_url = 'https://cdn.discordapp.com/avatars/725121351584710707/96d4dfce31014cbdea61c9fe2a433ece.png?')
        embed.add_field(name = '$bday', value = 'Set your bday which will be announced in the channel you set it in\n `$bday mm/dd timezone`\n [List of timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)', inline = False)
        embed.add_field(name = "$checkbday", value = "For a user's bday: `$checkbday @user`\nFor your own: `$checkbday`", inline = False)
        embed.add_field(name = "$clearbday", value = "Delete your birthday", inline = False)
        embed.add_field(name = "$luck", value = "Gives you luck", inline = False)
        embed.add_field(name = "$pet", value = "Pet bork bot", inline = False)
        embed.add_field(name = "$poll", value = "Create a poll\n`$poll [title]{option 1, option 2,...}`", inline = False)
        embed.add_field(name = "$qp", value = "Create a quick poll which is a ✅ or ❌ to your message", inline = False)
        embed.add_field(name = "$uwu", value = "uwu", inline = False)
        await message.channel.send(embed = embed)
        #await message.channel.send("Commands: \n>>> $pet \n$luck\n$poll\n$qp\n$uwu")
    
    elif message.content.lower().startswith("$pet"):
        await message.channel.send(message.author.mention +" has pet me!")
    
    elif message.content.lower().startswith("$luck"):
        #mentioned = message.mentions
        sent = await message.channel.send("You have been visited by the doggo of good garlic fortune. React with 👍 in 10 seconds for little to no benefit",file = discord.File('Garlic_dog.png'))
        reacted = await sent.add_reaction('👍')
        def check (reaction,user):
            return user == message.author and str(reaction.emoji) == "👍" and sent.id == reaction.message.id #bool
        try:
            reaction, user = await client.wait_for("reaction_add", timeout = 10, check = check)
        except asyncio.TimeoutError:
            await message.channel.send("No luck for {.author.name}".format(message))
            reacted.remove()
            
        else:
            await message.channel.send("{.name} has been blessed".format(user))
    
    elif message.content.lower().startswith("$poll"):

        titleStart = message.content.find('[')
        titleEnd = message.content.find(']')
        optionStart = message.content.find('{')
        optionEnd = message.content.find('}')
        if -1 in {titleStart ,titleEnd ,optionStart, optionEnd}  or ''in {message.content[titleStart +1:titleEnd].strip(), message.content[optionStart +1:optionEnd].strip()}:
            await message.channel.send("Format should be: $poll [title] {options 1, option 2...}")
        else:
            options = message.content[optionStart + 1 : optionEnd]
            options = options.split(",")

            if len(options) > 8:
                await message.channel.send("Too many options")
                return

            output = message.content[titleStart +1:titleEnd]+ "\n>>> "
            emote = 97
            for i in options: #round about way to avoid hardcoding each emoji into the code, but I had to do it anyways for the reaction portion so no point in doing it this way here
                if i.strip() == '':
                    await message.channel.send("Empty options")
                    return
                output = output +  ":regional_indicator_" + chr(emote)+": " +i.strip() +"\n"
                emote +=1
            sent = await message.channel.send(output)
            reactions = ['🇦','🇧','🇨','🇩','🇪','🇫','🇬','🇭']

            for i in range (len(options)):
                await sent.add_reaction(reactions[i])
    elif message.content.lower().startswith("$qp"):
        await message.add_reaction("✅")
        await message.add_reaction("❌")

    elif message.content.lower().startswith("$uwu"):
        toSend = message.content[4:]
        toSend = toSend.replace("u","uwu").replace("U","UWU").replace("o","owo").replace("O","OWO").replace("l","w").replace("L","W").replace("r","w").replace("R","W")
        await message.channel.send(toSend)
    
    elif message.content.lower().startswith("$clearbday"):
        try: 
            existing = database.request(("SELECT * FROM birthdays WHERE userID = %s AND guild = %s LIMIT 1 ;",(message.author.id, message.guild.id)),"fetchone")
        except AttributeError:
            existing = database.request(("SELECT * FROM birthdays WHERE userID = %s AND channel = %s LIMIT 1 ;", (message.author.id, message.channel.id)),"fetchone")
        if existing != None:
            try:
                database.request(("DELETE FROM birthdays WHERE guild = %s AND userId = %s", (message.guild.id, message.author.id)), "change")
                birthday.closestDateInfo = [i for i in birthday.closestDateInfo if i[3] != message.guild.id or i[0] != message.author.id]
            except AttributeError:
                database.request(("DELETE FROM birthdays WHERE channel = %s AND userId = %s", (message.channel.id, message.author.id)), "change")
                birthday.closestDateInfo = [i for i in birthday.closestDateInfo if i[2] != message.channel.id or i[0] != message.author.id]
            database.connection.commit()
            await birthday.refreshTimer()            
            print("YEA")
            await message.channel.send("Cleared")
        else: 
            await message.channel.send("No record on file")
    elif message.content.lower().startswith('$checkbday'):
        try:
            user = message.mentions[0]
        except IndexError as e:
            print (e)
            user = message.author
        try: 
            info = database.request(("SELECT * FROM birthdays WHERE userID = %s AND guild = %s LIMIT 1 ;",(user.id, message.guild.id)),"fetchone")
        except AttributeError:
            info = database.request(("SELECT * FROM birthdays WHERE userID = %s AND channel = %s LIMIT 1 ;", (user.id, message.channel.id)),"fetchone")

        if info == None or birthday.checkUserChannel(info):
            await message.channel.send(user.mention + " has no bday on record")
            return
        tz = pytz.timezone(info[4])
        localizedTimestamp = info[1].astimezone(tz)
        try:
            await message.channel.send(user.mention + "'s Bday is on " + str(localizedTimestamp.date()) + ' ' + info[4].upper() + ' in ' + client.get_channel(info[2]).mention)
        except AttributeError:
            await message.channel.send(user.mention + "'s Bday is on " + str(localizedTimestamp.date()) + ' ' + info[4].upper())



    elif message.content.lower().startswith("$bday"):
        try:
            try:
                date = datetime.strptime(message.content.split(" ")[1].strip(), "%m/%d")
                date = date.replace(year=datetime.now(pytz.utc).year)
                tzString = message.content.split(" ")[2].strip()
                tz = pytz.timezone(tzString)
                date = tz.localize(date)
                if date < datetime.now(tz):
                    date = date.replace(year=datetime.now(tz).year + 1)
                
            except IndexError as e:
                print(e)
                await message.channel.send("Format should be: $bday mm/dd timezone \nYou are missing some fields")
                return
            except ValueError as e:
                print(e)
                await message.channel.send("Format should be: $bday mm/dd timezone \nYour date is invalid")
                return
            except pytz.exceptions.UnknownTimeZoneError as e:
                print(e)
                await message.channel.send("Your timezone is invalid")
                return
                
            try: 
                existing = database.request(("SELECT * FROM birthdays WHERE userID = %s AND guild = %s LIMIT 1 ;",(message.author.id, message.guild.id)),"fetchone")
            except AttributeError:
                existing = database.request(("SELECT * FROM birthdays WHERE userID = %s AND channel = %s LIMIT 1 ;", (message.author.id, message.channel.id)),"fetchone")
            if existing == None:
                try:
                    new = (message.author.id, date, message.channel.id, message.guild.id, tzString)
                    database.request(('INSERT INTO birthdays (userId,date,channel,guild, timezone) VALUES (%s, %s, %s, %s, %s)', new),"change")
                except AttributeError:
                    new = (message.author.id, date, message.channel.id, None, tzString)
                    database.request(('INSERT INTO birthdays (userId,date,channel, guild, timezone) VALUES (%s, %s, %s,%s, %s)', new),"change")
            elif existing[1] == date and existing [2] == message.channel.id:
                await message.channel.send("This is matches your existing record")
                return
            else:
                try:
                    new = (message.author.id, date, message.channel.id, message.guild.id, tzString)
                    database.request(("UPDATE birthdays SET date = %s, channel = %s, timezone = %s WHERE userId =%s AND guild = %s", (date, message.channel.id, tzString, message.author.id, message.guild.id)), "change")
                except AttributeError:
                    new = (message.author.id, date, message.channel.id, None, tzString)
                    database.request(("UPDATE birthdays SET date = %s, timezone = %s WHERE userId =%s AND channel = %s", (date,tzString, message.author.id, message.channel.id)), "change")
            database.connection.commit()
            #global birthday
            await birthday.update(new, existing)
            await message.channel.send("Saved")
        except ConnectionError:
            await message.channel.send("Could not connect to database D:")
       # except Exception as e:
        #    print(e)

'''
@client.event
async def on_reaction_update(reaction, user): #only works when message is in internal message cache i.e message sent when bot was online
    if user == client.user:
        await reaction.message.channel.send("haha i reacted")
    else:
        await reaction.message.channel.send("{.name} has reacted".format(user))
'''
client.run(os.environ["token"])
