from disnake import Color, Embed
from disnake.ext.commands import Cog, slash_command

from core.match import start_queue
from core.embeds import error

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

    @Cog.listener()
    async def on_ready(self):
        await self.send_new_queues()

    @slash_command(name="start")
    async def start_slash(self, ctx):
        """
        Démarrer une nouvelle file.
        """
        game_check = await self.bot.fetchrow(f"SELECT * FROM queuechannels WHERE channel_id = {ctx.channel.id}")
        if not game_check:
            return await ctx.send(embed=error("Ce salon n'est pas un salon permettant de créer une file."))
        try:
            await ctx.send("La game a commencée!")
        except:
            pass
        await start_queue(self.bot, ctx.channel, game_check[2], ctx.author)

def setup(bot):
    bot.add_cog(Match(bot))
