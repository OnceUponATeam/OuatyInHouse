import asyncio
import itertools
import json
import random
import re
import traceback
import uuid
from datetime import datetime, timedelta

import async_timeout
import websockets
from disnake import (ButtonStyle, Color, Embed, PermissionOverwrite,
                     SelectOption, ui)
from disnake.ext import tasks
from trueskill import Rating, quality

from core.buttons import ConfirmationButtons
from core.embeds import error, success
from core.selectmenus import SelectMenuDeploy

LOL_LABELS = ["Top", "Jungle", "Mid", "ADC", "Support"]
VALORANT_LABELS = ["Controller", "Initiator", "Sentinel", "Duelist", "Flex"]
OVERWATCH_LABELS = ["Tank", "DPS 1", "DPS 2", "Support 1", "Support 2"]
OTHER_LABELS = ["Role 1", "Role 2", "Role 3", "Role 4", "Role 5"]

async def start_queue(bot, channel, game, author=None, existing_msg = None, game_id = None):
    def region_icon(region, game):
        if game == "lol":
            if region == "euw":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444853028175934/OW_Europe.png"
            elif region == "eune":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444853028175934/OW_Europe.png"
            elif region == "br":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444852579373136/OW_Americas.png"
            elif region == "la":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444852579373136/OW_Americas.png"
            elif region == "jp":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444853233684581/VAL_AP.png"
            elif region == "las":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444852579373136/OW_Americas.png"
            elif region == "tr":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444853233684581/VAL_AP.png"
            elif region == "oce":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444853233684581/VAL_AP.png"
            elif region == "ru":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444853233684581/VAL_AP.png"
            else:
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444852369670214/VAL_NA.png"

        elif game == "valorant":
            if region == "ap":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1077957848161591387/VAL_AP.png"
            elif region == "br":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1077957848409067661/VAL_BR.png"
            elif region == "kr":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1077957848660713494/VAL_KR.png"
            elif region == "latam":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1077957848899801129/VAL_LATAM.png"
            elif region == "na":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1077957849130467408/VAL_NA.png"
            else:
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1075444853028175934/OW_Europe.png"

        elif game == "overwatch":
            if region == "americas":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1077957898329673728/OW_Americas.png"
            elif region == "asia":
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1077957898598101022/OW_Asia.png?width=572&height=572"
            else:
                icon_url = "https://media.discordapp.net/attachments/1046664511324692520/1077957898963013814/OW_Europe.png"

        else:
            icon_url = ""
        return icon_url

    def banner_icon(game):
        if game == "lol":
            return "https://cdn.discordapp.com/attachments/880913866719117412/1111770498049777705/banner.png"
        elif game == "valorant":
            return "https://media.discordapp.net/attachments/1046664511324692520/1077958380964036689/image.png"
        elif game == "overwatch":
            return "https://media.discordapp.net/attachments/1046664511324692520/1077958380636868638/image.png"
        else:
            return "https://media.discordapp.net/attachments/328696263568654337/1067908043624423497/image.png?width=1386&height=527"

    def get_title(game):
        if game == "lol":
            return "Aperçu des matchs - Faille de l'invocateur Draft de tournoi"
        elif game == "valorant":
            return "Match Overview - Valorant Competitive"
        elif game == "overwatch":
            return "Match Overview - Overwatch Competitive"
        else:
            return "Match Overview"

    data = await bot.fetchrow(
        f"SELECT * FROM queuechannels WHERE channel_id = {channel.id}"
    )
    if not data:
        try:
            return await channel.send(
                embed=error(
                    f"{channel.mention} n'est pas un salon de file, s'il vous plait faites cette commande dans un salon de file."
                )
            )
        except:
            if author:
                return await author.send(embed=error(f"Impossible de lancer de file dans {channel.mention}, merci de vérifer mes permissions."))

    # If you change this - update /events.py L28 as well!
    
    testmode = await bot.check_testmode(channel.guild.id)
    if testmode:
        title = "1v1 Test Mode"
    else:
        title = get_title(game)
        
    embed = Embed(
        title=title, color=Color.red()
    )
    st_pref = await bot.fetchrow(f"SELECT * FROM switch_team_preference WHERE guild_id = {channel.guild.id}")
    
    if not st_pref:
        if existing_msg:
            game_members = await bot.fetch(f"SELECT * FROM game_member_data WHERE game_id = '{game_id}'")
            slot1 = ""
            slot2 = ""
            for i, member in enumerate(game_members):
                if i in [x for x in range(0, 5)]:
                    slot1 += f"<@{member[0]}> - `{member[1].capitalize()}`\n"
                else:
                    slot2 += f"<@{member[0]}> - `{member[1].capitalize()}`\n"
        else:
            slot1 = "Pas encore de joueur"
            slot2 = "Pas encore de joueur"
        embed.add_field(name="Groupe 1", value=slot1)
        embed.add_field(name="Groupe 2", value=slot2)
        sbmm = True
    else:
        if existing_msg:
            game_members = await bot.fetch(f"SELECT * FROM game_member_data WHERE game_id = '{game_id}'")
            blue_value = ""
            red_value = ""
            for member in game_members:
                if member[2] == "blue":
                    blue_value += f"<@{member[0]}> - `{member[1].capitalize()}`\n"
                else:
                    red_value += f"<@{member[0]}> - `{member[1].capitalize()}`\n"
        else:
            blue_value = "Pas encore de joueur"
            red_value = "Pas encore de joueur"
        embed.add_field(name="🔵 Blue", value=blue_value)
        embed.add_field(name="🔴 Red", value=red_value)
        sbmm = False
    if channel.guild.id == 1071099639333404762:
        embed.set_image(url="https://media.discordapp.net/attachments/1071237723857363015/1073428745253290014/esporty_banner.png")
    else:
        banner = banner_icon(game)
        if banner:
            embed.set_image(url=banner)
    with open('assets/tips.txt', 'r') as f:
        tips = f.readlines()
        tip = random.choice(tips)
    if existing_msg:
        footer_game_id = game_id
    else:
        footer_game_id = str(uuid.uuid4()).split("-")[0]
    
    embed.set_footer(text="🎮 " + footer_game_id + '\n' + "💡 " + tip)
    if not data[1]:
        data = (data[0], 'na')
    icon_url = region_icon(data[1], game)
    if icon_url:
        embed.set_author(name=f"File {data[1].upper()}", icon_url=icon_url)
    
    duo_pref = await bot.fetchrow(f"SELECT * FROM duo_queue_preference WHERE guild_id = {channel.guild.id}")
    if duo_pref:
        duo = True
    else:
        duo = False
    
    try:
        if existing_msg:
            await existing_msg.edit(embed=embed, view=Queue(bot, sbmm, duo, game, testmode), content="")
        else:
            await channel.send(embed=embed, view=Queue(bot, sbmm, duo, game, testmode))
    except:
        if author:
            await author.send(embed=error(f"Impossible de lancer de file dans {channel.mention}, merci de vérifer mes permissions."))

