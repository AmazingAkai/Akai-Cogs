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

from typing import Optional

import discord
from redbot.core import commands


class Device(commands.Cog):
    """Tells the device the user is using."""

    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def device(
        self, ctx: commands.Context, user: discord.Member = commands.Author
    ) -> None:
        """Displays the device user is using."""
        if user.bot:
            await ctx.send(
                embed=discord.Embed(
                    title="Ha! Bots don't have a physical device for you to check. But don't worry, all bots are safe and sound in the cloud, living their best virtual lives.",
                    color=0xFF0000,
                )
            )
            return
        devices = []
        if user.web_status != discord.Status.offline:
            devices.append("A Web 💻 device")
        if user.desktop_status != discord.Status.offline:
            devices.append("A Desktop 🖥️ device")
        if user.mobile_status != discord.Status.offline:
            devices.append("A Mobile 📱 device")
        if len(devices) == 0:
            await ctx.send(
                embed=discord.Embed(
                    title=f"{user.name} is offline on all devices.", color=0xFF0000
                )
            )
            return
        deviceString = (
            devices[0]
            if len(devices) <= 1
            else ", ".join(devices[:-1]) + " and " + devices[-1]
        )
        embed = discord.Embed(
            title=f"{user.name} is using {deviceString}.", color=0x00FF00
        )
        await ctx.send(embed=embed)
