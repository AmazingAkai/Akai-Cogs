from __future__ import annotations

import asyncio
import datetime
import time
from typing import Any, Dict, List, Optional

import aiohttp
import discord
from iso639 import NonExistentLanguageError, to_name
from redbot.cogs.streams.streamtypes import TWITCH_STREAMS_ENDPOINT, rnd

from .exceptions import StreamFetchError


class TwitchStream:
    def __init__(self, game: TwitchGame, data: dict) -> None:
        self.game = game
        self.data = data

        self.id: int = int(data["id"])
        self.title: str = data["title"]
        self.user_name: str = data["user_name"]
        self.user_login: str = data["user_login"]
        self.game_name: str = data["game_name"]
        self.image: str = data["thumbnail_url"].format(width=1920, height=1080)
        self.viewer_count: int = data["viewer_count"]

        try:
            self.language: str = to_name(data["language"])
        except NonExistentLanguageError:
            self.language: str = data["language"]

        self.started_at: datetime.datetime = datetime.datetime.strptime(
            data["started_at"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=datetime.timezone.utc)
        self.is_mature: bool = data["is_mature"]
        self.tags: List[str] = data["tags"]

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: TwitchStream) -> bool:
        return self.id == other.id

    def make_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=f"**{self.user_name}** is streaming **{self.game_name}**",
            url=f"https://twitch.tv/{self.user_login}",
            color=discord.Color.purple(),
        )

        embed.set_image(url=rnd(self.image))
        embed.set_thumbnail(url=self.game.image)

        embed.add_field(
            name="Viewer Count",
            value=f"{self.viewer_count} viewers",
            inline=False,
        )
        embed.add_field(name="Language", value=self.language, inline=False)
        embed.add_field(
            name="Started",
            value=f"{discord.utils.format_dt(self.started_at, style='R')} ({discord.utils.format_dt(self.started_at)})",
            inline=False,
        )
        embed.add_field(
            name="Is Adult Stream?",
            value="Yes" if self.is_mature else "No",
            inline=False,
        )
        if self.tags:
            embed.add_field(name="Tags", value=", ".join(self.tags), inline=False)
        return embed


class TwitchGame:
    _rate_limit_resets = set()
    _rate_limit_remaining = 800  # Assuming an initial limit of 800 requests per minute

    def __init__(self, data: dict, headers: dict) -> None:
        self.data = data
        self.headers = headers

        self.name = self.data["name"]
        self.id: int = int(data["id"])
        self.image: str = data["box_art_url"].format(width=180, height=180)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: TwitchGame) -> bool:
        return self.id == other.id

    async def wait_for_rate_limit_reset(self) -> None:
        """Check rate limits in response header and ensure we're following them.

        From python-twitch-client and adapted to asyncio from Trusty-cogs:
        https://github.com/tsifrer/python-twitch-client/blob/master/twitch/helix/base.py
        https://github.com/TrustyJAID/Trusty-cogs/blob/master/twitch/twitch_api.py
        """
        current_time = int(time.time())
        self._rate_limit_resets = {
            x for x in self._rate_limit_resets if x > current_time
        }

        if self._rate_limit_remaining == 0:
            if self._rate_limit_resets:
                reset_time = next(iter(self._rate_limit_resets))
                wait_time = reset_time - current_time + 0.1
                await asyncio.sleep(wait_time)

    async def fetch_streams(self, cursor: Optional[str] = None) -> List[TwitchStream]:
        streams: List[TwitchStream] = []

        await self.wait_for_rate_limit_reset()

        async with aiohttp.ClientSession() as session:
            params: Dict[str, Any] = {"game_id": self.id, "first": 100, "type": "live"}
            if cursor:
                params["after"] = cursor

            async with session.get(
                TWITCH_STREAMS_ENDPOINT,
                headers=self.headers,
                params=params,
            ) as response:
                if response.status == 429:
                    reset = response.headers.get("Ratelimit-Reset")
                    if reset:
                        self._rate_limit_resets.add(int(reset))
                    await self.wait_for_rate_limit_reset()

                    # Retry the request with the same cursor
                    return await self.fetch_streams(cursor=cursor)

                if response.status != 200:
                    raise StreamFetchError(
                        f"Error {response.status} was raised while fetching streams."
                    )

                data = await response.json()
                for stream_data in data.get("data", []):
                    stream = TwitchStream(self, stream_data)
                    streams.append(stream)

                # Check if there's more data to fetch
                next_cursor = data.get("pagination", {}).get("cursor")
                if next_cursor:
                    # Recursively fetch more streams with the next cursor
                    more_streams = await self.fetch_streams(cursor=next_cursor)
                    streams.extend(more_streams)

            remaining = response.headers.get("Ratelimit-Remaining")
            if remaining:
                self._rate_limit_remaining = int(remaining)

            reset = response.headers.get("Ratelimit-Reset")
            if reset:
                self._rate_limit_resets.add(int(reset))

        return sorted(streams, key=lambda stream: stream.viewer_count, reverse=True)


class YouTubeStream:
    def __init__(self, data: dict):
        self.video_id: str = data["id"]
        self.title: str = data["snippet"]["title"]
        self.channel_name: str = data["snippet"]["channelTitle"]
        self.thumbnail_url: str = data["snippet"]["thumbnails"]["meduim"]["url"]
        self.start_time: datetime.datetime = datetime.datetime.strptime(
            data["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
        )

    def make_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=f"Live stream by **{self.channel_name}**",
            url=f"https://www.youtube.com/watch?v={self.video_id}",
            color=discord.Color.red(),
        )

        embed.set_image(url=rnd(self.thumbnail_url))
        embed.add_field(
            name="Start Time",
            value=self.start_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            inline=False,
        )

        return embed

    @staticmethod
    async def fetch_streams_for_game(
        api_key: str, game_name: str, page_token: Optional[str] = None
    ) -> List[YouTubeStream]:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "eventType": "live",
            "type": "video",
            "q": game_name,
            "key": api_key,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token

        live_streams: List[YouTubeStream] = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    response_json = await response.json()
                    if "items" in response_json:
                        for item in response_json["items"]:
                            live_stream_data = {
                                "id": item["id"]["videoId"],
                                "snippet": item["snippet"],
                            }
                            live_stream = YouTubeStream(live_stream_data)
                            live_streams.append(live_stream)

                    # Check if there's a next page
                    if "nextPageToken" in response_json:
                        next_page_token = response_json["nextPageToken"]
                        # Recursively call the function to fetch the next page
                        more_streams = await YouTubeStream.fetch_streams_for_game(
                            api_key, game_name, page_token=next_page_token
                        )
                        live_streams.extend(more_streams)

        except aiohttp.ClientError as e:
            print("Error:", e)

        return live_streams