class SpectateButton(ui.View):
    def __init__(self, bot, game_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.game_id = game_id

    async def process_button(self, button, inter):
        await inter.response.defer()

        if "Rouge" in button.label:
            team = "Red"
        else:
            team = "Blue"

        
        data = await self.bot.fetchrow(
            f"SELECT * FROM games WHERE game_id = '{self.game_id}'"
        )

        if not data:
            return await inter.send(embed=error("Cette partie est terminée."), ephemeral=True)

        members_data = await self.bot.fetch(
            f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}'"
        )
        for member in members_data:
            if member[0] == inter.author.id:
                return await inter.send(
                    embed=error("Vous ne pouvez pas être spectateur car vous jouez cette partie."),
                    ephemeral=True,
                )

        await inter.send(
            embed=success(f"Vous êtes maintenant spectateur de l'équipe {team} !"), ephemeral=True
        )

        lobby = self.bot.get_channel(data[1])

        if team == "Red":
            voice = self.bot.get_channel(data[2])
        else:
            voice = self.bot.get_channel(data[3])

        lobby_overwrites = lobby.overwrites
        lobby_overwrites.update(
            {
                inter.author: PermissionOverwrite(send_messages=True),
            }
        )

        voice_overwrites = voice.overwrites
        voice_overwrites.update(
            {
                inter.author: PermissionOverwrite(
                    send_messages=True, connect=True, speak=False
                ),
            }
        )

        await lobby.edit(overwrites=lobby_overwrites)
        await voice.edit(overwrites=voice_overwrites)

    @ui.button(label="Observer l'équipe Rouge", style=ButtonStyle.red, custom_id="lol-specred")
    async def spec_red(self, button, inter):
        await self.process_button(button, inter)

    @ui.button(label="Observer l'équipe Bleu", style=ButtonStyle.blurple, custom_id="lol-specblue")
    async def spec_blue(self, button, inter):
        await self.process_button(button, inter)

class RoleButtons(ui.Button):
    def __init__(self, bot, label, custom_id, disabled=False):
        super().__init__(
            label=label, style=ButtonStyle.green, custom_id=custom_id, disabled=disabled
        )
        self.bot = bot
        self.cooldown = None
    
    async def in_ongoing_game(self, inter) -> bool:
        data = await self.bot.fetch(f"SELECT * FROM games")
        for entry in data:
            user_roles = [x.id for x in inter.author.roles]
            if entry[4] in user_roles or entry[5] in user_roles:
                return True

        return False

    async def overwatch_team(self, label, view):
        team = "blue"

        def disable():
            view.disabled.append(label)
            
        if label == "tank":
            data = await self.bot.fetchrow(
                f"SELECT * FROM game_member_data WHERE role = '{label}' and game_id = '{view.game_id}'"
            )
            if data:
                if data[2] == "blue":
                    team = "red"
                disable()
        else:
            data = await self.bot.fetch(
                f"SELECT * FROM game_member_data WHERE role = '{label}' and game_id = '{view.game_id}'"
            )
            if len(data) > 2:
                if data[2] == "blue":
                    team = "red"
                if len(data)+1 == 4:
                    disable()
        
        return team

    async def add_participant(self, inter, button, view) -> None:
        data = await self.bot.fetchrow(f"SELECT * FROM igns WHERE game = 'lol' and user_id = {inter.author.id} and guild_id = {inter.guild.id}")
        if data:
            preference = await self.bot.fetchrow(f"SELECT * FROM queue_preference WHERE guild_id = {inter.guild.id}")
            if preference:
                preference = preference[1]
            else:
                preference = 1
            
            if preference == 2:
                in_other_games = await self.bot.fetch(
                    f"SELECT * FROM game_member_data WHERE author_id = {inter.author.id} and game_id != '{view.game_id}'"
                )
                if in_other_games:
                    return await inter.send(
                        embed=error(f"Vous ne pouvez pas faire partie de plusieurs files."),
                        ephemeral=True,
                    )

            label = button.label.lower()
            team = "blue"

            data = await self.bot.fetchrow(
                f"SELECT * FROM game_member_data WHERE role = '{label}' and game_id = '{view.game_id}'"
            )
            if data:
                if data[2] == "blue":
                    team = "red"
                view.disabled.append(label)

            await self.bot.execute(
                "INSERT INTO game_member_data(author_id, role, team, game_id, queue_id, channel_id) VALUES($1, $2, $3, $4, $5, $6)",
                inter.author.id,
                label,
                team,
                view.game_id,
                inter.message.id,
                inter.channel.id
            )

            embed = await view.gen_embed(inter.message, view.game_id)

            await inter.message.edit(view=view, embed=embed, attachments=[])

            await inter.send(
                embed=success(f"Vous avez été assigné à **{label.capitalize()}**."),
                ephemeral=True,
            )
        else:
            await inter.send(
                embed=success(f"Définis ton nom en jeu pour rejoindre une file avec la commande /ign."),
                ephemeral=True,
            )
    async def disable_buttons(self, inter, view):
        for label in view.disabled:
            for btn in view.children:
                if btn.label.lower() == label:
                    btn.disabled = True
                    btn.style = ButtonStyle.gray
        
        await inter.edit_original_message(view=view)

    async def callback(self, inter):
        await inter.response.defer()

        assert self.view is not None
        view: Queue = self.view

        # if not self.cooldown:
        #     self.cooldown = datetime.now() + timedelta(seconds=1.5)
        # else:
        #     if self.cooldown <= datetime.now():
        #         self.cooldown = datetime.now() + timedelta(seconds=1.5)
        #     else:
        #         await asyncio.sleep((datetime.now() - self.cooldown).seconds)

        view.check_gameid(inter)
        
        if await self.in_ongoing_game(inter):
            return await inter.send(embed=error("Vous êtes déjà dans une partie en cours."), ephemeral=True)
        
        game_members = await self.bot.fetch(
            f"SELECT * FROM game_member_data WHERE game_id = '{view.game_id}'"
        )
        for member in game_members:
            data = await self.bot.fetch(
                f"SELECT * FROM game_member_data WHERE role = '{member[1]}' and game_id = '{view.game_id}'"
            )
            if len(data) == 2:
                if member[1] not in view.disabled:
                    view.disabled.append(member[1])
        
        if self.label.lower() in view.disabled:
            return await inter.send(embed=error("Ce rôle est pris, veuillez en choisir un autre."), ephemeral=True)

        if await view.has_participated(inter, view.game_id):
            return await inter.send(
                embed=error("Vous participez déjà à cette partie."),
                ephemeral=True,
            )

        await self.add_participant(inter, self, view)
        await self.disable_buttons(inter, view)
        await view.check_end(inter)

