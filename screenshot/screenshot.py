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
import random
import string
from io import BytesIO
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import discord
from redbot.core import app_commands, commands
from redbot.core.bot import Red


class Screenshot(commands.Cog):
    """Capture screenshots of websites."""

    __version__ = "0.0.2"
    __author__ = "Akai"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.key: Optional[str] = None

    async def cog_load(self):
        rapid_api = await self.bot.get_shared_api_tokens("rapid_api")
        rapid_api_key = rapid_api.get("api_key")
        if rapid_api_key is not None:
            self.key = rapid_api_key

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def detect_nsfw(self, image_bytes: bytes) -> Optional[int]:
        if not self.key:
            return 0
        url = "https://nsfw1.p.rapidapi.com/nsfw"
        headers = {
            "X-RapidAPI-Key": self.key,
            "X-RapidAPI-Host": "nsfw1.p.rapidapi.com",
        }

        payload = aiohttp.FormData()
        payload.add_field("image", image_bytes, content_type="multipart/form-data")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["response"]["nsfw"]

    @commands.hybrid_command(name="screenshot", aliases=["ss"])
    @app_commands.describe(
        site="The URL of the website to take a screenshot of.",
        width="Thumbnail width in pixels. Default: 600.",
        crop="Height of the original screenshot in pixels. Default: 1200.",
        max_age="Refresh the thumbnail if the cached image is older than this amount, in hours.",
        allow_jpg="Return a JPG instead of PNG format when possible.",
        png="Return a PNG format regardless of the resolution.",
        no_animate="Don't animate the resulting image, just return the final PNG.",
        full_page="Return an image containing the full page, not just the visible area.",
        wait="Wait for the specified number of seconds after the webpage has loaded before taking a screenshot.",
        viewport_width="Set the viewportWidth of the browser. Maximum value is 2400. Default: 1200.",
        iphone5="Emulate an iPhone 5.",
        iphone6="Emulate an iPhone 6.",
        iphone6plus="Emulate an iPhone 6 Plus.",
        iphone_x="Emulate an iPhone X.",
        galaxys5="Emulate a Galaxy S5.",
    )
    async def screenshot_command(
        self,
        ctx: commands.Context,
        site: str,
        width: Optional[int] = 600,
        crop: Optional[int] = 1200,
        max_age: Optional[int] = None,
        wait: Optional[int] = None,
        viewport_width: Optional[int] = 1200,
    ):
        """
        Capture a screenshot of a website.

        Parameters:
        - site: The URL of the website to take a screenshot of.
        - width: Thumbnail width in pixels. Default: 600.
        - crop: Height of the original screenshot in pixels. Default: 1200.
        - max_age: Refresh the thumbnail if the cached image is older than this amount, in hours.
        - wait: Wait for the specified number of seconds after the webpage has loaded before taking a screenshot.
        - viewport_width: Set the viewportWidth of the browser. Maximum value is 2400. Default: 1200.
        """
        parsed_url = urlparse(site)
        if all([parsed_url.scheme, parsed_url.netloc]):
            async with ctx.typing():
                url = f"https://image.thum.io/get/"
                url += f"width/{width}/"
                url += f"crop/{crop}/"
                if max_age:
                    url += f"maxAge/{max_age}/"

                if wait:
                    url += f"wait/{wait}/"
                if viewport_width:
                    url += f"viewportWidth/{viewport_width}/"

                url += site

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        image_bytes = await response.read()

                nsfw_score = await self.detect_nsfw(image_bytes)

                if nsfw_score is None:
                    return await ctx.send(
                        "Failed to detect the NSFW score of that image."
                    )

                if nsfw_score > 0.5:
                    await ctx.send(
                        "NSFW content detected. The screenshot cannot be displayed."
                    )
                else:
                    random_string = "".join(
                        random.choice(string.ascii_letters + string.digits)
                        for _ in range(10)
                    )
                    file = discord.File(
                        fp=BytesIO(image_bytes),
                        filename=f"screenshot-{random_string}.png",
                    )
                    embed = discord.Embed(
                        title=site, url=site, colour=await ctx.bot.get_embed_color(ctx)
                    )
                    embed.set_image(url=f"attachment://screenshot-{random_string}.png")
                    await ctx.send(file=file, embed=embed)
        else:
            await ctx.send("Invalid URL. Please provide a valid URL.")
