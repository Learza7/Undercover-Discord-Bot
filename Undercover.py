import discord
from discord.ext import commands
from discord.utils import get
import random
import asyncio
import Variables


bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await bot.change_presence(activity=discord.Game(name='Undercover'))

@bot.event
async def on_message(message):
    if str(message.content[:1]) == "!" and message.channel.type != "private" :
        await message.delete()
    await bot.process_commands(message)


@bot.event
async def on_message_edit(before,after):
    await bot.process_commands(after)
    #await after.delete()



@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user :
        return 0

    if reaction.emoji in Variables.alphabet:
        player = idToPlayer(user)
        player.setVote(Partie.players[Variables.alphabet.index(reaction.emoji)])

    
    if reaction.emoji == Variables.emoji[0]:
        Partie.addPlayer(user)
        await Partie.updateInit()

    if reaction.emoji == Variables.emoji[1] and user.name == "Rémi" :
        await run(reaction)




@bot.command()
async def new(ctx):

    global Partie

    Partie = Game(ctx.channel)
    print(Partie)
    await Partie.updateInit()

    await Partie.init.add_reaction(Variables.emoji[0])
    await Partie.init.add_reaction(Variables.emoji[1])


@bot.command()
async def vote(ctx):

    message = await Partie.channel.send(embed = embedVote(Partie.players))

    for i in range(Partie.NBPlayers):
        await message.add_reaction(Variables.alphabet[i])

    tlm_a_vote = False
    while not tlm_a_vote:
        await asyncio.sleep(1)
        message = await Partie.channel.fetch_message(message.id)
        NBreactions = 0
        for react in message.reactions:
            NBreactions += react.count
        if NBreactions>= 2*Partie.NBPlayers:
            tlm_a_vote = True
    await asyncio.sleep(3)

    soloVote = soloVoteIntrus(Partie.players)
    intrus_trouve = False
    for play in Partie.players:
        if play.isUndercover:
            intrus = play
        else:
            normal = play
        if play.vote.isUndercover:
            intrus_trouve = True
            if soloVote:
                play.addPoints(150)
            else:
                play.addPoints(100)

    if not intrus_trouve:
        intrus.addPoints(200)


    await Partie.channel.send(embed = embedFinVote(intrus, normal))
    




def soloVoteIntrus(players):
    deja_vote = False
    for play in players:
        if play.vote.isUndercover:
            if deja_vote:
                return False
            else:
                deja_vote = True
    return True








@bot.command()
async def run(ctx):

    Partie.rollOrder()

    duo = random.choice(Variables.Mots)

    L = Tirage(Partie.NBPlayers, duo)
    print(Partie.players)
    for k in range(Partie.NBPlayers):
        Partie.players[k].setMot(L[k][0])
        await Partie.players[k].sendText("Ton mot est: "+Partie.players[k].mot)
        Partie.players[k].initProps()
        Partie.players[k].setUnder(L[k][1])


    Partie.addMsg(await Partie.channel.send(embed = embedPlayers(Partie.players)))

@bot.command()
async def a(ctx, *, mot):

    play = idToPlayer(ctx.author)
    play.addProps(mot)

    await updateMSG(ctx)





@bot.command()
async def updateMSG(ctx):

    await Partie.msg.edit(embed = embedPlayers(Partie.players))





def Tirage(nbplayers,L):

    intrus = L.pop(random.randint(0,len(L)-1))
    mot = L[random.randint(0,len(L)-1)]

    Liste = [[mot,False]]*(nbplayers-1)
    Liste.insert(random.randint(0,nbplayers-1),[intrus, True])

    return Liste



    
@bot.command()
async def role(ctx):
	role = discord.utils.get(ctx.guild.roles, name="PSI")

	await role.edit(name="Salut")




class Game:
    def __init__(self, channel):

        

        self.players = []
        self.channel = channel

        self.msg = "undefined"
        self.init = ""

    def addMsg(self, msg):
        self.msg = msg

    def rollOrder(self):
        self.players.append(self.players.pop(0))

    def addPlayer(self, play):
        self.players.append(Joueur(play, self))
        self.NBPlayers = len(self.players)

    async def updateInit(self):
        if self.init == "":
            self.init = await Partie.channel.send(embed = embedStart(self.players))
        else:
            await self.init.edit(embed = embedStart(self.players))





class Joueur:
    def __init__(self, play, game):

        self.points = 0
        self.id = play
        self.mot = ""
        self.props = ""
        self.isUndercover = False
        self.vote = "undefined"


    async def sendText(self, text):
        await self.id.send(embed = simpleEmbed(text))

    def initProps(self):
        self.props = ""

    def setUnder(self, Boule):
        if Boule:
            self.isUndercover = True
        else:
            self.isUndercover = False

    def addProps(self, mot):
        self.props += " {},".format(mot)

    def setMot(self, mot):
        self.mot = mot

    def setVote(self, play):
        self.vote = play

    def addPoints(self, points):
        self.points += points



def embedVote(players):
    embed = discord.Embed(
        title = "Undercover",
        colour = discord.Colour.blue(),
        description = "")

    votestring = ""
    i=0
    for play in players:

        votestring += "{} .  {}\n".format(Variables.alphabet[i], play.id.display_name)
        i+=1
    embed.add_field(name="Votez pour la lettre correspondante", value=votestring, inline=False)
    return embed


def simpleEmbed(text):
    embed = discord.Embed(
        title = "",
        colour = discord.Colour.blue(),
        description=text)
    return embed

def embedStart(players):
    embed = discord.Embed(
        title = "Undercover",
        colour = discord.Colour.blue(),
        description = "Une nouvelle partie va commencer...")

    string = " ".join([play.id.display_name for play in players])
    if string == "":
        string="..."
    embed.add_field(name = "Liste des Joueurs",
                    value = string,
                    inline = False)
    embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/701767069191897149/706979358614487304/danny.png")
    return embed

def embedPlayers(players):
    embed = discord.Embed(
        title = "Undercover",
        colour = discord.Colour.blue(),
        description = "")

    for play in players:
        embed.add_field(
            name = "{} ({} points)".format(play.id.display_name,str(play.points)),
            value = "-"+str(play.props),
            inline = False
            )
    return embed 

def embedFinVote(intrus, normal):
    embed = discord.Embed(
        title = "Undercover",
        colour = discord.Colour.blue(),
        description = "")
    embed.add_field(name = "...", value = "{} était l'**intrus**".format(intrus.id.display_name), inline = False)
    embed.add_field(name = "Mot de l'intrus", value = "{}".format(intrus.mot), inline = False)
    embed.add_field(name = "Mot des autres", value = "{}".format(normal.mot), inline = False)
    embed.set_thumbnail(url = "https://cdn.discordapp.com/attachments/701767069191897149/706979358614487304/danny.png")
    
    return embed

def idToPlayer(user):
    for play in Partie.players:
        if play.id == user:
            return play


   
#bot.run(TOKEN)


    



