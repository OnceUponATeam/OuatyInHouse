
from disnake.ext.commands import Cog, slash_command, Param

from core.embeds import error, success
from dotenv import load_dotenv
import os

load_dotenv()

TOP_MAIN_ROLE = os.getenv("TOP_MAIN_ROLE")
JUNGLE_MAIN_ROLE = os.getenv("JUNGLE_MAIN_ROLE")
MID_MAIN_ROLE = os.getenv("MID_MAIN_ROLE")
ADC_MAIN_ROLE = os.getenv("ADC_MAIN_ROLE")
SUPPORT_MAIN_ROLE = os.getenv("SUPPORT_MAIN_ROLE")
TOP_SECOND_ROLE = os.getenv("TOP_SECOND_ROLE")
JUNGLE_SECOND_ROLE = os.getenv("JUNGLE_SECOND_ROLE")
MID_SECOND_ROLE = os.getenv("MID_SECOND_ROLE")
ADC_SECOND_ROLE = os.getenv("ADC_SECOND_ROLE")
SUPPORT_SECOND_ROLE = os.getenv("SUPPORT_SECOND_ROLE")

class Utility(Cog):
    """
    🛠️;Utilitaire
    """
    def __init__(self, bot):
        self.bot = bot

    @slash_command()
    #async def ign(self, ctx, ign, role1 = Param(choices={"TOP": "top", "JUNGLE": "jungle", "MID": "mid", "ADC": "adc", "SUPPORT": "support"}), role2 = Param(choices={"TOP": "top", "JUNGLE": "jungle", "MID": "mid", "ADC": "adc", "SUPPORT": "support"}), game = Param(choices={"League Of Legends": "lol", "Valorant": "valorant", "Overwatch": "overwatch", "Other": "other"})):
    async def ign(self, ctx, ign, main_role = Param(choices={"TOP": TOP_MAIN_ROLE, "JUNGLE": JUNGLE_MAIN_ROLE, "MID": MID_MAIN_ROLE, "ADC": ADC_MAIN_ROLE, "SUPPORT": SUPPORT_MAIN_ROLE}), second_role = Param(choices={"TOP": TOP_SECOND_ROLE, "JUNGLE": JUNGLE_SECOND_ROLE, "MID": MID_SECOND_ROLE, "ADC": ADC_SECOND_ROLE, "SUPPORT": SUPPORT_SECOND_ROLE})):    
        """
        Indiquez votre nom en jeu.
        """
        guild = self.bot.get_guild(ctx.guild_id)
        game = "lol"
        user = ctx.author;
        data = await self.bot.fetchrow(f"SELECT * FROM igns WHERE game = '{game}' and user_id = {ctx.author.id} and guild_id = {ctx.guild.id}")
        if data:
            return await ctx.send(embed=error("Vous avez déjà enregistré votre nom en jeu une fois pour ce jeu. Veuillez contacter les administrateurs."))
                   
        await self.bot.execute(f"INSERT INTO igns(guild_id, user_id, game, ign, main_role, second_role) VALUES(?,?,?,?,?,?)", ctx.guild.id, ctx.author.id, game, ign, int(main_role), int(second_role))
        if main_role == second_role:
            role = guild.get_role(int(main_role))
            await user.add_roles(role, reason="Ajouté via /ign")
        elif main_role != second_role:
            primary_role = guild.get_role(int(main_role))
            print(primary_role)
            secondary_role = guild.get_role(int(second_role))
            print(secondary_role)
            await user.add_roles(primary_role, secondary_role, reason="Ajouté via /ign")
        await ctx.send(embed=success("Votre nom en jeu a été enregistré correctement."), ephemeral=True)

def setup(bot):
    bot.add_cog(Utility(bot))