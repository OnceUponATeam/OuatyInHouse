from core import embeds, buttons, selectmenus
from disnake import TextChannel, Embed, Color, OptionChoice, SelectOption
from disnake.ext.commands import Cog, command, slash_command, Param


class ChannelCommands(Cog):
    """
    ⚙️;Channel Setup
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_slash_command_check(self, inter):
        # checks that apply to every command in here

        if inter.author.guild_permissions.administrator:
            return True

        await inter.send(
            embed=embeds.error(
                "Vous avez besoin d'avoir les permissions d'**administrateur** pour faire appel à cette commande."
            )
        )
        return False

    async def cog_check(self, ctx):
        # checks that apply to every command in here

        if ctx.author.guild_permissions.administrator:
            return True

        await ctx.send(
            embed=embeds.error(
                "Vous avez besoin d'avoir les permissions d'**administrateur** pour faire appel à cette commande."
            )
        )
        return False

    @command(aliases=["channel"])
    async def setchannel(self, ctx, channel: TextChannel, game):
        if game.lower() not in ['lol', 'valorant', 'overwatch', 'other']:
            return await ctx.send(embed=embeds.error("Le jeu doit être un des trois suivants: `valorant/lol/overwatch/other`."))

        data = await self.bot.fetchrow(
            f"SELECT * FROM queuechannels WHERE channel_id = {channel.id}"
        )
        if data:
            return await ctx.edit_original_message(
                embed=embeds.error(
                    f"{channel.mention} est déjà configuré comme le salon de file."
                )
            )

        if game == 'lol':
            regions =  ["BR", "EUNE", "EUW", "LA", "LAS", "NA", "OCE", "RU", "TR", "JP"]
        elif game == 'valorant':
            regions = ["EU", "NA", "BR", "KR", "AP", "LATAM"]
        elif game == "overwatch":
            regions = ["AMERICAS", "ASIAS", "EUROPE"]
        else:
            regions = []

        if regions:
            options = []
            for region in regions:
                options.append(SelectOption(label=region, value=region.lower()))
            async def Function(inter, vals, *args):
                view = buttons.ConfirmationButtons(inter.author.id)
                await inter.edit_original_message(
                    embed=Embed(title=":warning: Notice", description=f"Les messages dans le salon {channel.mention} seront supprimé automatiquement pour garder le salon propre, est-ce que vous voulez procéder?", color=Color.yellow()),
                    view=view,
                    content=""
                )
                await view.wait()
                if view.value is None:
                    return
                elif view.value:
                    pass
                else:
                    return await inter.edit_original_message(embed=embeds.success("Process aborted."))

                await self.bot.execute(
                    "INSERT INTO queuechannels(channel_id, region, game) VALUES($1, $2, $3)", channel.id, vals[0], game
                )

                await inter.edit_original_message(
                    embed=embeds.success(
                        f"{channel.mention} a été défini avec succès comme salon de file."
                    )
                )

            await ctx.send(content="Sélectionner une région pour la file.", view=selectmenus.SelectMenuDeploy(self.bot, ctx.author.id, options, 1, 1, Function))
        else:
            
            await self.bot.execute(
                "INSERT INTO queuechannels(channel_id, region, game) VALUES($1, $2, $3)", channel.id, "none", game
            )
            await ctx.send(embed=embeds.success(f"{channel.mention} a été défini avec succès comme salon de file."))

    @slash_command(name="setchannel")
    async def setchannel_slash(self, ctx, channel: TextChannel, game = Param(choices={"League Of Legends": "lol", "Valorant": "valorant", "Overwatch": "overwatch", "Other": "other"})):
        """
        Sélectionner un salon pour être utilisé comme la file d'attente.
        """
        await self.setchannel(ctx, channel, game)

    @command()
    async def setregion(self, ctx, queue_channel: TextChannel, region):
        if region.upper() not in [ "BR", "EUNE", "EUW", "LA", "LAS", "NA", "OCE", "RU", "TR", "JP"]:
            return await ctx.send(embed=embeds.error("S'il vous plait choisissez une région valide."))

        data = await self.bot.fetchrow(f"SELECT * FROM queuechannels WHERE channel_id = {queue_channel.id} and game = 'lol'")
        if not data:
            return await ctx.send(embed=embeds.error(f"{queue_channel.mention} n'est pas un salon de file pour League of Legends."))
        
        await self.bot.execute(f"UPDATE queuechannels SET region = ? WHERE channel_id = {queue_channel.id}", region)
        await ctx.send(embed=embeds.success("La réfion pour le salon de file a été modifié correctement."))

    @slash_command(name="setregion")
    async def setregion_slash(self, ctx, queue_channel: TextChannel, region= Param(choices=[
        OptionChoice("EUW", "euw"),
        OptionChoice("NA", 'na'),
        OptionChoice("BR", 'br'),
        OptionChoice("EUNE", 'eune'),
        OptionChoice("LA", 'la'),
        OptionChoice("LAS", 'las'),
        OptionChoice("OCE", 'oce'),
        OptionChoice("RU", 'ru'),
        OptionChoice("TR", 'tr'),
        OptionChoice("JP", 'jp')]),
        ):
            """
            Modifier la région pour le salon de file de League Of Legends.
            """
            await self.setregion(ctx, queue_channel, region)
            
    @command()
    async def setwinnerlog(self, ctx, channel: TextChannel, game):
        if game not in ['lol', 'valorant', 'overwatch', 'other']:
            return await ctx.send(embed=embeds.error("S'il vous plait choisissez une jeu valide. Le jeu peut être `lol/valorant/overwatch/other`."))
        data = await self.bot.fetchrow(
            f"SELECT * FROM winner_log_channel WHERE channel_id = {channel.id} and game = '{game}'"
        )
        if data:
            if data[0] == channel.id:
                return await ctx.send(
                    embed=embeds.error(
                        f"{channel.mention} est déjà le salon d'historique de match pour ce jeu."
                    )
                )

        else:
            await self.bot.execute(
                "INSERT INTO winner_log_channel(guild_id, channel_id, game) VALUES($1, $2, $3)",
                ctx.guild.id,
                channel.id,
                game
            )

        await ctx.send(
            embed=embeds.success(
                f"{channel.mention} a été défini avec succès en tant que salon de l'historique de match."
            )
        )

    @slash_command(name="setwinnerlog")
    async def setwinnerlog_slash(self, ctx, channel: TextChannel, game=Param(choices={"League Of Legends": "lol", "Valorant": "valorant", "Overwatch": "overwatch", "Other": "other"})):
        """
        Sélectionner un salon pour envoyer les résultats de game.
        """
        await self.setwinnerlog(ctx, channel, game)


def setup(bot):
    bot.add_cog(ChannelCommands(bot))