class LeaveButton(ui.Button):
    def __init__(self, bot, game):
        self.bot = bot
        super().__init__(
            label="Quitter la file", style=ButtonStyle.red, custom_id=f"{game}-queue:leave"
        )

    async def callback(self, inter):
        assert self.view is not None
        view: Queue = self.view
        view.check_gameid(inter)
        if await view.has_participated(inter, view.game_id):
            await self.bot.execute(
                f"DELETE FROM game_member_data WHERE author_id = {inter.author.id} and game_id = '{view.game_id}'"
            )
            await self.bot.execute(
                f"DELETE FROM duo_queue WHERE user1_id = {inter.author.id} AND game_id = '{view.game_id}' OR user2_id = {inter.author.id} AND game_id = '{view.game_id}'"
            )

            embed = await view.gen_embed(inter.message, view.game_id)

            for button in view.children:
                if button.label in ["Quitter la file", "Changer d'équipe", "Duo"]:
                    continue

                data = await self.bot.fetch(
                    f"SELECT * FROM game_member_data WHERE game_id = '{view.game_id}' and role = '{button.label.lower()}'"
                )
                if len(data) < 2:
                    if button.disabled:
                        view.disabled.remove(button.label.lower())
                        button.disabled = False
                        button.style = ButtonStyle.green

            await inter.message.edit(view=view, embed=embed)

            await inter.send(
                embed=success("Vous avez été retiré de la liste des participants."),
                ephemeral=True,
            )

        else:
            await inter.send(
                embed=error("Vous ne participez pas à cette partie."), ephemeral=True
            )

class SwitchTeamButton(ui.Button):
    def __init__(self, bot, game):
        self.bot = bot
        super().__init__(
            label="Changer d'équipe", style=ButtonStyle.blurple, custom_id=f"{game}-queue:switch"
        )
    
    async def callback(self, inter):
        await inter.response.defer()
        
        assert self.view is not None
        view: Queue = self.view
        view.check_gameid(inter)

        data = await self.bot.fetchrow(
            f"SELECT * FROM game_member_data WHERE author_id = {inter.author.id} and game_id = '{view.game_id}'"
        )
        if data:
            check = await self.bot.fetchrow(
                f"SELECT * FROM game_member_data WHERE role = '{data[1]}' and game_id = '{view.game_id}' and author_id != {inter.author.id}"
            )
            if check:
                return await inter.send(
                    "Le poste de l'autre équipe pour ce rôle est déjà occupé.",
                    ephemeral=True,
                )

            if data[2] == "blue":
                team = "red"
            else:
                team = "blue"

            await self.bot.execute(
                f"UPDATE game_member_data SET team = '{team}' WHERE game_id = $1 and author_id = $2",
                view.game_id,
                inter.author.id,
            )
            await inter.edit_original_message(embed=await view.gen_embed(inter.message, view.game_id))
            await inter.send(f"Vous avez été assigné à l'équipe **{team.capitalize()}**.", ephemeral=True)

        else:
            await inter.send(
                embed=error("Vous ne participez pas à cette partie."), ephemeral=True
            )

