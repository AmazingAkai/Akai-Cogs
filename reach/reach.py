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

from typing import Union

import discord
from redbot.core import Config, commands


class Reach(commands.Cog):
    """Shows the reach of roles in a channel"""

    __version__ = "1.0.0"
    __author__ = "Akai"

    def __init__(self, bot):
        self.config = Config.get_conf(self, identifier=696969696969)
        self.bot = bot
        default_global = {
            "arrow": "➡️",
        }
        self.config.register_global(**default_global)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.hybrid_group(invoke_without_command=True)
    @commands.guild_only()
    async def reach(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        *roles: Union[discord.Role, str],
    ):
        """Shows the reach of roles in a channel"""
        assert ctx.guild is not None

        if len(roles) == 0:
            await ctx.send("Please enter atleast one role to check reach of.")
            return

        arrow = await self.config.arrow()
        members = set()
        total_members = set()
        description = f"Channel: {channel.mention} `{channel.id}`\n\n"
        for role in roles:
            if isinstance(role, str):
                if "everyone" in role.lower():
                    for member in ctx.guild.default_role.members:
                        total_members.add(member)
                        if channel.permissions_for(member).read_messages:
                            members.add(member)
                    description += f"\n{arrow} @everyone members: {len(ctx.guild.default_role.members)} reach: {100 * len(members) / len(ctx.guild.default_role.members):.2f}%"
                elif "here" in role.lower():
                    for member in ctx.guild.members:
                        if member.status != discord.Status.offline:
                            total_members.add(member)
                            if channel.permissions_for(member).read_messages:
                                members.add(member)
                    description += f"\n{arrow} @here members: {len(total_members)} reach: {100 * len(members) / len(total_members):.2f}%"

                else:
                    await ctx.send("Invalid role passed.")
                    return
            else:
                for member in role.members:
                    total_members.add(member)
                    if channel.permissions_for(member).read_messages:
                        members.add(member)
                description += f"\n{arrow} {role.mention} `{role.id}` members: {len(role.members)} reach: {100 * len(role.members) / len(total_members):.2f}%"

        percent = 100 * len(members) / len(total_members)
        description += f"\nTotal reach: {len(members)} out of {len(total_members)} targeted members\nwhich represents {percent:.2f}%"

        embed = discord.Embed(
            title="**Roles Reach**", description=description, color=0x2B2D31
        )
        embed.set_footer(text="Run ';invite' to invite me!")

        await ctx.send(embed=embed)

    @reach.command()
    @commands.is_owner()
    async def setarrow(self, ctx: commands.Context, emoji: discord.Emoji):
        """Set a new arrow emoji for the reach command."""
        emote = f"<{'a' if emoji.animated else ''}:{emoji.name}:{emoji.id}>"
        await self.config.arrow.set(emote)
        await ctx.send("Done, updated the emoji.")
