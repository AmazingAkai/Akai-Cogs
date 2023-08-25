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

from typing import Dict, List, Optional, Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.views import SimpleMenu

from .cache import DeletedMessages, EditedMessage, EditedMessages

MAX_SNIPE_SIZE = 100  # Only 100 messages are cached per channel.


SnipeableChannel = Union[discord.TextChannel, discord.Thread, discord.VoiceChannel]


class Snipe(commands.Cog):
    """Snipe deleted and edited messages."""

    __version__ = "0.0.1"

    def __init__(self, bot: Red):
        self.config = Config.get_conf(self, identifier=747403406154)
        self.bot = bot
        self.toggles: Dict[discord.Guild, bool] = {}
        self.deleted_messages: Dict[SnipeableChannel, DeletedMessages] = {}
        self.edited_messages: Dict[SnipeableChannel, EditedMessages] = {}
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

        self.deleted_messages.setdefault(
            message.channel, DeletedMessages(maxsize=MAX_SNIPE_SIZE)
        ).add(message)

    @commands.Cog.listener()
    async def on_message_edit(
        self, before: discord.Message, after: discord.Message
    ) -> None:
        if (
            before.author.bot
            or not before.guild
            or not isinstance(
                before.channel,
                (discord.TextChannel, discord.Thread, discord.VoiceChannel),
            )
            or not before.content
            or not before.content != after.content  # or before.content == after.content
            or not await self.is_toggled(before.guild)
        ):
            return

        self.edited_messages.setdefault(
            before.channel, EditedMessages(maxsize=MAX_SNIPE_SIZE)
        ).add(EditedMessage(before=before, after=after))

    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=["sn"])
    async def snipe(
        self,
        ctx: commands.GuildContext,
        index: int = 0,
        channel: Optional[SnipeableChannel] = None,
        author: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Snipe a deleted message in the given channel."""
        if ctx.invoked_subcommand is not None:
            return

        if not self.is_toggled(ctx.guild):
            return await ctx.send(
                f"Sniping is disabled in this server. To enable sniping, run `{ctx.clean_prefix}snipeset toggle`.",
                mention_author=False,
            )

        if not isinstance(
            ctx.channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)
        ):
            return await ctx.reply(
                "You cannot snipe in this channel type.", mention_author=False
            )

        channel = ctx.channel if channel is None else channel

        messages = self.deleted_messages.get(channel)

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
        embed.set_footer(
            text=f"Sniped by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar,
        )
        embed.set_author(
            name=message.author.display_name, icon_url=message.author.display_avatar
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.guild_only()
    @snipe.command(name="bulk", aliases=["list"])
    async def snipe_bulk(
        self,
        ctx: commands.GuildContext,
        channel: Optional[SnipeableChannel] = None,
        author: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Snipe all the deleted messages in the given channel."""

        if not self.is_toggled(ctx.guild):
            return await ctx.send(
                f"Sniping is disabled in this server. To enable sniping, run `{ctx.clean_prefix}snipeset toggle`.",
                mention_author=False,
            )

        if not isinstance(
            ctx.channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)
        ):
            return await ctx.reply(
                "You cannot snipe in this channel type.", mention_author=False
            )

        channel = ctx.channel if channel is None else channel

        messages = self.deleted_messages.get(channel)

        if messages is None:
            return await ctx.reply("There's nothing to snipe!", mention_author=False)

        filtered_messages = messages.get_bulk(author)
        if filtered_messages is None:
            return await ctx.reply("There's nothing to snipe!", mention_author=False)

        embeds: List[discord.Embed] = []

        for i, message in enumerate(filtered_messages):
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

            embed.set_author(
                name=message.author.display_name, icon_url=message.author.display_avatar
            )
            embed.set_footer(
                text=f"Sniped by {ctx.author.display_name} | Page {i + 1}/{len(filtered_messages)}",
                icon_url=ctx.author.display_avatar,
            )
            embeds.append(embed)

        pages = SimpleMenu(embeds, disable_after_timeout=True)  # type: ignore

        await pages.start(ctx)

    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=["esnipe", "esn"])
    async def editsnipe(
        self,
        ctx: commands.GuildContext,
        index: int = 0,
        channel: Optional[SnipeableChannel] = None,
        author: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Snipe an edited message in the given channel."""
        if ctx.invoked_subcommand is not None:
            return

        if not self.is_toggled(ctx.guild):
            return await ctx.send(
                f"Sniping is disabled in this server. To enable sniping, run `{ctx.clean_prefix}snipeset toggle`.",
                mention_author=False,
            )

        if not isinstance(
            ctx.channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)
        ):
            return await ctx.reply(
                "You cannot snipe in this channel type.", mention_author=False
            )

        channel = ctx.channel if channel is None else channel

        messages = self.edited_messages.get(channel)

        if messages is None:
            return await ctx.reply("There's nothing to snipe!", mention_author=False)

        message = messages.get(index, author)
        if message is None:
            return await ctx.reply("There's nothing to snipe!", mention_author=False)

        embed = discord.Embed(
            colour=discord.Colour.dark_embed(),
            timestamp=message.before.created_at,
        )

        embed.add_field(
            name="Before",
            value=message.before.content
            if len(message.before.content) <= 1024
            else message.before.content[:1021] + "...",
            inline=False,
        )
        embed.add_field(
            name="After",
            value=message.after.content
            if len(message.after.content) <= 1024
            else message.after.content[:1021] + "...",
            inline=False,
        )

        embed.set_footer(
            text=f"Sniped by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar,
        )
        embed.set_author(
            name=message.before.author.display_name,
            icon_url=message.before.author.display_avatar,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.guild_only()
    @editsnipe.command(name="bulk", aliases=["list"])
    async def editsnipe_bulk(
        self,
        ctx: commands.GuildContext,
        channel: Optional[SnipeableChannel] = None,
        author: Optional[Union[discord.Member, discord.User]] = None,
    ):
        """Snipe all the edited messages in the given channel."""

        if not self.is_toggled(ctx.guild):
            return await ctx.send(
                f"Sniping is disabled in this server. To enable sniping, run `{ctx.clean_prefix}snipeset toggle`.",
                mention_author=False,
            )

        if not isinstance(
            ctx.channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)
        ):
            return await ctx.reply(
                "You cannot snipe in this channel type.", mention_author=False
            )

        channel = ctx.channel if channel is None else channel

        messages = self.edited_messages.get(channel)

        if messages is None:
            return await ctx.reply("There's nothing to snipe!", mention_author=False)

        filtered_messages = messages.get_bulk(author)
        if filtered_messages is None:
            return await ctx.reply("There's nothing to snipe!", mention_author=False)

        embeds: List[discord.Embed] = []

        for i, message in enumerate(filtered_messages):
            embed = discord.Embed(
                colour=discord.Colour.dark_embed(),
                timestamp=message.before.created_at,
            )

            embed.add_field(
                name="Before",
                value=message.before.content
                if len(message.before.content) <= 1024
                else message.before.content[:1021] + "...",
                inline=False,
            )
            embed.add_field(
                name="After",
                value=message.after.content
                if len(message.after.content) <= 1024
                else message.after.content[:1021] + "...",
                inline=False,
            )

            embed.set_author(
                name=message.before.author.display_name,
                icon_url=message.before.author.display_avatar,
            )
            embed.set_footer(
                text=f"Sniped by {ctx.author.display_name} | Page {i + 1}/{len(filtered_messages)}",
                icon_url=ctx.author.display_avatar,
            )
            embeds.append(embed)

        pages = SimpleMenu(embeds, disable_after_timeout=True)  # type: ignore

        await pages.start(ctx)

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