class DuoButton(ui.Button):
    def __init__(self, bot, game):
        self.bot = bot
        super().__init__(
            label="Duo", style=ButtonStyle.blurple, custom_id=f"{game}-queue:duo"
        )

    async def callback(self, inter):
        await inter.response.defer()
        duo_pref = await self.bot.fetchrow(f"SELECT * FROM duo_queue_preference WHERE guild_id = {inter.guild.id}")
        if not duo_pref:
            return await inter.send(embed=error("La DuoQ n'est pas activée. Merci de demander à un admin de taper `/admin duo_queue Enabled`"), ephemeral=True)

        assert self.view is not None
        view = self.view
        if isinstance(view, Queue):
            view.check_gameid(inter)

        queue_check = await self.bot.fetchrow(
            f"SELECT * FROM game_member_data WHERE author_id = {inter.author.id} and game_id = '{view.game_id}'"
        )
        if not queue_check:
            return await inter.send(embed=error("Vous ne faites pas partie de cette file."), ephemeral=True)
        
        queue_members = await self.bot.fetch(
            f"SELECT * FROM game_member_data WHERE game_id = '{view.game_id}'"
        )
        
        options = []
        for member_data in queue_members:
            duos = await self.bot.fetch(f"SELECT * FROM duo_queue WHERE game_id = '{view.game_id}'")
            member = inter.guild.get_member(member_data[0])
            if member.id == inter.author.id:
                continue
            if member_data[1] == queue_check[1]:
                continue
            check = False
            for duo in duos:
                if inter.author.id in [duo[1], duo[2]]:
                    return await inter.send(embed=error("Vous êtes déjà en duo."), ephemeral=True,)
                if member.id in [duo[1], duo[2]]:
                    check = True
            if check:
                continue
            options.append(SelectOption(label=member.display_name, value=member.id))

        if not options:
            return await inter.send(
                embed=error("Impossible de trouver des membres disponibles pour duo avec vous."),
                ephemeral=True
            )
        async def Function(select_inter, vals, *args):
            con_view = ConfirmationButtons(inter.author.id)
            m = inter.guild.get_member(int(vals[0]))
            await inter.send(f"Voulez-vous vraiment duo avec {m.display_name}?", view=con_view, ephemeral=True)
            await con_view.wait()
            if con_view.value:
                con_view = ConfirmationButtons(m.id)
                try:
                    await m.send(
                        embed=Embed(
                            title="👥 Demande de Duo",
                            description=f"**{inter.author.display_name}** vous a envoyé une demande de duo pour jouer **{args[0]}** dans {inter.channel.mention}. Acceptez-vous ?",
                            color=Color.red()
                        ),
                        view=con_view
                    )
                except:
                    return await inter.send(embed=success(f"Impossible d'envoyer de demande de duo à {m.display_name}. Ses messages privés doivent être désactivés pour le bot."), ephemeral=True)
                await inter.send(embed=success(f"Demande de duo envoyée avec succès à {m.display_name}"), ephemeral=True)
                await con_view.wait()
                if con_view.value:
                    user_duos = await self.bot.fetch(f"SELECT * FROM duo_queue WHERE game_id = '{view.game_id}'")
                    for user_duo in user_duos:
                        if int(vals[0]) in [user_duo[1], user_duo[2]]:
                            return await m.send(embed=error("Vous êtes déjà en duo."))
                    await self.bot.execute(f"INSERT INTO duo_queue(guild_id, user1_id, user2_id, game_id) VALUES($1, $2, $3, $4)", inter.guild.id, inter.author.id, int(vals[0]), args[0])
                    if isinstance(self, Queue):
                        embed = await self.gen_embed(inter.message)
                    else:
                        ready_ups = await self.bot.fetch(
                            f"SELECT * FROM ready_ups WHERE game_id = '{view.game_id}'"
                        )
                        ready_ups = [x[1] for x in ready_ups]
                        st_pref = await self.bot.fetchrow(f"SELECT * FROM switch_team_preference WHERE guild_id = {inter.guild.id}")
                        if st_pref:
                            embed = await ReadyButton(self.bot, view.game, view.game_id, inter.message).team_embed(ready_ups)
                        else:
                            embed = await ReadyButton(self.bot, view.game, view.game_id, inter.message).anonymous_team_embed(ready_ups)
                    await inter.message.edit(embed=embed, attachments=[]) 
                    await m.send(embed=success(f"Vous faites désormais équipe avec {inter.author.display_name}"))

        await inter.send(content="Sélectionnez un membre avec lequel vous souhaitez former un duo.", view=SelectMenuDeploy(self.bot, inter.author.id, options, 1, 1, Function, view.game_id), ephemeral=True)

