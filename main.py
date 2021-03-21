import io
import os
import time
import json
import asyncio
import aiohttp
import discord
from discord.ext import commands

# Local imports
import utils
import globals

# Setup globals
globals.loop = asyncio.get_event_loop()

globals.BOT_PREFIX = os.environ["BOT_PREFIX"] if os.environ.get("BOT_PREFIX") else "a/"
globals.TROPHY_ROLES = json.loads(os.environ["TROPHY_ROLES"]) if os.environ.get("TROPHY_ROLES") else []
globals.STAFF_ROLE_ID = os.environ["STAFF_ROLE_ID"] if os.environ.get("STAFF_ROLE_ID") else 0
globals.DISCORD_TOKEN = os.environ["DISCORD_TOKEN"] if os.environ.get("DISCORD_TOKEN") else ""
globals.WRITE_AS_POST_ID = os.environ["WRITE_AS_POST_ID"] if os.environ.get("WRITE_AS_POST_ID") else ""
globals.WRITE_AS_POST_TOKEN = os.environ["WRITE_AS_POST_TOKEN"] if os.environ.get("WRITE_AS_POST_TOKEN") else ""
# For testing purposes:
# globals.BOT_PREFIX = "a/"
# globals.TROPHY_ROLES = [1234567890, 9876543210]
# globals.STAFF_ROLE_ID = 1234567890
# globals.DISCORD_TOKEN = "a1b2c3d4f5g6h7i8j9k0"
# globals.WRITE_AS_POST_ID = "a1b2c3d4f5g6"
# globals.WRITE_AS_POST_TOKEN = "a1b2c3d4f5g6h7i8j9k0"


# Only start bot if running as main and not import
if __name__ == '__main__':

    # Make persistent image components
    utils.setup_persistent_components()

    # Fetch config
    utils.get_config()

    # Periodically save config
    async def config_loop():
        while True:
            await asyncio.sleep(1800)
            utils.save_config()
            if globals.bot.user:  # Check if logged in
                admin = globals.bot.get_user(285519042163245056)
                if admin:
                    if not admin.dm_channel:
                        await admin.create_dm()
                    binary = io.BytesIO()
                    binary.write(json.dumps(globals.config).encode())
                    binary.seek(0)
                    await admin.dm_channel.send(file=discord.File(binary, filename="backup.json"))
                else:
                    print("Couldn't DM config backup!")
    globals.loop.create_task(config_loop())

    # Enable intents
    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True
    # Create bot
    globals.bot = commands.Bot(globals.BOT_PREFIX, intents=intents)
    globals.bot.remove_command('help')
    globals.bot.load_extension('commands')

    # On ready, fires when fully connected to Discord
    @globals.bot.event
    async def on_ready():
        print(f'Logged in as {globals.bot.user}!')
    
    # Ignore command not found errors
    @globals.bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            return
        raise error

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
