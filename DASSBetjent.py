import NPST_utils

import aiohttp
import logging
import discord
import json


def command(name):
    def wrapper(func):
        func.command_info = {
            "name": name
        }
        return func
    return wrapper


class DASSBetjent(discord.Client):
    def __init__(self, prefix="!", admin_prefix="+"):
        super().__init__()

        self.http_session = None
        self.npst_token = None

        self.admin_prefix = admin_prefix
        self.prefix = prefix

        self.logger = logging.getLogger("DASSBetjent")
        self.logger.debug("Initializing bot...")

        self.cryptobin_channels = []
        self.commands = {}

        self.event(self.on_ready)
        self.event(self.on_message)
        self.event(self.on_message_edit)

    async def api_request(self, path, method="GET"):
        full_path = f"https://dass.npst.no/.netlify/functions/{path}"
        return json.loads(await (await self.http_session.request(method, full_path, headers={
            "authorization": f"Bearer {self.npst_token}",
            "credentials": "include",
            "referrer": "https://dass.npst.no/",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "mode": "cors",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        })).text())["result"]

    async def on_ready(self):
        self.register_commands()

        for guild in await self.fetch_guilds():
            guild: discord.Guild
            for channel in await guild.fetch_channels():
                if type(channel) is discord.TextChannel:
                    channel: discord.TextChannel
                    if channel.name.lower() == "cryptobin":
                        self.cryptobin_channels.append(channel.id)

        self.logger.info(f"Bot started as {self.user}")

        self.http_session = aiohttp.ClientSession()

    async def on_message(self, msg):
        if type(msg.channel) is discord.DMChannel:
            self.logger.info(f"DMChannel/{msg.channel.recipient.name} {msg.author}: {msg.content}")
        else:
            self.logger.info(f"{msg.guild.name}/{msg.channel.name} {msg.author}: {msg.content}")

        if msg.content.startswith(self.prefix):
            command_segments = msg.content[len(self.prefix):].split(" ")
            command_name = command_segments[0]
            command_args = command_segments[1:]
            if command_name in self.commands:
                await self.commands[command_name]["func"](msg, command_args)

    async def on_message_edit(self, before, after):
        pass

    def register_commands(self):
        for attr in dir(self):
            obj = getattr(self, attr)
            if hasattr(obj, "command_info"):
                command_name = getattr(obj, "command_info")["name"]
                self.commands[command_name] = {"func": obj}
                self.logger.debug(f"Registered command {command_name}")

    @command(name="ping")
    async def ping_command(self, msg: discord.Message, args):
        await msg.channel.send("Pong!")

    @command(name="score")
    async def score_command(self, msg: discord.Message, args):
        scoreboard = await self.api_request("scoreboard")
        embed = await NPST_utils.get_scoreboard_embed(scoreboard, input_users=args)
        embed.set_footer(text=f"Etterspurt av {msg.author}")
        await msg.channel.send(embed=embed)

    def run(self, discord_token, npst_token):
        self.logger.debug("Running bot....")
        self.npst_token = npst_token
        super().run(discord_token)
