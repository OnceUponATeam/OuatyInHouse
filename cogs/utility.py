
from disnake.ext.commands import Cog, slash_command, Param

from core.embeds import error, success
from dotenv import load_dotenv
import os

load_dotenv()

TOP_ROLE = os.getenv("TOP_ROLE")
JUNGLE_ROLE = os.getenv("JUNGLE_ROLE")
MID_ROLE = os.getenv("MID_ROLE")
ADC_ROLE = os.getenv("ADC_ROLE")
SUPPORT_ROLE = os.getenv("SUPPORT_ROLE")

class Utility(Cog):
    """
    🛠️;Utilitaire
    """
    def __init__(self, bot):
        self.bot = bot

    @slash_command()
    #async def ign(self, ctx, ign, role1 = Param(choices={"TOP": "top", "JUNGLE": "jungle", "MID": "mid", "ADC": "adc", "SUPPORT": "support"}), role2 = Param(choices={"TOP": "top", "JUNGLE": "jungle", "MID": "mid", "ADC": "adc", "SUPPORT": "support"}), game = Param(choices={"League Of Legends": "lol", "Valorant": "valorant", "Overwatch": "overwatch", "Other": "other"})):
    async def ign(self, ctx, ign, role1 = Param(choices={"TOP": TOP_ROLE, "JUNGLE": JUNGLE_ROLE, "MID": MID_ROLE, "ADC": ADC_ROLE, "SUPPORT": SUPPORT_ROLE}), role2 = Param(choices={"TOP": TOP_ROLE, "JUNGLE": JUNGLE_ROLE, "MID": MID_ROLE, "ADC": ADC_ROLE, "SUPPORT": SUPPORT_ROLE})):    
        """
        Indiquez votre nom en jeu.
        """
        guild = self.bot.get_guild(ctx.guild_id)
        game = "lol"
        user = ctx.author;
        data = await self.bot.fetchrow(f"SELECT * FROM igns WHERE game = '{game}' and user_id = {ctx.author.id} and guild_id = {ctx.guild.id}")
        if data:
            return await ctx.send(embed=error("Vous avez déjà enregistré votre nom en jeu une fois pour ce jeu. Veuillez contacter les administrateurs."))
                   
        await self.bot.execute(f"INSERT INTO igns(guild_id, user_id, game, ign, role1, role2) VALUES(?,?,?,?,?,?)", ctx.guild.id, ctx.author.id, game, ign, int(role1), int(role2))
        if role1 == role2:
            role = guild.get_role(int(role1))
            await user.add_roles(role, reason="Ajouté via /ign")
        elif role1 != role2:
            primary_role = guild.get_role(int(role1))
            print(primary_role)
            secondary_role = guild.get_role(int(role2))
            print(secondary_role)
            await user.add_roles(primary_role, secondary_role, reason="Ajouté via /ign")
        await ctx.send(embed=success("Votre nom en jeu a été enregistré correctement."), ephemeral=True)

def setup(bot):
    bot.add_cog(Utility(bot))