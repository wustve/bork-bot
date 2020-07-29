import discord
from datetime import datetime
import asyncio
import os
from db import Db

from  dotenv import load_dotenv
load_dotenv()

#database.execute ("DELETE FROM birthdays")
#database.connection.commit()

database = Db()

client = discord.Client()
class Bday():
    def __init__(self, closestDateInfo = []):
        self.closestDateInfo = closestDateInfo
        self.currentDate = datetime.now()
        self.closestDate = None
        self.task = asyncio.ensure_future(self.bdayTimer())

    async def check(self):
        self.task.cancel()
        allBdays =  database.request("SELECT * FROM birthdays", "fetchall")
        for i in allBdays:
            if i in self.closestDateInfo:
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
                    self.closestDateInfo.pop(self.closestDateInfo.index(i))
                except:
                    pass
                newDate = i[1].replace(year = i[1].year + 1)
                if i[3] != None:
                    database.change(("UPDATE birthdays SET date = %s, channel = %s WHERE userId =%s AND guild = %s", (newDate, i[2], i[0], i[3])), "change")
                else:
                    database.change(("UPDATE birthdays SET date = %s WHERE userId =%s AND channel = %s", (newDate, i[0], i[2])), "change")
                    
                try:
                    await client.get_channel(i[2]).send("While I was offline, we missed " + client.get_user(i[0]).mention + "'s Bday on " + str(i[1].date()) )
                except:
                    await client.get_user(i[0]).send("While I was offline, we missed " +client.get_user(i[0]).mention + "'s Bday on " + str(i[1].date()) )
            elif i[1] < self.closestDate:
                self.closestDate = i[1]
                self.closestDateInfo.clear()
                self.closestDateInfo.append(i)
            elif i[1] == self.closestDate:
                self.closestDateInfo.append(i)
        
        database.connection.commit()
        self.task = asyncio.ensure_future(self.bdayTimer())

    async def bdayTimer(self): 
        if self.closestDate != None:
            await asyncio.sleep((self.closestDate - self.currentDate).total_seconds())
            for i in self.closestDateInfo:
                try:
                    
                    await client.get_channel(i[2]).send("It's " +client.get_user(i[0]).mention + "'s Bday!" )
                except:
                    await client.get_user(i[0]).send("It's " +client.get_user(i[0]).mention + "'s Bday!")

            self.__init__(self.closestDateInfo) 
            await self.check()
    async def update(self,new, existing):
        print(self.closestDateInfo)
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

        if len(self.closestDateInfo) == 0:
            self.closestDate = None
            self.__init__() 
            await self.check()
        else:     
            self.task.cancel()
            self.task = asyncio.ensure_future(self.bdayTimer())

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
        await message.channel.send("Commands: \n>>> $pet \n$luck\n$poll\n$qp\n$uwu")
    
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
        except:
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
    
    
    
    elif message.content.lower().startswith("$bday"):
        try:
            date = datetime.strptime(message.content[5:].strip(), "%m/%d")
            date = date.replace(year=datetime.now().year)
            if date < datetime.now():
                date = date.replace(year=datetime.now().year + 1)
        except:
            await message.channel.send("Format should be: $bday mm/dd")
            return
        try: 
            existing = database.request(("SELECT * FROM birthdays WHERE userID = %s AND guild = %s LIMIT 1 ;",(message.author.id, message.guild.id)),"fetchone")
        except:
            existing = database.request(("SELECT * FROM birthdays WHERE userID = %s AND channel = %s LIMIT 1 ;", (message.author.id, message.channel.id)),"fetchone")
        if existing == None:
            try:
                new = (message.author.id, date, message.channel.id, message.guild.id)
                database.request(('INSERT INTO birthdays (userId,date,channel,guild) VALUES (%s, %s, %s, %s)', new),"change")
            except:
                new = (message.author.id, date, message.channel.id, None)
                database.request(('INSERT INTO birthdays (userId,date,channel, guild) VALUES (%s, %s, %s,%s)', new),"change")
        elif existing[1] == date and existing [2] == message.channel.id:
            await message.channel.send("This is matches your existing record")
            return
        else:
            try:
                new = (message.author.id, date, message.channel.id, message.guild.id)
                database.request(("UPDATE birthdays SET date = %s, channel = %s WHERE userId =%s AND guild = %s", (date, message.channel.id, message.author.id, message.guild.id)), "change")
            except:
                new = (message.author.id, date, message.channel.id, None)
                database.request(("UPDATE birthdays SET date = %s WHERE userId =%s AND channel = %s", (date, message.author.id, message.channel.id)), "change")
        database.connection.commit()
        #global birthday
        await birthday.update(new, existing)
        await message.channel.send("Saved")

'''
@client.event
async def on_reaction_update(reaction, user): #only works when message is in internal message cache i.e message sent when bot was online
    if user == client.user:
        await reaction.message.channel.send("haha i reacted")
    else:
        await reaction.message.channel.send("{.name} has reacted".format(user))
'''
client.run(os.environ["token"])
