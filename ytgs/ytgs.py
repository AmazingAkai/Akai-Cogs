import asyncio
from typing import Annotated, Any, Dict, List

import aiohttp
import discord
import youtube_dl
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.views import SimpleMenu


class GameChannelConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://www.youtube.com/channel/{argument}/letsplay"
            ) as response:
                if response.status == 404:
                    raise commands.BadArgument(
                        f"Invalid or inaccessible channel ID: {argument}"
                    )

                return argument


class Stream:
    def __init__(self, stream_data: Dict[str, Any]):
        self._type = stream_data["_type"]
        self.ie_key = stream_data["ie_key"]
        self.id = stream_data["id"]
        self.url = stream_data["url"]
        self.title = stream_data["title"]
        self.description = stream_data["description"]
        self.duration = stream_data["duration"]
        self.view_count = stream_data["view_count"]
        self.uploader = stream_data["uploader"]

    def make_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            url=f"https://www.youtube.com/watch?v={self.id}",
            description=self.description
            if self.description
            else "No description available.",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Uploader", value=self.uploader, inline=True)
        embed.add_field(
            name="View Count",
            value=f"{int(self.view_count): ,}" if self.view_count else "Not available",
            inline=True,
        )
        embed.add_field(
            name="Duration",
            value=self.duration if self.duration else "Not available",
            inline=True,
        )
        return embed


class YTGS(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.group()
    async def ytgs(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ytgs.command()
    async def search(
        self,
        ctx: commands.Context,
        channel_id: Annotated[str, GameChannelConverter],
    ):
        streams = await self.get_streams(channel_id)

        if streams:
            embeds: List[discord.Embed] = []

            for i, stream in enumerate(streams):
                embed = stream.make_embed()
                embed.set_footer(
                    text=f"Page {i + 1}/{len(streams)}",
                    icon_url=ctx.guild.icon or self.bot.user.display_avatar,  # type: ignore
                )
                embeds.append(embed)

            pages = SimpleMenu(embeds, disable_after_timeout=True)  # type: ignore

            await pages.start(ctx)
        else:
            await ctx.send("No streams found for this channel.")

    async def get_streams(self, channel_id: str) -> List[Stream]:
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "force_generic_extractor": True,
            "force_title": True,
            "cachedir": False,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info = await asyncio.to_thread(
                    ydl.extract_info,
                    url=f"https://www.youtube.com/channel/{channel_id}/live",
                    download=False,
                )
                if isinstance(info, dict) and "entries" in info:
                    return [Stream(entry) for entry in info["entries"]]
            except:
                return []

        return []
