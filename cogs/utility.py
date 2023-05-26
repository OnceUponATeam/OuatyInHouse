
from disnake.ext.commands import Cog, slash_command, Param

from core.embeds import error, success

class Utility(Cog):
    """
    🛠️;Utilitaire
    """
    def __init__(self, bot):
        self.bot = bot

    @slash_command()
    async def ign(self, ctx, ign, game = Param(choices={"League Of Legends": "lol", "Valorant": "valorant", "Overwatch": "overwatch", "Other": "other"})):
        """
        Indiquez votre nom en jeu.
        """
        data = await self.bot.fetchrow(f"SELECT * FROM igns WHERE game = '{game}' and user_id = {ctx.author.id} and guild_id = {ctx.guild.id}")
        if data:
            return await ctx.send(embed=error("Vous avez déjà enregistré votre nom en jeu une fois pour ce jeu. Veuillez contacter les administrateurs."))
                   
        await self.bot.execute(f"INSERT INTO igns(guild_id, user_id, game, ign) VALUES(?,?,?,?)", ctx.guild.id, ctx.author.id, game, ign)
        await ctx.send(embed=success("Votre nom en jeu a été enregistré correctement."))

def setup(bot):
    bot.add_cog(Utility(bot))