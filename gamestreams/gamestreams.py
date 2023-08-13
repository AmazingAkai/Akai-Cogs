"""
MIT License

Copyright (c) 2023-present AmazingAkai

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
from __future__ import annotations

from typing import List, Optional

import aiohttp
import discord
from redbot.cogs.streams import streams
from redbot.cogs.streams.streamtypes import TWITCH_BASE_URL, TWITCH_STREAMS_ENDPOINT
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.views import SimpleMenu

TWITCH_GAMES_ENDPOINT = TWITCH_BASE_URL + "/helix/games"


class FetchError(Exception):
    """Custom exception for fetching errors."""


class GameNotFoundError(FetchError):
    """Exception for game not found errors."""


class StreamFetchError(FetchError):
    """Exception for stream fetch errors."""


class Stream:
    def __init__(self, data: dict) -> None:
        self.data = data

    def make_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.data["title"],
            description=f"**{self.data['user_name']}** is streaming **{self.data['game_name']}**",
            url=f"https://twitch.tv/{self.data['user_login']}",
            color=discord.Color.purple(),
        )
        embed.set_image(url=self.data["thumbnail_url"].format(width=1280, height=720))
        embed.add_field(
            name="Viewer Count",
            value=f"{self.data['viewer_count']} viewers",
            inline=True,
        )
        embed.add_field(name="Language", value=self.data["language"], inline=True)
        embed.add_field(name="Started At", value=self.data["started_at"], inline=True)
        if self.data["tags"]:
            embed.add_field(
                name="Tags", value=", ".join(self.data["tags"]), inline=False
            )
        return embed


class Game:
    def __init__(self, data: dict, headers: dict) -> None:
        self.data = data
        self.headers = headers

    def make_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.data["name"],
            description=self.data["summary"],
            url=f"https://www.twitch.tv/directory/game/{self.data['name']}",
            color=discord.Color.purple(),
        )
        embed.set_thumbnail(url=self.data["box_art_url"].format(width=285, height=380))
        return embed

    async def fetch_streams(self) -> List[Stream]:
        streams = []

        async with aiohttp.ClientSession() as session:
            async with session.get(
                TWITCH_STREAMS_ENDPOINT,
                headers=self.headers,
                params={"game_id": self.data["id"], "first": 100},
            ) as response:
                if response.status != 200:
                    raise StreamFetchError(
                        f"Error {response.status} was raised while fetching streams."
                    )

                data = await response.json()
                for stream_data in data.get("data", []):
                    stream = Stream(stream_data)
                    streams.append(stream)

        return streams


class GameStreams(commands.Cog):
    """Receive live announcements for new game streams."""

    __version__ = "0.0.1"
    __author__ = "Akai"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    @property
    def streams_cog(self) -> Optional[streams.Streams]:
        return self.bot.get_cog("Streams")  # type: ignore

    async def fetch_game(self, game_name: str, headers: dict) -> Game:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                TWITCH_GAMES_ENDPOINT,
                headers=headers,
                params={"name": game_name, "first": 1},
            ) as response:
                if response.status == 401:
                    raise FetchError(
                        "Failed to fetch that game, make sure to set proper credentials. Check `[p]streamset twitchtoken` for more info."
                    )

                data = await response.json()
                games_data = data["data"]
                if not games_data:
                    raise GameNotFoundError("That game does not exist on Twitch.")

                return Game(games_data[0], headers)

    @commands.command(name="findtwitchstreams")
    async def find_twitch_streams(self, ctx: commands.Context, game_name: str) -> None:
        if self.streams_cog is None:
            await ctx.send(
                f"Streams cog is currently not loaded. {' You can load the cog using `[p]load streams`' if await self.bot.is_owner(ctx.author) else ''}"
            )
            return

        await self.streams_cog.maybe_renew_twitch_bearer_token()
        token = (await self.bot.get_shared_api_tokens("twitch")).get("client_id")

        if token is None:
            await ctx.send(
                "The Twitch Client ID is not set. Please read `;streamset twitchtoken`."
            )
            return

        access_token = self.streams_cog.ttv_bearer_cache.get("access_token")
        if access_token is None:
            await ctx.send("Failed to fetch the access token for Twitch API.")
            return

        headers = {
            "Client-ID": token,
            "Authorization": f"Bearer {access_token}",
        }

        try:
            game = await self.fetch_game(game_name, headers)
        except Exception as error:
            await ctx.send(str(error))
            return

        try:
            streams = await game.fetch_streams()
        except StreamFetchError as error:
            await ctx.send(str(error))
            return

        if not streams:
            await ctx.send("No streams found for this game.")
            return

        embeds: List[discord.Embed] = []

        for stream in streams:
            embed = stream.make_embed()
            embeds.append(embed)

        pages = SimpleMenu(embeds, disable_after_timeout=True)

        await pages.start(ctx)
