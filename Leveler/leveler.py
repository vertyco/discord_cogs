﻿# -*- coding: utf-8 -*-

from redbot.core import checks, Config
import discord
from redbot.core import commands
from redbot.core.utils import mod
from redbot.core.data_manager import cog_data_path
import asyncio
import datetime
from .userprofile import UserProfile
from . import __path__
from PIL import Image, ImageDraw, ImageFont
from math import floor, ceil
import os
from collections import namedtuple
import urllib
import aiohttp
from random import randint
from redbot.core.i18n import Translator, cog_i18n
from io import BytesIO
import functools
import textwrap



_ = Translator("Leveler", __file__)


@cog_i18n(_)
class Leveler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.profiles = UserProfile()
        self.loop = self.bot.loop.create_task(self.start())
        self.restart = True
        self.__path__ = __path__


    __version__ = "1.0.0"
    __author__ = "Malarne#1418"
    __info__ = {
        "bot_version": "3.0.0rc2",
        "description": (
            "A leveler cog for Red V3\n",
            "Inspired by Stevy's v2 leveler cog\n",
            "Please consult the docs at ayrobot.netlify.com for setup informations.\n",
            "Thanks for using my cog !"
        ),
        "hidden": False,
        "install_msg": (
            "Thank you for installing this leveler !\n",
            "Please consult the docs at ayrobot.netlify.com for setup informations."
        ),
        "required_cogs": [],
        "requirements": ["pillow"],
        "short": "Leveler tool, better than MEE6",
        "tags": ["leveler", "pillow", "fun"]
    }


    def __unload(self):
        self.loop.cancel()


    async def start(self):
        await self.bot.wait_until_ready()
        while True:
            if not self.restart:
                guilds = self.bot.guilds
                for i in guilds:
                    profils = await self.profiles.data.all_members(i)
                    for j in profils.keys():
                        member = i.get_member(j)
                        if member is None:
                            await self._reset_member(i, j)
                        else:
                            await self.profiles.data.member(member).today.set(0)
                self.restart = True
            if datetime.datetime.now().strftime('%H:%M') in ["05:00", "05:01", "05:02", "05:03", "05:04", "05:05"]:
                self.restart = False
            await asyncio.sleep(30)

    async def _reset_member(self, guild, memberid):
        try:
            base = self.profiles.data._get_base_group(self.profiles.data.MEMBER)
            await base.clear_raw(str(guild.id), memberid)
        except:
            pass

    @commands.command(hidden=True)
    @checks.is_owner()
    async def testreset(self, ctx):
        self.restart = False
        await ctx.send(_("Reset dans max 30 secondes"), delete_after=30)

    async def get_avatar(self, user):
        async with aiohttp.ClientSession() as session:
            async with session.get(user.avatar_url_as(format="png", size=1024)) as f:
                data = await f.read()
                return BytesIO(data)

    async def get_background(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as f:
                data = await f.read()
                return Image.open(BytesIO(data))

    def round_corner(self, radius):
        """Draw a round corner"""
        corner = Image.new('L', (radius, radius), 0)
        draw = ImageDraw.Draw(corner)
        draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=255)
        return corner

    def add_corners(self, im, rad):
        # https://stackoverflow.com/questions/7787375/python-imaging-library-pil-drawing-rounded-rectangle-with-gradient
        width, height = im.size
        alpha = Image.new('L', im.size, 255)
        origCorner = self.round_corner(rad)
        corner = origCorner
        alpha.paste(corner, (0,0))
        corner = origCorner.rotate(90)
        alpha.paste(corner, (0, height-rad))
        corner = origCorner.rotate(180)
        alpha.paste(corner, (width - rad, height - rad))
        corner = origCorner.rotate(270)
        alpha.paste(corner, (width - rad, 0))
        im.putalpha(alpha)
        return im

    def make_full_profile(self, avatar_data, user, xp, nxp, lvl, minone, elo, ldb, desc, bg=None):
        img = Image.new("RGBA", (340, 390), (17, 17, 17, 255))
        if bg is not None:
            bg_width, bg_height = bg.size
            ratio = bg_height/390
            bg = bg.resize((int(bg_width/(ratio)), int(bg_height/ratio)))
            if bg.size[0] <340:
                ratio = bg_width/340
                bg = bg.resize((int(bg_width/(ratio)), int(bg_height/ratio)))
            bg = bg.convert("RGBA")
            bg.putalpha(128)
            offset = 0
            if bg.size[0] >= 340:
                offset = (int((-(bg.size[0]-340)/2)), 0)
            if bg.size[0] <340:
                offset = (0, int((-(bg.size[1]-390)/2)))
        
            img.paste(bg, offset, bg)
        img = self.add_corners(img, 10)
        draw = ImageDraw.Draw(img)
        usercolor = (255, 255, 0)  # user.color.to_rgb()
        aviholder = self.add_corners(Image.new("RGBA", (140, 140), (255, 255, 255, 255)), 10)
        nameplate = self.add_corners(Image.new("RGBA", (180, 60), (0, 0, 0, 255)), 10)
        xptot = self.add_corners(Image.new("RGBA", (310, 20), (215, 215, 215, 255)), 10)
        img.paste(aviholder, (10, 10), aviholder)
        img.paste(nameplate, (155, 10), nameplate)
        img.paste(xptot, (15, 340), xptot)

        font1 = ImageFont.truetype(os.path.join(__path__[0],"cambria.ttc"), 18)
        font2 = ImageFont.truetype(os.path.join(__path__[0],"cambria.ttc"), 22)
        font3 = ImageFont.truetype(os.path.join(__path__[0],"cambria.ttc"), 32)

        avatar = Image.open(avatar_data)
        avatar_size = 130, 130
        avatar.thumbnail(avatar_size)
        img.paste(avatar, (15, 15))
        lxp = xp - minone
        lnxp = nxp - minone
        prc = floor(xp / (nxp / 100))
        lprc = ceil(lxp / (lnxp / 100))
        b_offset = floor(lprc * 3.1)
        xpbar = self.add_corners(Image.new("RGBA", (b_offset, 20), usercolor), 10)
        img.paste(xpbar, (12, 340), xpbar)

        lvl_str = _("Niveau:")
        ldb_str = _("Classement:")
        rank_str = _("Elo:")
        prog_str = _("Le progrès:")

        draw.text((10, 180), lvl_str, fill='white', font=font3)
        draw.text((10, 220), ldb_str, fill='white', font=font3)
        draw.text((10, 260), rank_str, fill='white', font=font3)
        nick = user.display_name
        if font2.getsize(nick)[0] > 150:
            nick = nick[:15] + "..."

        draw.text((154, 316), f"{lprc}%", fill=usercolor, font=font1)
        draw.text((100, 360), (prog_str + f" {xp}/{nxp}"), fill=usercolor, font=font1)
        draw.text(((font3.getsize(lvl_str)[0]+20), 180), f"{lvl}", fill=usercolor, font=font3)
        draw.text(((font3.getsize(ldb_str)[0]+20), 220), f"{ldb}", fill=usercolor, font=font3)
        draw.text(((font3.getsize(rank_str)[0]+20), 260), f"{elo}", fill=usercolor, font=font3)

        draw.text((162, 14), f"{nick}", fill=usercolor, font=font2)
        draw.text((162, 40), f"{user.name}#{user.discriminator}", fill=usercolor, font=font1)
        margin = 162
        offset = 70
        count = 0
        for line in textwrap.wrap(desc, width=20):
            count += 1
            if count == 6:
                draw.text((margin, offset), f"{line}...", fill=usercolor, font=font1)
                break
            draw.text((margin, offset), f"{line}", fill=usercolor, font=font1)
            offset += font1.getsize(line)[1]
        temp = BytesIO()
        img.save(temp, format="PNG")
        temp.name = "profile.png"
        return temp

    async def profile_data(self, user):
        """Async get user profile data to pass to image creator"""
        avatar = await self.get_avatar(user)
        try:
            bg = await self.get_background(await self.profiles._get_background(user))
        except:
            bg = None
        data = {"avatar_data":avatar, 
                "user":user,
                "xp":0, 
                "nxp":100, 
                "lvl":1, 
                "minone":0,
                "elo":_("Nouveau"),
                "ldb":0,
                "desc":"",
                "bg":bg}
        if not await self.profiles._is_registered(user):
            return data            
        else:
            data["xp"] = await self.profiles._get_exp(user)
            data["nxp"] = await self.profiles._get_level_exp(user)
            data["lvl"] = lvl = await self.profiles._get_level(user)
            data["ldb"] = await self.profiles._get_leaderboard_pos(user.guild, user)
            data["desc"] = await self.profiles._get_description(user)
            if data["lvl"] != 1:
                data["minone"] = await self.profiles._get_xp_for_level(lvl -1)
            else:
                data["minone"] = 0
            roles = await self.profiles._get_guild_roles(user.guild)
            ln = data["lvl"] // 10
            if ln == 0 or len(roles) == 0:
                data["elo"] = _("Nouveau")
            elif ln > len(roles):
                elo = roles[len(roles)-1]
                data["elo"] = user.guild.get_role(elo).name
            else:
                elo = roles[ln-1]
                data["elo"] = user.guild.get_role(elo).name
        return data

    @commands.command()
    async def profile(self, ctx, user : discord.Member = None):
        """Affiche la progression sur le Leveler. Defaut a soi-même s'il n'y a pas de tag après la commande."""
        if user is None:
            user = ctx.author
        data = await self.profile_data(user)
        
        task = functools.partial(self.make_full_profile, **data)
        task = self.bot.loop.run_in_executor(None, task)
        try:
            img = await asyncio.wait_for(task, timeout=60)
        except asyncio.TimeoutError:
            return
            
        img.seek(0)
        await ctx.send(file=discord.File(img))

    async def on_message(self, message):
        if type(message.author) != discord.Member:
            # throws an error when webhooks talk, this fixes it
            return
        if type(message.channel) != discord.channel.TextChannel:
            return
        if message.author.bot:
            return
        if await self.profiles.data.guild(message.guild).whitelist():
            if message.channel.id not in await self.profiles._get_guild_channels(message.author.guild):
                return
        elif await self.profiles.data.guild(message.guild).blacklist():
            if message.channel.id in await self.profiles._get_guild_blchannels(message.author.guild):
                return

        if not await self.profiles._is_registered(message.author):
            if await self.profiles._get_auto_register(message.guild):
                await self.profiles._register_user(message.author)
                return

        elif await self.profiles._is_registered(message.author):
            if message.content is not None:
                if message.content[0] in await self.bot.get_prefix(message):
                    return
            timenow = datetime.datetime.now().timestamp()
            lastmessage = await self.profiles._get_user_lastmessage(message.author)
            cooldown = await self.profiles._get_cooldown(message.guild)
            if timenow - lastmessage < cooldown:
                # check if we've passed the cooldown
                # return None if messages are sent too soon
                return
            mots = len(message.content.split(" "))
            if mots <= 10:
                xp = 1
            elif mots > 10:
                xp = 2
            await self.profiles._today_addone(message.author)
            await self.profiles._give_exp(message.author, xp)
            await self.profiles._set_user_lastmessage(message.author, timenow)
            lvl = await self.profiles._get_level(message.author)
            roles = await self.profiles._get_guild_roles(message.guild)
            ln = lvl//10
            if ln == 0:
                return
            elif ln >= len(roles):
                ln = len(roles) -1
            grade = message.guild.get_role(roles[ln-1])
            if grade is None:
                return
            if not grade in message.author.roles:
                for i in roles:
                    role = message.guild.get_role(i)
                    if role is None:
                        continue
                    await message.author.remove_roles(role)
                await message.author.add_roles(grade)
            

    @commands.command()
    async def register(self, ctx):
        """Vous permets de commencer a gagner de l'expérience !"""
        if await self.profiles._is_registered(ctx.author):
            await ctx.send(_("Vous êtes déjà enregistré !"))
            return
        else:
            await self.profiles._register_user(ctx.author)
            await ctx.send(_("Vous avez été enregistré avec succès !"))
            return

    @commands.command()
    async def toplevel(self, ctx):
        """Affiche le classement des meilleures blablateurs !"""
        ld = await self.profiles._get_leaderboard(ctx.guild)
        emb = discord.Embed(title=_("Le classement des PGM !"))
        for i in range(len(ld)):
            cur = ld[i]
            user = ctx.guild.get_member(cur["id"])
            if user is None:
                await self._reset_member(ctx.guild, cur["id"])
            else:
                txt = _("Niveau")+" {} | {} XP | {} ".format(cur["lvl"], 
                                                             cur["xp"], 
                                                             cur["today"]) +_("Messages Today!")
                emb.add_field(name="{}".format(user.display_name), value=txt)
        await ctx.send(embed=emb)

    @commands.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def levelerset(self, ctx):
        """Commandes de configuration."""
        pass

    @levelerset.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def channel(self, ctx):
        """Configuration des channels permettant de gagner de l'expérience."""
        pass

    @channel.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def whitelist(self, ctx):
        """Configuration des channels whitelistés"""
        pass

    @channel.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def blacklist(self, ctx):
        """Configuration des channels blacklistés"""
        pass    

    @levelerset.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def roles(self, ctx):
        """Configuration des roles obtenables grâce à l'expérience."""
        pass

    @commands.group()
    async def profileset(self, ctx):
        """Définir divers paramètres de profil"""
        pass

    @profileset.command()
    async def background(self, ctx, *, link:str=None):
        """Définir l'image de fond du profil"""
        await self.profiles._set_background(ctx.author, link)
        await ctx.send(_("Profil de fond défini sur: ") + str(link))

    @profileset.command()
    async def description(self, ctx, *, description:str=None):
        """Définir la description du profil"""
        await self.profiles._set_description(ctx.author, description)
        await ctx.send(_("Description du profil définie sur: ") + str(description))

    @roles.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def add(self, ctx, role : discord.Role):
        """Ajoute un role a la liste des roles obtenables grâce à l'expérience."""
        await self.profiles._add_guild_role(ctx.guild, role.id)
        await ctx.send(_("Role configuré"))

    @roles.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def remove(self, ctx, role : discord.Role):
        """Supprime un role de la liste des roles obtenables grâce à l'expérience."""
        if role.id in await self.profiles._get_guild_roles(ctx.guild):
            await self.profiles._remove_guild_role(ctx.guild, role.id)
            await ctx.send(_("Role supprimé"))
        else:
            await ctx.send(_("Role inconnu dans la config"))

    @roles.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def move(self, ctx, role : discord.Role, position : int):
        """Permet de déplacer un role, modifiant l'expérience necessaire pour l'obtenir."""
        if role.id in await self.profiles._get_guild_roles(ctx.guild):
            await self.profiles._move_guild_role(ctx.guild, role.id, position-1)
            await ctx.send(_("Role déplacé"))
        else:
            await ctx.send(_("Role inconnu dans la config"))

    @roles.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def show(self, ctx):
        """Affiche la liste des roles dans l'ordre auquel ils sont obtenables."""
        emb = discord.Embed()
        emb.title = _("Liste des roles configurés pour le leveler de ce serveur.")
        emb.description= _("Garanti 100% presque pas bugué.")
        roles = await self.profiles._get_guild_roles(ctx.guild)
        counter = 1
        for x in roles:
            emb.add_field(name=counter, value=discord.utils.get(ctx.guild.roles, id=x).name)
            counter += 1
        await ctx.send(embed=emb)

    @whitelist.command(name="add")
    @checks.mod_or_permissions(manage_messages=True)
    async def _add(self, ctx, channel : discord.TextChannel = None):
        """Ajoute un channel, permettant aux utilisateurs de gagner de l'expérience lorsqu'ils parlent dans ce channel là."""
        if channel is None:
            channel = ctx.channel
        if channel.id not in await self.profiles._get_guild_channels(ctx.guild):
            await self.profiles._add_guild_channel(ctx.guild, channel.id)
            await ctx.send(_("Channel ajouté"))
        else:
            await ctx.send(_("Channel déjà enregistré"))

    @whitelist.command(name="toggle")
    @checks.mod_or_permissions(manage_messages=True)
    async def toggle(self, ctx):
        new = await self.profiles._toggle_whitelist(ctx.guild)
        await ctx.send(f"La whitelist est désormais {'activée.' if new else 'désactivée.'}")

    @whitelist.command(name="remove")
    @checks.mod_or_permissions(manage_messages=True)
    async def _remove(self, ctx, channel : discord.TextChannel = None):
        """Supprime un channel, les utilisateurs qui y parleront ne gagneront ainsi plus d'expérience."""
        if channel is None:
            channel = ctx.channel
        if channel.id not in await self.profiles._get_guild_channels(ctx.guild):
            await ctx.send(_("Ce channel n'est pas dans la liste configurée."))
        else:
            await self.profiles._remove_guild_channel(ctx.guild, channel.id)
            await ctx.send(_("Channel supprimé"))

    @whitelist.command(name="show")
    @checks.mod_or_permissions(manage_messages=True)
    async def _show(self, ctx):
        """Affiche la liste des channels configurés pour donner de l'expérience."""
        emb = discord.Embed()
        emb.title = _("Liste des channels autorisés a faire gagner de l'experience sur ce serveur.")
        emb.description = _("A une vache prés, c'pas une science exacte")
        channels = await self.profiles._get_guild_channels(ctx.guild)
        if not len(channels):
            return await ctx.send(_("Aucun channel configuré"))
        emb.add_field(name="Channels:", value="\n".join([ctx.guild.get_channel(x).mention for x in channels]))
        await ctx.send(embed=emb)


    @blacklist.command(name="add")
    @checks.mod_or_permissions(manage_messages=True)
    async def __add(self, ctx, channel : discord.TextChannel = None):
        """Ajoute un channel à ignorer dans le gain d'xp."""
        if channel is None:
            channel = ctx.channel
        if channel.id not in await self.profiles._get_guild_blchannels(ctx.guild):
            await self.profiles._add_guild_blacklist(ctx.guild, channel.id)
            await ctx.send(_("Channel ignoré"))
        else:
            await ctx.send(_("Channel déjà ignoré"))

    @blacklist.command(name="toggle")
    @checks.mod_or_permissions(manage_messages=True)
    async def _toggle(self, ctx):
        new = await self.profiles._toggle_blacklist(ctx.guild)
        await ctx.send(f"La blacklist est désormais {'activée.' if new else 'désactivée.'}")

    @blacklist.command(name="remove")
    @checks.mod_or_permissions(manage_messages=True)
    async def __remove(self, ctx, channel : discord.TextChannel = None):
        """Supprime un channel, les utilisateurs qui y parleront gagneront ainsi de l'expérience."""
        if channel is None:
            channel = ctx.channel
        if channel.id not in await self.profiles._get_guild_blchannels(ctx.guild):
            await ctx.send(_("Ce channel n'est pas dans la liste configurée."))
        else:
            await self.profiles._remove_guild_blacklist(ctx.guild, channel.id)
            await ctx.send(_("Channel supprimé"))

    @blacklist.command(name="show")
    @checks.mod_or_permissions(manage_messages=True)
    async def __show(self, ctx):
        """Affiche la liste des channels configurés pour être ignorés."""
        emb = discord.Embed()
        emb.title = _("Liste des channels non autorisés a faire gagner de l'experience sur ce serveur.")
        emb.description = _("A une vache prés, c'pas une science exacte")
        channels = await self.profiles._get_guild_blchannels(ctx.guild)
        if not len(channels):
            return await ctx.send(_("Aucun channel configuré"))
        emb.add_field(name="Channels:", value="\n".join([ctx.guild.get_channel(x).mention for x in channels]))
        await ctx.send(embed=emb)

    @levelerset.command()
    async def autoregister(self, ctx):
        """Bascule l'enregistrement automatique des utilisateurs"""
        if await self.profiles._get_auto_register(ctx.guild):
            await self.profiles._set_auto_register(ctx.guild, False)
            await ctx.send(_("Enregistrement automatique désactivé"))
        else:
            await self.profiles._set_auto_register(ctx.guild, True)
            await ctx.send(_("Enregistrement automatique activé"))

    @levelerset.command()
    async def cooldown(self, ctx, cooldown: float):
        """Définir le temps de recharge pour le gain xp, la valeur par défaut est 60 secondes"""
        await self.profiles._set_cooldown(ctx.guild, cooldown)
        await ctx.send(_("Le temps de recharge est réglé sur: ") + str(cooldown))

    @levelerset.command()
    @checks.is_owner()
    async def setlevel(self, ctx, level:int, member:discord.Member=None):
        """Définir un niveau de membres, principalement pour les tests"""
        if member is None:
            member = ctx.message.author
        await self.profiles._set_level(member, level)
        await ctx.send(member.name + _(" niveau réglé à ") + str(level))

    @levelerset.command()
    @checks.is_owner()
    async def setxp(self, ctx, xp:int, member:discord.Member=None):
        """définir un membre xp, principalement pour les tests"""
        if member is None:
            member = ctx.message.author
        await self.profiles._set_exp(member, xp)
        await ctx.send(member.name +_(" xp mis à ") + str(xp))

