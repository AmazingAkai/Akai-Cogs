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


import discord
from redbot.core import app_commands, commands
from redbot.core.bot import Red


class Screenshot(commands.Cog):
    """Capture screenshots of websites."""

    __version__ = "0.0.3"
    __author__ = "Akai"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.hybrid_command(name="screenshot", aliases=["ss"])
    @app_commands.describe(
        site="The URL of the website to take a screenshot of.",
        width="Thumbnail width in pixels. Default: 600.",
        crop="Height of the original screenshot in pixels. Default: 1200.",
        max_age="Refresh the thumbnail if the cached image is older than this amount, in hours. Default: 12.",
        wait="Wait for the specified number of seconds after the webpage has loaded before taking a screenshot. Default: 0.",
        viewport_width="Set the viewportWidth of the browser. Maximum value is 2400. Default: 1200.",
    )
    async def screenshot(
        self,
        ctx: commands.Context,
        site: str,
        width: int = 600,
        crop: int = 1200,
        max_age: Optional[int] = 12,
        wait: Optional[int] = 0,
        viewport_width: int = 1200,
    ) -> None:
        """
        Capture a screenshot of a website.

        Parameters:
        - site: The URL of the website to take a screenshot of.
        - width: Thumbnail width in pixels. Default: 600.
        - crop: Height of the original screenshot in pixels. Default: 1200.
        - max_age: Refresh the thumbnail if the cached image is older than this amount, in hours. Default: 12.
        - wait: Wait for the specified number of seconds after the webpage has loaded before taking a screenshot. Default: 0.
        - viewport_width: Set the viewportWidth of the browser. Maximum value is 2400. Default: 1200.
        """
        parsed_url = urlparse(site)

        if not all([parsed_url.scheme, parsed_url.netloc]):
            await ctx.send("Invalid URL. Please provide a valid URL.")
            return

        url = (
            "https://image.thum.io/get/"
            f"width/{width}/"
            f"crop/{crop}/"
            f"maxAge/{max_age}/"
            f"wait/{wait}/"
            f"viewportWidth/{viewport_width}/"
            f"{site}"
        )

        color = await ctx.bot.get_embed_color(ctx)

        embed = discord.Embed(
            title=site,
            url=site,
            color=color,
        )
        embed.set_image(url=url)

        await ctx.send(embed=embed)
