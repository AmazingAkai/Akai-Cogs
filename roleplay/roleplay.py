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
from typing import Optional, Union

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red

from .core import ACTIONS, NEKOS

log = logging.getLogger("red.akaicogs.roleplay")


class RolePlay(commands.Cog):
    """The Roleplay cog is a Discord bot module that provides commands for immersive and engaging roleplaying activities."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot: Red, command: Optional[commands.Command]):
        self.original_hug_command = command

        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        if self.original_hug_command is not None:
            self.bot.add_command(self.original_hug_command)
        asyncio.create_task(self.session.close())

    __version__ = "0.2"
    __author__ = "MAX, Akai"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def send_embed(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]],
        action: str,
    ):
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

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def baka(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Baka baka baka!"""
        await self.send_embed(ctx, user, "baka")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def cry(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Cry!"""
        await self.send_embed(ctx, user, "cry")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def cuddle(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Cuddle a user!"""
        await self.send_embed(ctx, user, "cuddle")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def dance(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Dance!"""
        await self.send_embed(ctx, user, "dance")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def feed(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Feeds a user!"""
        await self.send_embed(ctx, user, "feed")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def hug(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Hugs a user!"""
        await self.send_embed(ctx, user, "hug")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def kiss(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Kiss a user!"""
        await self.send_embed(ctx, user, "kiss")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def laugh(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Laugh at someone!"""
        await self.send_embed(ctx, user, "laugh")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def pat(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Pats a user!"""
        await self.send_embed(ctx, user, "pat")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def poke(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Poke a user!"""
        await self.send_embed(ctx, user, "poke")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def slap(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Slap a user!"""
        await self.send_embed(ctx, user, "slap")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def smile(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Smile!"""
        await self.send_embed(ctx, user, "smile")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def smug(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Smugs at someone!"""
        await self.send_embed(ctx, user, "smug")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def tickle(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Tickle a user!"""
        await self.send_embed(ctx, user, "tickle")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def wave(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Waves!"""
        await self.send_embed(ctx, user, "wave")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def bite(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Bite a user!"""
        await self.send_embed(ctx, user, "bite")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def blush(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Blushes!"""
        await self.send_embed(ctx, user, "blush")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def bored(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """You're bored!"""
        await self.send_embed(ctx, user, "bored")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def facepalm(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Facepalm a user!"""
        await self.send_embed(ctx, user, "facepalm")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def happy(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Share your happiness with a user!"""
        await self.send_embed(ctx, user, "happy")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def highfive(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Highfive a user!"""
        await self.send_embed(ctx, user, "highfive")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def pout(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Pout a user!"""
        await self.send_embed(ctx, user, "pout")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def shrug(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Shrugs a user!"""
        await self.send_embed(ctx, user, "shrug")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def sleep(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Sleep zzzz!"""
        await self.send_embed(ctx, user, "sleep")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def stare(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Stares at a user!"""
        await self.send_embed(ctx, user, "stare")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def think(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Thinking!"""
        await self.send_embed(ctx, user, "think")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def thumbsup(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Thumbsup!"""
        await self.send_embed(ctx, user, "thumbsup")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def wink(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Winks at a user!"""
        await self.send_embed(ctx, user, "wink")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["handholding"])
    async def handhold(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Handhold a user!"""
        await self.send_embed(ctx, user, "handhold")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command(aliases=["kicks"])
    async def rkick(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Kick a user!"""
        await self.send_embed(ctx, user, "kick")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def punch(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Punch a user!"""
        await self.send_embed(ctx, user, "punch")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def shoot(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Shoot a user!"""
        await self.send_embed(ctx, user, "shoot")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def yeet(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Yeet a user far far away."""
        await self.send_embed(ctx, user, "yeet")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def nod(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Nods a user."""
        await self.send_embed(ctx, user, "nod")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def nope(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Say nope to a user."""
        await self.send_embed(ctx, user, "nope")

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.command()
    async def nom(
        self,
        ctx: commands.Context,
        user: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Nom nom a user."""
        await self.send_embed(ctx, user, "nom")
