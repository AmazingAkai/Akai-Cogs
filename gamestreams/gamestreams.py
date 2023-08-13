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

from typing import Optional

import aiohttp
from redbot.cogs.streams import streams
from redbot.cogs.streams.streamtypes import TWITCH_BASE_URL, TwitchStream
from redbot.core import commands
from redbot.core.bot import Red

TWITCH_GAMES_ENDPOINT = TWITCH_BASE_URL + "/helix/games"


class GameStreams(commands.Cog):
    """Receive live announcements for new game streams."""

    __version__ = "0.0.1"
    __author__ = "Akai"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession

    @property
    def streams_cog(self) -> Optional[streams.Streams]:
        return self.bot.get_cog("Streams")  # type: ignore

    @commands.command(name="findtwitchstreams")
    async def find_twitch_streams(self, ctx: commands.Context, game: str) -> None:
        """Find all the ongoing twitch streams of a specific game."""

        if self.streams_cog is None:
            await ctx.send(
                f"Streams cog is currently not loaded. {' You can load the cog using `[p]load streams`' if await self.bot.is_owner(ctx.author) else ''}"
            )
            return

        await self.streams_cog.maybe_renew_twitch_bearer_token()
        token = (await self.bot.get_shared_api_tokens("twitch")).get("client_id")

        headers = {
            "Client-ID": token,
            "Authorization": f"Bearer {self.streams_cog.ttv_bearer_cache['access_token']}",
        }

        params = {
            "name": game,
            "first": 1,
        }

        async with self.session() as session:
            async with session.get(
                TWITCH_GAMES_ENDPOINT, headers=headers, params=params
            ) as response:
                data = await response.json()

                await ctx.send(data)
