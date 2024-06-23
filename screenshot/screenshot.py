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

from typing import Optional
from urllib.parse import urlparse

import aiohttp
import discord
from redbot.core import app_commands, commands
from redbot.core.bot import Red


class Screenshot(commands.Cog):
    """Capture screenshots of websites."""

    __version__ = "0.0.3"
    __author__ = "Akai"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def cog_unload(self) -> None:
        await self.session.close()

    @commands.hybrid_command(name="screenshot", aliases=["ss"])
    @app_commands.describe(
        site="The URL of the website to take a screenshot of.",
        width="Thumbnail width in pixels.",
        crop="Height of the original screenshot in pixels.",
        max_age="Refresh the thumbnail if the cached image is older than this amount, in hours.",
        wait="Wait for the specified number of seconds after the webpage has loaded before taking a screenshot.",
        viewport_width="Set the viewportWidth of the browser. Maximum value is 2400.",
    )
    async def screenshot(
        self,
        ctx: commands.Context,
        site: str,
        width: Optional[int] = None,
        crop: Optional[int] = None,
        viewport_width: Optional[int] = None,
        max_age: Optional[int] = None,
        wait: Optional[int] = None,
    ) -> None:
        """
        Capture a screenshot of a website.

        Parameters:
        - site: The URL of the website to take a screenshot of.
        - width: Thumbnail width in pixels.
        - crop: Height of the original screenshot in pixels.
        - max_age: Refresh the thumbnail if the cached image is older than this amount, in hours.
        - wait: Wait for the specified number of seconds after the webpage has loaded before taking a screenshot.
        - viewport_width: Set the viewportWidth of the browser. Maximum value is 2400.
        """
        parsed_url = urlparse(site)

        if not all([parsed_url.scheme, parsed_url.netloc]):
            await ctx.send("Invalid URL. Please provide a valid URL.")
            return

        url = "https://image.thum.io/get/"
        if width:
            url += f"width/{width}/"
        if crop:
            url += f"crop/{crop}/"
        if max_age:
            url += f"maxAge/{max_age}/"
        if wait:
            url += f"wait/{wait}/"
        if viewport_width:
            url += f"viewportWidth/{viewport_width}/"
        url += f"{site}"

        async with self.session.get(url) as response:
            fp = await response.read()

        file = discord.File(fp, filename="screenshot.png")

        color = await ctx.bot.get_embed_color(ctx)

        embed = discord.Embed(
            title=site,
            url=site,
            color=color,
        )
        embed.set_image(url="attachment://screenshot.png")

        await ctx.send(embed=embed, file=file)