class ReadyButton(ui.Button):
    def __init__(self, bot, game, game_id, msg = None):
        self.bot = bot
        self.game = game
        self.game_id = game_id
        self.time_of_execution = datetime.now()

        self.data = None
        self.msg = msg

        super().__init__(
            label="Prêt !", style=ButtonStyle.green, custom_id=f"{game}-queue:readyup"
        )

        self.disable_button.start()
    
    async def anonymous_team_embed(self, ready_ups):
        embed = self.msg.embeds[0]
        embed.clear_fields()
        embed.description = "Il ne s'agit pas des équipes définitives."
        duos = await self.bot.fetch(f"SELECT * FROM duo_queue WHERE game_id = '{self.game_id}'")
        in_duo = {}
        for i, duo in enumerate(duos):
            duo_emojis = [":one:", ":two:", ":three:", ":four:"]
            in_duo.update({duo[1]: duo_emojis[i]})
            in_duo.update({duo[2]: duo_emojis[i]})
        
        team_data = await self.bot.fetch(
            f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}'"
        )
        value1 = ""
        value2 = ""
        for i, team in enumerate(team_data):
            value = ""
            if team[0] in ready_ups:
                value += "✅"
            else:
                value += "❌"
            if team[0] in in_duo:
                value += f"{in_duo[team[0]]} "
            
            value += f"<@{team[0]}> - `{team[1].capitalize()}` \n"
            if i in range(0, 5):
                value1 += value
            else:
                value2 += value

        embed.add_field(name="👥 Participants", value=value1)
        embed.add_field(name="👥 Participants", value=value2)

        with open('assets/tips.txt', 'r') as f:
            tips = f.readlines()
            tip = random.choice(tips) 
        embed.set_footer(text="🎮 " + self.game_id + '\n' + "💡 " + tip)

        return embed

    async def team_embed(self, ready_ups):

        embed = self.msg.embeds[0]
        embed.clear_fields()
        teams = ["blue", "red"]
        embed.description = ""

        duos = await self.bot.fetch(f"SELECT * FROM duo_queue WHERE game_id = '{self.game_id}'")
        in_duo = []
        for duo in duos:
            in_duo.extend([duo[1], duo[2]])
        duo_usage = 0
        duo_emoji = ":one:"

        for team in teams:

            team_data = await self.bot.fetch(
                f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}' and team = '{team}'"
            )

            if team == "red":
                emoji = "🔴"
            elif team == "blue":
                emoji = "🔵"

            name = f"{emoji} {team.capitalize()}"

            if team_data:
            
                value = ""
                for data in team_data:
                    
                    if data[0] in ready_ups:
                        value += "✅ "
                    else:
                        value += "❌ "
                    if data[0] in in_duo:
                        value += f"{duo_emoji} "
                        duo_usage += 1
                        if not duo_usage%2:
                            if duo_usage/2 == 1:
                                duo_emoji = ":two:"
                            elif duo_usage/2 == 2:
                                duo_emoji = ":three:"
                            elif duo_usage/2 == 3:
                                duo_emoji = ":four:"
                            else:
                                duo_emoji = ":five:" # Should not happen

                    value += f"<@{data[0]}> - `{data[1].capitalize()}`\n"
            else:
                value = "Pas encore de joueur"

            embed.add_field(name=name, value=value)

        with open('assets/tips.txt', 'r') as f:
            tips = f.readlines()
            tip = random.choice(tips) 
        embed.set_footer(text="🎮 " + self.game_id + '\n' + "💡 " + tip)

        return embed

    async def lol_lobby(self, inter, lobby_channel):
        response = None
        async with websockets.connect("wss://draftlol.dawe.gg/") as websocket:
            data = {"type": "createroom", "blueName": "Équipe Bleu", "redName": "Équipe Rouge", "disabledTurns": [], "disabledChamps": [], "timePerPick": "30", "timePerBan": "30"}
            await websocket.send(json.dumps(data))
            
            try:
                async with async_timeout.timeout(10):
                    result = await websocket.recv()
                    if result:
                        data = json.loads(result)
                        response = ("🔵 https://draftlol.dawe.gg/" + data["roomId"] +"/" +data["bluePassword"] + " (Uniquement un joueur de l'équipe bleu sur ce lien)", "🔴 https://draftlol.dawe.gg/" + data["roomId"] +"/" +data["redPassword"] + " (Uniquement un joueur de l'équipe bleu sur ce lien)", "\n**Spectators:** https://draftlol.dawe.gg/" + data["roomId"] + " (Lien pour tous les autres joueurs)")
            except asyncio.TimeoutError:
                pass
        
        if response:
            await lobby_channel.send(
                embed=Embed(
                    title="League of Legends Draft",
                    description="\n".join(response),
                    color=Color.blurple()
                )
            )
        else:
            await lobby_channel.send(
                embed=error("Draftlol ne répond pas, impossible de récupérer un lien.")
            )

        region = await self.bot.fetchrow(f"SELECT region FROM queuechannels WHERE channel_id = {inter.channel.id}")
        if not region[0]:
            region = "na"
        else:
            region = region[0]
        teams = {
            'blue': '',
            'red': ''
        }

        for team in teams:
            url = f'https://www.op.gg/multisearch/{region}?summoners='
            data = await self.bot.fetch(f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}' and team = '{team}'")
            nicknames = []
            for entry in data:
                ign = await self.bot.fetchrow(f"SELECT ign FROM igns WHERE guild_id = {inter.guild.id} and user_id = {entry[0]} and game = 'lol'")
                if ign:
                    nicknames.append(ign[0].replace(' ', '%20'))
                else:
                    member = lobby_channel.guild.get_member(entry[0])
                    if member.nick:
                        nick = member.nick
                    else:
                        nick = member.name

                    pattern = re.compile("ign ", re.IGNORECASE)
                    nick = pattern.sub("", nick)

                    pattern2 = re.compile("ign: ", re.IGNORECASE)
                    nick = pattern2.sub("", nick)


                    nicknames.append(str(nick).replace(' ', '%20'))

            for i, nick in enumerate(nicknames):
                if not i == 0:
                    url += "%2C"
                url += nick

            teams[team] = url
        
        await lobby_channel.send(
            embed=Embed(
                title="🔗 Multi OP.GG",
                description=f"🔵 {teams['blue']}\n🔴 {teams['red']}",
                color=Color.blurple()
            )
        )

    async def valorant_lobby(self, lobby_channel):
        map_dict = random.choice(self.bot.valorant_maps)
        for key in map_dict.keys():
            map_name = key
            map_link = map_dict[key]
        embed = Embed(
            title="Game Map (Optional)",
            description=f"Set the game map to **{map_name}**.",
            color=Color.red()
        )
        embed.set_image(url=map_link)
        await lobby_channel.send(embed=embed)

        options = []
        for label in VALORANT_LABELS:
            if label == "Flex":
                continue
            options.append(SelectOption(label=label, value=label.lower()))

        async def Function(inter, val, *args):
            await self.bot.execute(
                f"UPDATE game_member_data SET role = 'flex - {val[0]}' WHERE author_id = {inter.author.id} and game_id = '{self.game_id}'"
            )
            await inter.send(embed=success(f"You've been given {val[0].capitalize()} successfully."), ephemeral=True)
            await inter.delete_original_message()
        
        flex_roles = await self.bot.fetch(f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}' and role = 'flex'")
        for holder in flex_roles:
            view = SelectMenuDeploy(self.bot, holder[0], options, 1, 1, Function)
            await lobby_channel.send(content=f"<@{holder[0]}> select the role you wish to play.", view=view)

    async def overwatch_lobby(self, lobby_channel):
        gamemode_dict = random.choice(self.bot.overwatch)
        for key in gamemode_dict.keys():
            gamemode_name = key
            gamemode_maps_Dict = gamemode_dict[key]
        map_dict = random.choice(gamemode_maps_Dict)
        for key in map_dict.keys():
            map_name = key
            map_link = map_dict[key]
        embed = Embed(
            title="Game Settings (Optional)",
            description=f"Game Mode: **{gamemode_name}** \nGame Map: **{map_name}**",
            color=Color.red()
        )
        embed.set_image(url=map_link)
        await lobby_channel.send(embed=embed)

    async def check_members(self, msg):
        members = await self.bot.fetch(
            f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}'"
        )
        if await self.bot.check_testmode(msg.guild.id):
            required_members = 2
        else:
            required_members = 10

        if len(members) != required_members:
            self.disable_button.stop()
            await start_queue(self.bot, msg.channel, self.game, None, msg, self.game_id)

    @tasks.loop(seconds=1)
    async def disable_button(self):
        await self.bot.wait_until_ready()
        
        if self.msg:
            await self.check_members(self.msg)
            # Update the stored message and stop timer if ready up phase was removed
            msg = self.bot.get_message(self.msg.id)
            if not msg:
                msg = await self.msg.channel.fetch_message(self.msg.id)
                if msg:
                    self.msg = msg
            else:
                self.msg = msg

            if not self.msg.components[0].children[0].label == "Prêt !":
                self.disable_button.stop()
                return

        if (datetime.now() - self.time_of_execution).seconds >= 120:
            if self.msg:
                ready_ups = await self.bot.fetch(
                    f"SELECT user_id FROM ready_ups WHERE game_id = '{self.game_id}'"
                )

                ready_ups = [x[0] for x in ready_ups]
                game_members = [member[0] for member in self.data]
                players_removed = []

                for user_id in game_members:
                    if user_id not in ready_ups:
                        await self.bot.execute(
                            f"DELETE FROM game_member_data WHERE author_id = {user_id} and game_id = '{self.game_id}'"
                        )
                        players_removed.append(user_id)
                        await self.bot.execute(
                            f"DELETE FROM duo_queue WHERE game_id = '{self.game_id}' and user1_id = {user_id} OR game_id = '{self.game_id}' and user2_id = {user_id}"
                        )

                        user = self.bot.get_user(user_id)
                        await user.send(
                            embed=Embed(
                                description=f"Vous avez été retiré de la [file]({self.msg.jump_url}) car vous n'étiez pas prêt à temps.",
                                color=Color.red(),
                            )
                        )

                await self.bot.execute(
                    f"DELETE FROM ready_ups WHERE game_id = '{self.game_id}'"
                )
                st_pref = await self.bot.fetchrow(f"SELECT * FROM switch_team_preference WHERE guild_id = {self.msg.guild.id}")
                if not st_pref:
                    sbmm = True
                else:
                    sbmm = False
                duo_pref = await self.bot.fetchrow(f"SELECT * FROM duo_queue_preference WHERE guild_id = {self.msg.guild.id}")
                if duo_pref:
                    duo = True
                else:
                    duo = False
                test_mode = await self.bot.check_testmode(self.msg.guild.id)
                await self.msg.edit(
                    embed=await Queue.gen_embed(self, self.msg, self.game_id, test_mode),
                    view=Queue(self.bot, sbmm, duo, self.game),
                    content="Tous les joueurs n'étaient pas prêt, la file a été libérée.",
                )
                await self.msg.channel.send(
                    content=", ".join(f"<@{x}>" for x in players_removed),
                    embed=Embed(
                        description="Les joueurs mentionnés on été supprimé de la file car ils n'étaient pas prêt à temps.",
                        color=Color.blurple(),
                    ),
                )

                self.disable_button.stop()

            else:
                self.time_of_execution = datetime.now()

    async def callback(self, inter):
        if not inter.response.is_done():
            await inter.response.defer()

        if not self.msg:
            self.msg = inter.message

        if not self.data:
            self.data = await self.bot.fetch(
                f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}'"
            )
        
        await self.check_members(inter.message)

        game_members = [member[0] for member in self.data]
        ready_ups = await self.bot.fetch(
            f"SELECT * FROM ready_ups WHERE game_id = '{self.game_id}'"
        )
        ready_ups = [x[1] for x in ready_ups]

        if inter.author.id in game_members:
            if inter.author.id in ready_ups:
                await inter.send(
                    embed=success("Vous êtes prêts, on le sait."), ephemeral=True
                )
                return

            await self.bot.execute(
                "INSERT INTO ready_ups(game_id, user_id) VALUES($1, $2)",
                self.game_id,
                inter.author.id,
            )
            ready_ups.append(inter.author.id)

            st_pref = await self.bot.fetchrow(f"SELECT * FROM switch_team_preference WHERE guild_id = {inter.guild.id}")
            if st_pref:
                embed = await self.team_embed(ready_ups)
            else:
                embed = await self.anonymous_team_embed(ready_ups)
            await inter.message.edit(
                f"{len(ready_ups)}/10 Joueurs sont prêts !\nCliquez sur prêt avant <t:{int(datetime.timestamp((self.time_of_execution + timedelta(seconds=110))))}:t>",
                embed=embed,
            )

            if await self.bot.check_testmode(inter.guild.id):
                required_readyups = 2
            else:
                required_readyups = 10
            if len(ready_ups) == required_readyups:
                
                if not st_pref:
                    member_data = await self.bot.fetch(
                        f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}'"
                    )

                    if self.game == 'lol':
                        labels = LOL_LABELS
                    elif self.game == 'valorant':
                        labels = VALORANT_LABELS
                    elif self.game == "overwatch":
                        labels = OVERWATCH_LABELS
                    else:
                        labels = OTHER_LABELS
                    
                    if await self.bot.check_testmode(inter.guild.id):
                        roles_occupation = {
                            labels[0].upper(): [{'user_id': 890, 'rating': Rating()}, {'user_id': 3543, 'rating': Rating()}],
                            labels[1].upper(): [{'user_id': 709, 'rating': Rating()}, {'user_id': 901, 'rating': Rating()},],
                            labels[2].upper(): [{'user_id': 789, 'rating': Rating()}, {'user_id': 981, 'rating': Rating()}, ],
                            labels[3].upper(): [{'user_id': 234, 'rating': Rating()}, {'user_id': 567, 'rating': Rating()}, ],
                            labels[4].upper(): []
                        }
                    else:
                        roles_occupation = {
                        labels[0].upper(): [],
                        labels[1].upper(): [],
                        labels[2].upper(): [],
                        labels[3].upper(): [],
                        labels[4].upper(): []
                        }

                    for data in member_data:
                        member_rating = await self.bot.fetchrow(f"SELECT * FROM mmr_rating WHERE user_id = {data[0]} and guild_id = {inter.guild.id} and game = '{self.game}'")
                        if member_rating:
                            mu = float(member_rating[2])
                            sigma = float(member_rating[3])
                            rating = Rating(mu, sigma)

                        else:
                            rating = Rating()
                            await self.bot.execute(
                                f"INSERT INTO mmr_rating(guild_id, user_id, mu, sigma, counter, game) VALUES($1, $2, $3, $4, $5, $6)",
                                inter.guild.id,
                                data[0],
                                rating.mu,
                                rating.sigma,
                                0,
                                self.game
                            )

                        roles_occupation[data[1].upper()].append({'user_id': data[0], 'rating': rating})

                    all_occupations = [*roles_occupation.values()]

                    unique_combinations = list(itertools.product(*all_occupations))
                    team_data = []
                    qualities = []
                    for pair in unique_combinations:
                        players_in_pair = [x['user_id'] for x in list(pair)]
                        t2 = []
                        for x in roles_occupation:
                            for val in roles_occupation[x]:
                                if val['user_id'] not in players_in_pair:
                                    t2.append(val)
                        duo = await self.bot.fetch(
                            f"SELECT * FROM duo_queue WHERE game_id = '{self.game_id}'"
                        )
                        check = True
                        for duo_data in duo:
                            user1 = duo_data[1]
                            user2 = duo_data[2]
                            
                            if not ( ( user1 in players_in_pair and user2 in players_in_pair ) or ( user1 in [x['user_id'] for x in t2] and user2 in [x['user_id'] for x in t2] ) ):
                                check = False
                        if not check:
                            # Skip the pair
                            continue

                        qua = quality([[x['rating'] for x in list(pair)], [x['rating'] for x in t2]])
                        qualities.append(qua)
                        team_data.append({'quality': qua, 'teams': [list(pair), t2]})

                    closet_quality = qualities[min(range(len(qualities)), key=lambda i: abs(qualities[i] - 50))]
                    for entry in team_data:
                        if entry['quality'] == closet_quality:
                            final_teams = entry['teams']
                    
                    for i, team_entries in enumerate(final_teams):
                        if i:
                            team = 'blue'
                        else:
                            team = 'red'
                        for entry in team_entries:
                            await self.bot.execute("UPDATE game_member_data SET team = $1 WHERE author_id = $2", team, entry['user_id'])
                    self.data = await self.bot.fetch(
                        f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}'"
                    )
                else:
                    pass
                            
                preference = await self.bot.fetchrow(f"SELECT * FROM queue_preference WHERE guild_id = {inter.guild.id}")
                if preference:
                    preference = preference[1]
                else:
                    preference = 1

                if preference == 1:
                    for member in game_members:
                        # Remove member from all other queues
                        await self.bot.execute(
                            f"DELETE FROM game_member_data WHERE author_id = {member} and game_id != '{self.game_id}'"
                        )

                await self.bot.execute(
                    f"DELETE FROM ready_ups WHERE game_id = '{self.game_id}'"
                )

                try:
                    # Creating roles
                    red_role = await inter.guild.create_role(
                        name=f"Red: {self.game_id}"
                    )
                    blue_role = await inter.guild.create_role(
                        name=f"Blue: {self.game_id}"
                    )

                    overwrites_red = {
                        inter.guild.default_role: PermissionOverwrite(connect=False),
                        red_role: PermissionOverwrite(connect=True),
                        self.bot.user: PermissionOverwrite(
                            send_messages=True, manage_channels=True, connect=True
                        ),
                    }
                    overwrites_blue = {
                        inter.guild.default_role: PermissionOverwrite(connect=False),
                        blue_role: PermissionOverwrite(connect=True),
                        self.bot.user: PermissionOverwrite(
                            send_messages=True, manage_channels=True, connect=True
                        ),
                    }
                    mutual_overwrites = {
                        inter.guild.default_role: PermissionOverwrite(
                            send_messages=False
                        ),
                        red_role: PermissionOverwrite(send_messages=True),
                        blue_role: PermissionOverwrite(send_messages=True),
                        self.bot.user: PermissionOverwrite(
                            send_messages=True, manage_channels=True
                        ),
                    }

                    # Creating channels
                    game_category_id = await self.bot.fetchrow(f"SELECT * FROM game_categories WHERE guild_id = {inter.guild.id} and game = '{self.game}'")
                    if game_category_id:
                        game_category = self.bot.get_channel(game_category_id[1])
                    else:
                        game_category = await inter.guild.create_category(
                            name=f"Partie:  {self.game_id}", overwrites=mutual_overwrites
                        )
                    game_lobby = await game_category.create_text_channel(
                        f"Lobby: {self.game_id}", overwrites=mutual_overwrites
                    )
                    
                    voice_channel_blue = await game_category.create_voice_channel(
                        f"Blue: {self.game_id}", overwrites=overwrites_blue
                    )
                    
                    voice_channel_red = await game_category.create_voice_channel(
                        f"Red: {self.game_id}", overwrites=overwrites_red
                    )
                except:
                    # If this ever fails due to limitations of discord or lack of permissions
                    await inter.send(
                        embed=error(
                            "Impossible de créer les canaux/roles. Merci de contacter un administrateur."
                        )
                    )
                    print(traceback.format_exc())
                    return

                await inter.message.edit(
                    content="La partie est actuellement en cours",
                    view=SpectateButton(self.bot, self.game_id),
                )

                for entry in self.data:
                    if entry[2] == "red":
                        member = inter.guild.get_member(entry[0])
                        await member.add_roles(red_role)

                    elif entry[2] == "blue":
                        member = inter.guild.get_member(entry[0])
                        await member.add_roles(blue_role)

                await game_lobby.send(
                    content=f"{red_role.mention} {blue_role.mention}",
                    embed=await self.team_embed(ready_ups),
                    view=SpectateButton(self.bot, self.game_id)
                )
                await game_lobby.send(
                    embed=Embed(
                        title=":warning: INFORMATIONS",
                        description=f"Votre partie est lancée ! Veuillez rejoindre votre vocal dès que possible.\n"
                                    f"C'est à l'équipe Bleu de créer la partie presonnalisée. Entrez `ouat{self.game_id}` en tant que nom de partie et mot de passe.\n"
                                    f"En type de partie, choississez mode aveugle et autorisez tous les spectateurs.\n\n"
                                    f"Une fois la partie terminée, tapez `/win`.\n "
                                    f"**6** votes **DOIVENT** être émis.\n"
                                    f"Seuls les votes des **membres** du lobby compteront.\n \n",
                        color=Color.yellow(),
                    )
                )

                await self.bot.execute(
                    f"INSERT INTO games(game_id, lobby_id, voice_red_id, voice_blue_id, red_role_id, blue_role_id, queuechannel_id, msg_id, game) VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                    self.game_id,
                    game_lobby.id,
                    voice_channel_red.id,
                    voice_channel_blue.id,
                    red_role.id,
                    blue_role.id,
                    inter.channel.id,
                    inter.message.id,
                    self.game
                )

                if self.game == 'lol':
                    await self.lol_lobby(inter, game_lobby)

                elif self.game == 'valorant':
                    await self.valorant_lobby(game_lobby)
                
                elif self.game == 'overwatch':
                    await self.overwatch_lobby(game_lobby)

                self.disable_button.cancel()
                await start_queue(self.bot, inter.channel, self.game)

        else:
            await inter.send(
                embed=error("Vous ne participez pas à cette partie."), ephemeral=True
            )

