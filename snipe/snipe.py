"""
MIT License

Copyright (c) 2023-present Akai

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

from typing import Dict, Optional, Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from .cache import Messages

MAX_SNIPE_SIZE = 100  # Only 100 messages are cached per channel.


SnipeableChannel = Union[discord.TextChannel, discord.Thread, discord.VoiceChannel]


class Snipe(commands.Cog):
    """Snipe deleted and edited messages."""

    __version__ = "0.0.1"

    def __init__(self, bot: Red):
        self.config = Config.get_conf(self, identifier=747403406154)
        self.bot = bot
        self.toggles: Dict[discord.Guild, bool] = {}
        self.messages: Dict[SnipeableChannel, Messages] = {}
        self.config.register_guild(snipe=False)

    async def is_toggled(self, guild: discord.Guild) -> bool:
        toggle = self.toggles.get(guild)

        if toggle is None:
            toggle = await self.config.guild(guild).snipe()
            self.toggles[guild] = toggle

        return toggle

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if (
            message.author.bot
            or not message.guild
            or not isinstance(
                message.channel,
                (discord.TextChannel, discord.Thread, discord.VoiceChannel),
            )
            or not message.content
            or not await self.is_toggled(message.guild)
        ):
            return

        self.messages.setdefault(message.channel, Messages(maxsize=MAX_SNIPE_SIZE)).add(
            message
        )

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.group(invoke_without_command=True, aliases=["sn"])
    async def snipe(
        self,
        ctx: commands.GuildContext,
        index: int = 0,
        channel: Optional[SnipeableChannel] = None,
        author: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Snipe a message in the given channel."""

        if not isinstance(
            ctx.channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)
        ):
            return await ctx.reply(
                "You cannot snipe in this channel type.", mention_author=False
            )

        channel = ctx.channel if channel is None else channel

        messages = self.messages.get(channel)

        if messages is None:
            return await ctx.reply("There's nothing to snipe!", mention_author=False)

        message = messages.get(index, author)
        if message is None:
            return await ctx.reply("There's nothing to snipe!", mention_author=False)

        content = (
            message.content
            if len(message.content) < 4000
            else message.content[:4000] + "..."
        )
        description = (
            f"{content} ({discord.utils.format_dt(message.created_at, style='R')})"
        )
        embed = discord.Embed(
            description=description,
            colour=discord.Colour.dark_embed(),
            timestamp=message.created_at,
        )
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_author(
            name=message.author.display_name, icon_url=message.author.display_avatar
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def snipeset(
        self,
        ctx: commands.Context,
    ):
        """Set up sniping rules in the server."""

    @snipeset.command(name="toggle")
    async def snipeset_toggle(self, ctx: commands.GuildContext):
        """Toggle sniping in the server."""
        toggle = await self.config.guild(ctx.guild).snipe()

        await self.config.guild(ctx.guild).snipe.set(not toggle)
        self.toggles[ctx.guild] = not toggle

        await ctx.send(
            f"Sniping is now {'enabled' if not toggle else 'disabled'} in this server."
        )
