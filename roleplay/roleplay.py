"""
MIT License

Copyright (c) 2022-present AmazingAkai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import asyncio
import logging
from typing import Optional

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number

from .core import ACTIONS, NEKOS

log = logging.getLogger("red.akaicogs.roleplay")


class RolePlay(commands.Cog):
    """The Roleplay cog is a Discord bot module that provides commands for immersive and engaging roleplaying activities."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    __version__ = "0.2"
    __author__ = "MAX, Akai"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def get_embed(self, ctx, user, action: str):
        async with self.session.get(NEKOS + action) as response:
            if response.status != 200:
                return await ctx.send(
                    "Something went wrong while trying to contact API."
                )
            data = await response.json()

        action_fmt = ACTIONS.get(action, action)
        embed = discord.Embed(
            colour=0xED80A7,
        )
        embed.set_image(url=data["results"][0]["url"])
        content = f"> ***{ctx.author.name}** {action_fmt} {f'**{user.mention}**' if user else 'themselves!'}*"

        try:
            await ctx.send(content=content, embed=embed)
        except discord.HTTPException:
            await ctx.send(
                "Something went wrong while posting. Check your console for details."
            )
            log.exception(f"Command '{ctx.command.name}' failed to post:")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def baka(self, ctx, user: Optional[discord.Member] = None):
        """Baka baka baka!"""
        await self.get_embed(ctx, user, "baka")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cry(self, ctx, user: Optional[discord.Member] = None):
        """Cry!"""
        await self.get_embed(ctx, user, "cry")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def cuddle(self, ctx, user: Optional[discord.Member] = None):
        """Cuddle a user!"""
        await self.get_embed(ctx, user, "cuddle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def dance(self, ctx, user: Optional[discord.Member] = None):
        """Dance!"""
        await self.get_embed(ctx, user, "dance")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def feed(self, ctx, user: Optional[discord.Member] = None):
        """Feeds a user!"""
        await self.get_embed(ctx, user, "feed")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def hug(self, ctx, user: Optional[discord.Member] = None):
        """Hugs a user!"""
        await self.get_embed(ctx, user, "hug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def kiss(self, ctx, user: Optional[discord.Member] = None):
        """Kiss a user!"""
        await self.get_embed(ctx, user, "kiss")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def laugh(self, ctx, user: Optional[discord.Member] = None):
        """Laugh at someone!"""
        await self.get_embed(ctx, user, "laugh")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pat(self, ctx, user: Optional[discord.Member] = None):
        """Pats a user!"""
        await self.get_embed(ctx, user, "pat")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def poke(self, ctx, user: Optional[discord.Member] = None):
        """Poke a user!"""
        await self.get_embed(ctx, user, "poke")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def slap(self, ctx, user: Optional[discord.Member] = None):
        """Slap a user!"""
        await self.get_embed(ctx, user, "slap")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smile(self, ctx, user: Optional[discord.Member] = None):
        """Smile!"""
        await self.get_embed(ctx, user, "smile")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def smug(self, ctx, user: Optional[discord.Member] = None):
        """Smugs at someone!"""
        await self.get_embed(ctx, user, "smug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tickle(self, ctx, user: Optional[discord.Member] = None):
        """Tickle a user!"""
        await self.get_embed(ctx, user, "tickle")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wave(self, ctx, user: Optional[discord.Member] = None):
        """Waves!"""
        await self.get_embed(ctx, user, "wave")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bite(self, ctx, user: Optional[discord.Member] = None):
        """Bite a user!"""
        await self.get_embed(ctx, user, "bite")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def blush(self, ctx, user: Optional[discord.Member] = None):
        """Blushes!"""
        await self.get_embed(ctx, user, "blush")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def bored(self, ctx, user: Optional[discord.Member] = None):
        """You're bored!"""
        await self.get_embed(ctx, user, "bored")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def facepalm(self, ctx, user: Optional[discord.Member] = None):
        """Facepalm a user!"""
        await self.get_embed(ctx, user, "facepalm")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def happy(self, ctx, user: Optional[discord.Member] = None):
        """Share your happiness with a user!"""
        await self.get_embed(ctx, user, "happy")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def highfive(self, ctx, user: Optional[discord.Member] = None):
        """Highfive a user!"""
        await self.get_embed(ctx, user, "highfive")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def pout(self, ctx, user: Optional[discord.Member] = None):
        """Pout a user!"""
        await self.get_embed(ctx, user, "pout")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shrug(self, ctx, user: Optional[discord.Member] = None):
        """Shrugs a user!"""
        await self.get_embed(ctx, user, "shrug")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def sleep(self, ctx, user: Optional[discord.Member] = None):
        """Sleep zzzz!"""
        await self.get_embed(ctx, user, "sleep")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def stare(self, ctx, user: Optional[discord.Member] = None):
        """Stares at a user!"""
        await self.get_embed(ctx, user, "stare")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def think(self, ctx, user: Optional[discord.Member] = None):
        """Thinking!"""
        await self.get_embed(ctx, user, "think")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def thumbsup(self, ctx, user: Optional[discord.Member] = None):
        """Thumbsup!"""
        await self.get_embed(ctx, user, "thumbsup")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def wink(self, ctx, user: Optional[discord.Member] = None):
        """Winks at a user!"""
        await self.get_embed(ctx, user, "wink")

    @commands.command(aliases=["handholding"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def handhold(self, ctx, user: Optional[discord.Member] = None):
        """Handhold a user!"""
        await self.get_embed(ctx, user, "handhold")

    @commands.command(aliases=["kicks"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def vkick(self, ctx, user: Optional[discord.Member] = None):
        """Kick a user!"""
        await self.get_embed(ctx, user, "kick")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def punch(self, ctx, user: Optional[discord.Member] = None):
        """Punch a user!"""
        await self.get_embed(ctx, user, "punch")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def shoot(self, ctx, user: Optional[discord.Member] = None):
        """Shoot a user!"""
        await self.get_embed(ctx, user, "shoot")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def yeet(self, ctx, user: Optional[discord.Member] = None):
        """Yeet a user far far away."""
        await self.get_embed(ctx, user, "yeet")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def nod(self, ctx, user: Optional[discord.Member] = None):
        """Nods a user."""
        await self.get_embed(ctx, user, "nod")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def nope(self, ctx, user: Optional[discord.Member] = None):
        """Say nope to a user."""
        await self.get_embed(ctx, user, "nope")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def nom(self, ctx, user: Optional[discord.Member] = None):
        """Nom nom a user."""
        await self.get_embed(ctx, user, "nom")
