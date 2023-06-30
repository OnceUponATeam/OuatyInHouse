import asyncio
import datetime
import pytz
from disnake import Color, Embed
from disnake.ext.commands import Cog, slash_command

from core.match import start_queue, activateQueue, deactivateQueue, getQueueStatus
from core.embeds import error

startingChannel = 1120153576447148092
justStarted = False #Permet de savoir si c'est un restart du bot ou simplement un nouveau cycle.

class Match(Cog):
    """
    ⚔️;Matchmaking
    """

    def __init__(self, bot):
        self.bot = bot

    async def send_new_queues(self):
        await self.bot.wait_until_ready()
        channels = await self.bot.fetch("SELECT * FROM queuechannels")
        for data in channels:
            channel = self.bot.get_channel(data[0])
            if channel:
                try:
                    await channel.send(
                        embed=Embed(
                            title=":warning: ATTENTION",
                            description="Le bot a été mis à jour pour maintenance. Les files **avant** ce message sont maintenant invalides. Veuillez utiliser la file située en dessous de ce message.",
                            color=Color.yellow()
                        )
                    )
                    await start_queue(self.bot, channel, data[2])
                except:
                    import traceback
                    print(traceback.format_exc())

    async def check_planning(self):
        channel = self.bot.get_channel(startingChannel)

        now = datetime.datetime.now(pytz.timezone("Europe/Brussels"))

        dayOfQueue = now.isoweekday()
        check = True
        dayBeforeQueue = 0
        while check:
            starting_day = await self.bot.fetch(f"SELECT * FROM schedule WHERE day = {dayOfQueue}")
            starting_day = starting_day[0]
            if starting_day[1] == 0:
                dayBeforeQueue += 1
                dayOfQueue += 1
                if dayOfQueue > 7:
                    dayOfQueue -= 7
            else:
                fakeEndingTime = starting_day[2]
                if starting_day[2] < starting_day[1]:
                    fakeEndingTime = 24 + starting_day[2]
                if (fakeEndingTime <= now.hour and dayBeforeQueue == 0):
                    dayBeforeQueue += 1
                    dayOfQueue += 1
                    if dayOfQueue > 7:
                        dayOfQueue -= 7
                else: 
                    check = False
            """
            if starting_day[1] == 0 or (starting_day[2] <= now.hour and dayBeforeQueue == 0):
                dayBeforeQueue += 1
                dayOfQueue += 1
                if dayOfQueue > 7:
                    dayOfQueue -= 7
            else:
                check = False
            """
        
        starting_time = now.replace(hour=starting_day[1], minute=0,second=0,microsecond=0)
        starting_time += datetime.timedelta(days=dayBeforeQueue)
        if starting_day[2] < starting_day[1]:
            ending_time = now.replace(hour=starting_day[2], minute=0,second=0,microsecond=0)
            ending_time += datetime.timedelta(days=dayBeforeQueue +1)
        else:
            ending_time = now.replace(hour=starting_day[2], minute=0,second=0,microsecond=0)
            ending_time += datetime.timedelta(days=dayBeforeQueue)

        QueueStatus = await getQueueStatus()
        if now < starting_time:
            timeLeft = starting_time - now
            channel = self.bot.get_channel(startingChannel)
            await channel.send(f"Les prochaines parties de OUAT ARENA pourront se faire le <t:{round(starting_time.timestamp())}:D> à <t:{round(starting_time.timestamp())}:t>")
            
            await asyncio.sleep(timeLeft.total_seconds())
            await self.start_ouat_arena(round(ending_time.timestamp()))
        elif now > starting_time and now < ending_time:
            if justStarted or not QueueStatus:
                await self.start_ouat_arena(round(ending_time.timestamp()))
            timeLeft = ending_time - now
            await asyncio.sleep(timeLeft.total_seconds())
            await self.end_ouat_arena()

    async def start_ouat_arena(self, stopTime):
        await activateQueue()
        #Supprime tous les joueurs actuellement en file (Permet de s'assurer que personne ne soit bloqué dans une précédente file)
        await self.bot.execute(
            f"DELETE FROM game_member_data"
        )#Supprime tous les duos actuellement en file
        await self.bot.execute(
            f"DELETE FROM duo_queue "
        )
        await self.send_new_queues()
        channel = self.bot.get_channel(startingChannel)
        await channel.send(f"# Lancement de la OUAT ARENA !\n**La OUAT ARENA est relancée !**\nPour jouer, cliquez ici : <#1109249201268858953> et choisissez votre rôle !\nLa file sera active jusqu'au <t:{stopTime}:D> à <t:{stopTime}:t>\n||@everyone||")
        global justStarted
        justStarted = False
        await self.check_planning()
            
    async def end_ouat_arena(self):
        await deactivateQueue()
        channels = await self.bot.fetch("SELECT * FROM queuechannels")
        for data in channels:
            channel = self.bot.get_channel(data[0])
            if channel:
                try:
                    await channel.send(
                        embed=Embed(
                            title=":warning: INFORMATION",
                            description=f"Fin de OUAT ARENA pour aujourd'hui ! Vous pouvez vous diriger vers le salon <#{startingChannel}> pour savoir quand reprendra la OUAT ARENA\n\nVous voyez peut être encore votre nom dans le lobby mais ne vous en faites pas, vous avez bien été retiré de la file.",
                            color=Color.yellow()
                        )
                    )
                except:
                    import traceback
                    print(traceback.format_exc())
        
        await self.check_planning()

    @Cog.listener()
    async def on_ready(self):
        global justStarted 
        justStarted = True
        await self.check_planning()
        #await self.send_new_queues()

    @slash_command(name="start")
    async def start_slash(self, ctx):
        """
        Démarrer une nouvelle file.
        """
        game_check = await self.bot.fetchrow(f"SELECT * FROM queuechannels WHERE channel_id = {ctx.channel.id}")
        if not game_check:
            return await ctx.send(embed=error("Ce salon n'est pas un salon permettant de créer une file."))
        try:
            await ctx.send("La partie a commencée!")
        except:
            pass
        await start_queue(self.bot, ctx.channel, game_check[2], ctx.author)

def setup(bot):
    bot.add_cog(Match(bot))
