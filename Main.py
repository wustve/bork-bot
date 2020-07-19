import discord
from datetime import datetime
import asyncio
import os
client = discord.Client()
class bday():
    def __init__(self, closestDateLines = []):
        self.closestDateLines = closestDateLines
        self.currentDate = datetime.now()
        self.closestDate = None
        self.task = asyncio.ensure_future(self.bdayTimer())

    async def check(self):
        self.task.cancel()

        file = open("birthdays.txt","r")
        bdays = file.readlines()
        file.close()
        file = open("birthdays.txt","w")
        for i in bdays:
            line = i.split(" ")
            checkDate = datetime.strptime(line[1],"%Y-%m-%d")
            if line in self.closestDateLines:
                checkDate = checkDate.replace(year = checkDate.year + 1)
                newLine = line.copy()
                newLine[1] = str(checkDate.date())
                newLine = " ".join(newLine)
                bdays.append(newLine)
                self.closestDateLines.pop(self.closestDateLines.index(line))
                continue
            elif self.closestDate == None and checkDate > self.currentDate:
                self.closestDate = checkDate
                self.closestDateLines.append(line)
                file.write(i)
            elif checkDate < self.currentDate:
                #datetime.strptime(line[1],"%Y-%m-%d")
                checkDate = checkDate.replace(year = checkDate.year + 1)
                newLine = line.copy()
                newLine[1] = str(checkDate.date())
                newLine = " ".join(newLine)
                bdays.append(newLine)

                try:
                    await client.get_channel(int(line[2].strip("\n"))).send("While I was offline, we missed " +client.get_user(int(line[0])).mention + "'s bday on " + line[1] )
                except:
                    await client.get_user(int(line[0].strip("\n"))).send("While I was offline, we missed " +client.get_user(int(line[0])).mention + "'s bday on " + line[1] )
            elif checkDate < self.closestDate:
                self.closestDate = checkDate
                self.closestDateLines.clear()
                self.closestDateLines.append(line)
                file.write(i)
            elif checkDate == self.closestDate:
                self.closestDateLines.append(line)
                file.write(i)
            else: 
                file.write(i)
        file.close()
        self.task = asyncio.ensure_future(self.bdayTimer())

    async def bdayTimer(self): 
        if self.closestDate != None:
            await asyncio.sleep((self.closestDate - self.currentDate).total_seconds())
        
            for i in self.closestDateLines:

                try:
                    await client.get_channel(int(i[2].strip("\n"))).send("It's " +client.get_user(int(i[0])).mention + "'s bday!" )
                except:
                    await client.get_user(int(i[0].strip("\n"))).send("It's " +client.get_user(int(i[0])).mention + "'s bday!")

            self.__init__(self.closestDateLines) 
            await self.check()
    def update(self,line,date, oldLine):

        if self.closestDate == None:
            return
        else:
            if date == self.closestDate:
                self.closestDateLines.append(line)
            elif date < self.closestDate:
                self.closestDate = date
                self.closestDateLines.clear()
                self.closestDateLines.append(line)
            if oldLine == "":
                return
            else:
                try:
                    self.closestDateLines.remove(oldLine)
                except:
                    pass
                if len(self.closestDateLines) == 0:
                    self.closestDate = None
        self.task.cancel()
        self.task = asyncio.ensure_future(self.bdayTimer())

global birthday
async def createBday(): #Can't call async functions from constructor, so I have to do this
    global birthday
    birthday = bday()
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

        file = open("birthdays.txt","r")
        existing  = file.readlines()
        file.close()
        oldLine = ""
        file = open("birthdays.txt","w")
        for i in existing:
            bday = i.split(" ")
            try:
                if bday[0] == str(message.author.id) and bday[3].strip("\n") == str(message.guild.id):
                    if bday[1] ==str(date.date()):
                        await message.channel.send("This is matches your existing birthday")
                        file.write(i)
                        oldLine = " "
                        continue
                    else:
                        oldLine = i
                        continue
                else:
                    file.write(i)
            except:
                if bday[0] == str(message.author.id) and len(bday) < 4 and bday[2].strip("\n") ==str(message.channel.id):
                    if bday[1] ==str(date.date()):
                        await message.channel.send("This is matches your existing birthday")
                        oldLine = " "
                        file.write(i)
                        continue
                    else:
                        oldLine = i
                        continue
                else:
                    file.write(i)
        file.close()
        if oldLine == " ":
            return
        file = open("birthdays.txt","a")
        try:
            line = str(message.author.id) + ' ' + str(date.date()) + ' ' + str(message.channel.id) + ' ' + str(message.guild.id) + '\n'
        except:
            line = str(message.author.id) + ' ' + str(date.date()) + ' ' + str(message.channel.id) +'\n'
        file.write(line)
        file.close()
        global birthday
        birthday.update(line,date, oldLine)
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
