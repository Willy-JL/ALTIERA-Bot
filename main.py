import io
import os
import time
import json
import asyncio
import aiohttp
import discord
import datetime
from discord.ext import commands, tasks

# Local imports
from modules import utils, globals, xp

# Setup globals
globals.loop = asyncio.get_event_loop()
globals.cur_presence = 0

globals.ADMIN_ID = int(os.environ["ADMIN_ID"]) if os.environ.get("ADMIN_ID") else 0
globals.ASSISTANCE_CATEGORY_ID = int(os.environ["ASSISTANCE_CATEGORY_ID"]) if os.environ.get("ASSISTANCE_CATEGORY_ID") else 0
globals.BLACKLISTED_CHANNELS_IDS = json.loads(os.environ["BLACKLISTED_CHANNELS_IDS"]) if os.environ.get("BLACKLISTED_CHANNELS_IDS") else []
globals.BOT_PREFIX = str(os.environ["BOT_PREFIX"]) if os.environ.get("BOT_PREFIX") else "a/"
globals.CONTRIB_AMOUNT = int(os.environ["CONTRIB_AMOUNT"]) if os.environ.get("CONTRIB_AMOUNT") else 1000
globals.CONTRIB_CHANNELS_IDS = json.loads(os.environ["CONTRIB_CHANNELS_IDS"]) if os.environ.get("CONTRIB_CHANNELS_IDS") else []
globals.CONTRIB_COOLDOWN = int(os.environ["CONTRIB_COOLDOWN"]) if os.environ.get("CONTRIB_COOLDOWN") else 3600
globals.DISCORD_TOKEN = str(os.environ["DISCORD_TOKEN"]) if os.environ.get("DISCORD_TOKEN") else ""
globals.JOIN_LOG_CHANNEL_ID = int(os.environ["JOIN_LOG_CHANNEL_ID"]) if os.environ.get("JOIN_LOG_CHANNEL_ID") else 0
globals.MODDER_CATEGORY_IDS = json.loads(os.environ["MODDER_CATEGORY_IDS"]) if os.environ.get("MODDER_CATEGORY_IDS") else []
globals.MODDER_ROLE_ID = int(os.environ["MODDER_ROLE_ID"]) if os.environ.get("MODDER_ROLE_ID") else 0
globals.ROLE_SELECT_CHANNEL_ID = int(os.environ["ROLE_SELECT_CHANNEL_ID"]) if os.environ.get("ROLE_SELECT_CHANNEL_ID") else 0
globals.RULES_CHANNEL_ID = int(os.environ["RULES_CHANNEL_ID"]) if os.environ.get("RULES_CHANNEL_ID") else 0
globals.STAFF_ROLE_ID = int(os.environ["STAFF_ROLE_ID"]) if os.environ.get("STAFF_ROLE_ID") else 0
globals.TROPHY_ROLES = json.loads(os.environ["TROPHY_ROLES"]) if os.environ.get("TROPHY_ROLES") else []
globals.WRITE_AS_PASS = str(os.environ["WRITE_AS_PASS"]) if os.environ.get("WRITE_AS_PASS") else ""
globals.WRITE_AS_POST_ID = str(os.environ["WRITE_AS_POST_ID"]) if os.environ.get("WRITE_AS_POST_ID") else ""
globals.WRITE_AS_USER = str(os.environ["WRITE_AS_USER"]) if os.environ.get("WRITE_AS_USER") else ""
globals.XP_AMOUNT = int(os.environ["XP_AMOUNT"]) if os.environ.get("XP_AMOUNT") else 50
globals.XP_COOLDOWN = int(os.environ["XP_COOLDOWN"]) if os.environ.get("XP_COOLDOWN") else 30


# Only start bot if running as main and not import
if __name__ == '__main__':

    # Make persistent image components
    utils.setup_persistent_components()

    # Fetch config
    utils.get_config()

    # Periodically save config
    async def config_loop():
        while True:
            await asyncio.sleep(5)
            utils.save_config()
            if globals.bot.user:  # Check if logged in
                admin = globals.bot.get_user(globals.ADMIN_ID)
                if admin:
                    if not admin.dm_channel:
                        await admin.create_dm()
                    binary = utils.bytes_to_binary_object(json.dumps(globals.config).encode())
                    await admin.dm_channel.send(file=discord.File(binary, filename="backup.json"))
                else:
                    print("Couldn't DM config backup!")
            await asyncio.sleep(895)
    globals.loop.create_task(config_loop())

    # Enable intents
    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True
    # Create bot
    globals.bot = commands.Bot(globals.BOT_PREFIX, intents=intents)
    globals.bot.remove_command('help')
    globals.bot.load_extension('modules.commands')

    # On ready, fires when fully connected to Discord
    @globals.bot.event
    async def on_ready():
        print(f'Logged in as {globals.bot.user}!')
        update_presence_loop.start()
    
    # Ignore command not found errors
    @globals.bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            return
        raise error

    # Greet user when they join
    @globals.bot.event
    async def on_member_join(member):
        channel = member.guild.get_channel(globals.JOIN_LOG_CHANNEL_ID)
        await channel.send(content=f"<@!{member.id}>",
                           embed=discord.Embed(title="Welcome!",
                                               description=f"Welcome <@!{member.id}> to Night City!\n"
                                                           f"\n"
                                                           f"Make sure you have a read through <#{globals.RULES_CHANNEL_ID}>!\n"
                                                           f"You can pick your poisons in <#{globals.ROLE_SELECT_CHANNEL_ID}>!\n"
                                                           f"Enjoy your stay!",
                                               color=discord.Color(0xEDE400),
                                               timestamp=datetime.datetime.utcnow())
                                               .set_thumbnail(url=member.avatar_url)
                                               .set_footer(text=member.guild.name,
                                                           icon_url=member.guild.icon_url))

    # Message handler and callback dispatcher
    @globals.bot.event
    async def on_message(message):
        if message.content and message.content.startswith(globals.bot.command_prefix):
            await globals.bot.process_commands(message)
        else:
            await xp.process_xp(message)

    @tasks.loop(seconds=15)
    async def update_presence_loop():
        if globals.cur_presence == 0:
            await globals.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name=f'Cyberspace'), status=discord.Status.dnd)
            globals.cur_presence = 1
        elif globals.cur_presence == 1:
            count = 0
            for guild in globals.bot.guilds:
                count += guild.member_count
            await globals.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'{count} users'), status=discord.Status.dnd)
            globals.cur_presence = 2
        elif globals.cur_presence == 2:
            await globals.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'the Blackwall'), status=discord.Status.dnd)
            globals.cur_presence = 0

    # Actually run the bot
    while True:
        try:
            globals.loop.run_until_complete(globals.bot.start(globals.DISCORD_TOKEN))
        except discord.LoginFailure:
            # Invalid token
            print("BAD TOKEN!")
            globals.loop.run_until_complete(globals.bot.http.close())
            break
        except aiohttp.ClientConnectorError:
            # Connection to Discord failed
            print("CONNECTION ERROR! Sleeping 60 seconds...")
            globals.loop.run_until_complete(globals.bot.http.close())
            time.sleep(60)
            continue
        except KeyboardInterrupt:
            print("INTERRUPTED BY USER! Exiting...")
            globals.loop.run_until_complete(globals.bot.close())
            break
        globals.loop.run_until_complete(globals.bot.http.close())
        time.sleep(10)
