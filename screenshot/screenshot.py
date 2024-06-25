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
import io
import time
from urllib.parse import urlparse

import discord
from redbot.core import app_commands, commands
from redbot.core.bot import Red
from selenium import webdriver
from selenium.webdriver.firefox import options, service
from webdriver_manager.firefox import GeckoDriverManager

OPTIONS = options.Options()
OPTIONS.add_argument("--headless")
OPTIONS.add_argument("--window-size=1280x1024")
OPTIONS.add_argument("--hide-scrollbars")


class Screenshot(commands.Cog):
    """Capture screenshots of websites."""

    __version__ = "0.1.0"
    __author__ = "Akai"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.driver = webdriver.Firefox(
            service=service.Service(executable_path=GeckoDriverManager().install()),
            options=OPTIONS,
        )

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def cog_unload(self) -> None:
        self.driver.quit()

    def get_screenshot(self, url: str) -> discord.File:
        self.driver.get(url)
        time.sleep(1)
        png = self.driver.get_screenshot_as_png()

        with io.BytesIO(png) as image:
            return discord.File(image, filename="screenshot.png")

    @commands.is_owner()
    @commands.hybrid_command(name="screenshot", aliases=["ss"])
    @app_commands.describe(
        site="The URL of the website to take a screenshot of.",
    )
    async def screenshot(
        self,
        ctx: commands.Context,
        site: str,
    ) -> None:
        """
        Capture a screenshot of a website.

        Parameters:
        - site: The URL of the website to take a screenshot of.
        """
        parsed_url = urlparse(site)

        if not all([parsed_url.scheme, parsed_url.netloc]):
            await ctx.send("Invalid URL. Please provide a valid URL.")
            return
        elif parsed_url.scheme != "https":
            await ctx.send("Invalid URL. Please provide a secure URL.")
            return

        async with ctx.typing():
            file = await asyncio.to_thread(self.get_screenshot, url=site)

        color = await ctx.bot.get_embed_color(ctx)

        embed = discord.Embed(
            title=site,
            url=site,
            color=color,
        )
        embed.set_image(url="attachment://screenshot.png")

        await ctx.send(embed=embed, file=file)