class ReadyUp(ui.View):
    def __init__(self, bot, game, game_id, duo):
        super().__init__(timeout=None)
        self.bot = bot
        self.game_id = game_id
        self.game = game
        self.add_item(ReadyButton(bot, game, game_id))
        if duo:
            self.add_item(DuoButton(bot, game))


class Queue(ui.View):
    def __init__(self, bot, sbmm, duo, game, testmode):
        super().__init__(timeout=None)
        self.bot = bot
        self.disabled = []
        self.game_id = None
        self.game = game
        self.msg = None
        if game == 'lol':
            labels = LOL_LABELS
        elif game == 'valorant':
            labels = VALORANT_LABELS
        elif game == "overwatch":
            labels = OVERWATCH_LABELS
        else:
            labels = OTHER_LABELS

        for i, label in enumerate(labels):
            if i != len(labels)-1:
                self.add_item(RoleButtons(bot, label, f"{game}-queue:{label.lower()}", testmode))
            else:
                self.add_item(RoleButtons(bot, label, f"{game}-queue:{label.lower()}", False))
        
        self.add_item(LeaveButton(bot, game))
        if not sbmm:
            self.add_item(SwitchTeamButton(bot, game))
        if duo and sbmm:
            self.add_item(DuoButton(bot, game))
            self.duo = True
        else:
            self.duo = False
    
    def check_gameid(self, inter):
        if not self.game_id:
            self.game_id = inter.message.embeds[0].footer.text.split('\n')[0].replace(' ', '').replace("🎮", "")

    async def has_participated(self, inter, game_id) -> bool:
        data = await self.bot.fetchrow(
            f"SELECT * FROM game_member_data WHERE author_id = {inter.author.id} and game_id = '{game_id}'"
        )
        if data:
            return True
        return False
    
    async def gen_embed(self, msg, game_id) -> Embed:
        embed = msg.embeds[0]
        embed.clear_fields()
        teams = ["blue", "red"]
        
        duo_usage = 0
        duo_emoji = ":one:"
        for index, team in enumerate(teams):
            team_data = await self.bot.fetch(
                f"SELECT * FROM game_member_data WHERE game_id = '{game_id}' and team = '{team}'"
            )

            if team == "red":
                emoji = "🔴"
            elif team == "blue":
                emoji = "🔵"

            name = f"{emoji} {team.capitalize()}"
            st_pref = await self.bot.fetchrow(f"SELECT * FROM switch_team_preference WHERE guild_id = {msg.guild.id}")
            if not st_pref:
                name = f"Groupe {index+1}"
            
            if team_data:
                duos = await self.bot.fetch(f"SELECT * FROM duo_queue WHERE game_id = '{game_id}'")
                in_duo = []
                for duo in duos:
                    in_duo.extend([duo[1], duo[2]])
            
                value = ""
                for data in team_data:
                    if data[0] in in_duo:
                        value += f"{duo_emoji} "
                        duo_usage += 1
                        if not duo_usage%2:
                            if duo_usage/2 == 1:
                                duo_emoji = ":two:"
                            elif duo_usage/2 == 2:
                                duo_emoji = ":three:"
                            elif duo_usage/2 == 3:
                                duo_emoji = ":four:"
                            else:
                                duo_emoji = ":five:" # Should not happen
                    value += f"<@{data[0]}> - `{data[1].capitalize()}`\n"

            else:
                value = "Pas encore de joueur"

            embed.add_field(name=name, value=value)

        with open('assets/tips.txt', 'r') as f:
            tips = f.readlines()
            tip = random.choice(tips) 
        embed.set_footer(text="🎮 " + game_id + '\n' + "💡 " + tip)

        return embed

    async def check_end(self, inter) -> None:
        checks_passed = 0
        for button in self.children:
            if button.label in ["Quitter la file", "Changer d'équipe", "Duo"]:
                continue

            data = await self.bot.fetch(
                f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}' and role = '{button.label.lower()}'"
            )
            if len(data) == 2:
                checks_passed += 1

        if await self.bot.check_testmode(inter.guild.id):
            required_checks = 1
        else:
            required_checks = 5
        if checks_passed == required_checks:
            member_data = await self.bot.fetch(
                f"SELECT * FROM game_member_data WHERE game_id = '{self.game_id}'"
            )

            mentions = (
                ", ".join(f"<@{data[0]}>" for data in member_data)
            )

            self.msg = inter.message
            st_pref = await self.bot.fetchrow(f"SELECT * FROM switch_team_preference WHERE guild_id = {inter.guild.id}")
            if st_pref:
                embed = await ReadyButton.team_embed(self, [])
            else:
                embed = await ReadyButton.anonymous_team_embed(self, [])
            
            # self.ready_up = True
            await inter.edit_original_message(
                view=None
            )
            await inter.edit_original_message(
                view=ReadyUp(self.bot, self.game, self.game_id, self.duo),
                content="0/10 Joueurs sont prêts !",
                embed=embed
            )

            embed = Embed(
                description=f"Une game a été trouvée! Il est temps de cliquer sur prêt!", color=Color.blurple()
            )

            await inter.message.reply(mentions, embed=embed, delete_after=120.0)