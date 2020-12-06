import NPST_utils

import hashlib
import asyncio
import aiohttp
import logging
import discord
import yaml
import json
import re
import os


def command(name, admin_only=False):
    def wrapper(func):
        func.command_info = {
            "name": name,
            "admin_only": admin_only
        }
        return func
    return wrapper


class DASSBetjent(discord.Client):
    def __init__(self, prefix="!", admin_prefix="+"):
        super().__init__()

        self.server_config_file = "servers.yaml"

        self.server_configs = None
        self.http_session = None
        self.npst_token = None
        self.profile = None

        self.admin_prefix = admin_prefix
        self.prefix = prefix

        self.logger = logging.getLogger("DASSBetjent")
        self.logger.debug("Initializing bot...")

        self.commands = {}

        self.event(self.on_ready)
        self.event(self.on_message)
        self.event(self.on_message_edit)

    async def api_request(self, path, method="GET"):
        full_path = path if path.startswith("http") else f"https://dass.npst.no/.netlify/functions/{path}"
        headers = {
            "authorization": f"Bearer {self.npst_token}",
            "credentials": "include",
            "referrer": "https://dass.npst.no/",
            "referrerPolicy": "strict-origin-when-cross-origin",
            "mode": "cors",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        resp = await self.http_session.request(method, full_path, headers=headers)
        resp_text = await resp.text()
        if resp.status == 200:
            try:
                resp_json = json.loads(resp_text)
            except json.JSONDecodeError:
                logging.warning(f"Failed to parse JSON from request for {method} {path}")
                return
            else:
                return resp_json
        else:
            logging.warning(f"Request failed for {method} {path}")

    async def on_ready(self):
        self.load_server_configs()
        self.register_commands()

        self.logger.info(f"Bot started as {self.user}")

        self.http_session = aiohttp.ClientSession()

        asyncio.create_task(self.autoupdate_inboxes())
        asyncio.create_task(self.autosave_server_configs())

        self.profile = await self.api_request("profile")

        self.logger.info(f"Bot started as [{self.user}] [{self.profile['display_name']}]")

    def load_server_configs(self):
        if os.path.exists(self.server_config_file):
            with open(self.server_config_file) as fr:
                self.server_configs = yaml.load(fr, Loader=yaml.FullLoader)
                if self.server_configs is None:
                    self.server_configs = {}
        else:
            with open(self.server_config_file, "w") as fw:
                yaml.dump({}, fw)
            self.server_configs = {}

    async def on_message(self, msg):
        await self.check_legality(msg)
        if type(msg.channel) is discord.DMChannel:
            self.logger.info(f"DMChannel/{msg.channel.recipient.name} {msg.author}: {msg.content}")
        else:
            self.logger.info(f"{msg.guild.name}/{msg.channel.name} {msg.author}: {msg.content}")

        if msg.content.startswith(self.prefix):
            command_segments = msg.content[len(self.prefix):].split(" ")
            command_name = command_segments[0]
            command_args = command_segments[1:]
            if command_name in self.commands:
                if self.commands[command_name]["info"]["admin_only"] and not msg.author.guild_permissions.administrator:
                    await msg.channel.send("No permission.")
                else:
                    try:
                        await self.commands[command_name]["func"](msg, command_args)
                    except Exception as e:
                        await msg.channel.send(f"`Noe gikk galt`")

    async def on_message_edit(self, _, after):
        await self.check_legality(after)

    async def check_legality(self, msg: discord.Message):
        if msg.author.bot:
            return
        if msg.channel.name == "cryptobin":
            if "cryptobin.co" not in msg.content:
                await msg.delete()
                await (await msg.channel.send(
                    f'Meldingen din ble slettet fra <#{msg.channel.id}>'
                    'fordi den ikke inneholdt en cryptobin link.'
                    'Du kan diskutere løsningene i <#652630061584875532>.'
                )).delete(delay=5)

        if not os.path.exists("known_keys.txt"):
            open("known_keys.txt", "w").close()
        else:
            with open("known_keys.txt", "r") as fr:
                known_keys = fr.read().split("\n")

            for possible in re.finditer(r"(?i)(PST|EGG){.*}", msg.content):
                span = possible.span()
                key_data = msg.content[span[0]:span[1]].upper()

                if hashlib.sha512(key_data.upper().encode()).hexdigest() in known_keys:
                    await msg.delete()
                    await msg.channel.send("Ikke del nøkler!")
                    if not msg.author.guild_permissions.administrator:
                        mod_channel = await self.fetch_channel(654781905660674049)
                        await mod_channel.send(f"{msg.author} delte en nøkkel i <#{msg.channel.id}>")
                else:
                    await msg.add_reaction("😒")

    def register_commands(self):
        for attr in dir(self):
            obj = getattr(self, attr)
            if hasattr(obj, "command_info"):
                command_info = getattr(obj, "command_info")
                self.commands[command_info['name']] = {"func": obj, "info": command_info}
                self.logger.debug(f"Registered command {command_info['name']}")

    def run(self, discord_token, npst_token):
        self.logger.debug("Running bot....")
        self.npst_token = npst_token
        super().run(discord_token)

    async def autosave_server_configs(self, delay=5):
        while True:
            await asyncio.sleep(delay)
            with open(self.server_config_file, "w") as fw:
                yaml.dump(self.server_configs, fw)

    async def autoupdate_inboxes(self, delay=15):
        while True:
            await self.update_inboxes()
            await asyncio.sleep(delay)

    async def update_inboxes(self, silenced=()):
        try:
            mail_inbox = await self.api_request("https://dass.npst.no/.netlify/functions/messages")
            assert type(mail_inbox) is list

        except Exception as e:
            logging.warning(f"Failed to get mail inbox, error: {str(e)} {str(type(e))}")
        else:
            for server in self.server_configs:
                asyncio.create_task(
                    self.forward_mail(self.server_configs[server], mail_inbox, silenced=server in silenced)
                )

    async def forward_mail(self, server_config, mail_inbox, silenced=False):
        try:
            inbox_channel = await self.fetch_channel(server_config['inbox']) if 'inbox' in server_config else None
            notif_channel = await self.fetch_channel(server_config['notif']) if 'notif' in server_config else None
        except discord.errors.Forbidden:
            return

        send_notification = False
        for mail in reversed(mail_inbox):
            mail_string = " ".join((mail['from'], ','.join(mail['to']), mail['sent'], mail['subject'], mail['content']))
            mail_hash = hashlib.md5(mail_string.encode()).hexdigest()
            if 'read_mail' in server_config:
                if mail_hash in server_config['read_mail']:
                    continue
            else:
                server_config['read_mail'] = []

            send_notification = True
            if inbox_channel is not None:
                server_config['read_mail'].append(mail_hash)
                await inbox_channel.send(NPST_utils.render_mail(mail))

        if send_notification and not silenced:
            if notif_channel is not None:
                await notif_channel.send(f"New mail in <#{server_config['inbox']}>")

    @command(name="ping")
    async def ping_command(self, msg: discord.Message, _):
        await msg.channel.send("Pong!")

    @command(name="score")
    async def score_command(self, msg: discord.Message, args):
        scoreboard = (await self.api_request("scoreboard"))["result"]
        embed = await NPST_utils.get_scoreboard_embed(scoreboard, input_users=args)
        embed.set_footer(text=f"Etterspurt av {msg.author}")
        await msg.channel.send(embed=embed)

    @command(name="reloadmail", admin_only=True)
    async def reloadmail_command(self, msg: discord.Message, _):
        if msg.guild.id in self.server_configs:
            self.server_configs[msg.guild.id]['read_mail'] = []
            await (await msg.channel.send("Reloading mail...")).delete(delay=5)
            await self.update_inboxes(silenced=[msg.guild.id])
            await msg.delete(delay=5)
        else:
            await msg.channel.send("Nothing is setup")

    @command(name="inbox", admin_only=True)
    async def inbox_command(self, msg: discord.Message, _):
        if msg.guild.id not in self.server_configs:
            self.server_configs[msg.guild.id] = {}
        if 'inbox' in self.server_configs[msg.guild.id]:
            del self.server_configs[msg.guild.id]['inbox']
            await msg.channel.send("Removed channel as inbox")
        else:
            self.server_configs[msg.guild.id]['inbox'] = msg.channel.id
            temp_msg = await msg.channel.send("Channel has been set as inbox")
            await asyncio.sleep(3)
            await self.update_inboxes(silenced=[msg.guild.id])
            await temp_msg.delete()
            await msg.delete()

    @command(name="notifications", admin_only=True)
    async def notifications_command(self, msg: discord.Message, _):
        if msg.guild.id not in self.server_configs:
            self.server_configs[msg.guild.id] = {}
        if 'notif' in self.server_configs[msg.guild.id]:
            del self.server_configs[msg.guild.id]['notif']
            await msg.channel.send("Removed channel as notification channel")
        else:
            self.server_configs[msg.guild.id]['notif'] = msg.channel.id
            await msg.channel.send("Channel has been set as notification channel")

    @command(name="purge", admin_only=True)
    async def purge_command(self, msg: discord.Message, args):
        if len(args) == 0:
            amount = 50
        else:
            try:
                amount = int(args[0])
            except ValueError:
                await msg.channel.send("Ugyldig mengde")
                return
        await msg.channel.purge(limit=amount)
