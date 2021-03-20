import os
import time
import json
import asyncio
import aiohttp
import discord
import requests
from discord.ext import commands

# Setup globals
config = {}
loop = asyncio.get_event_loop()
BOT_PREFIX = os.environ["BOT_PREFIX"] if os.environ.get("BOT_PREFIX") else "a/"
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"] if os.environ.get("DISCORD_TOKEN") else ""
WRITE_AS_POST_ID = os.environ["WRITE_AS_POST_ID"] if os.environ.get("WRITE_AS_POST_ID") else ""
WRITE_AS_POST_TOKEN = os.environ["WRITE_AS_POST_TOKEN"] if os.environ.get("WRITE_AS_POST_TOKEN") else ""
# BOT_PREFIX = "a/"
# DISCORD_TOKEN = ""
# WRITE_AS_POST_ID = ""
# WRITE_AS_POST_TOKEN = ""


# Get config
def get_config():
    global config
    config = json.loads(requests.get(f"https://write.as/{WRITE_AS_POST_ID}.txt").text)


# Save config
def save_config():
    global config
    requests.post(f'https://write.as/api/posts/{WRITE_AS_POST_ID}',
              headers={'Content-Type': 'application/json'},
              data=json.dumps({
                      "token": WRITE_AS_POST_TOKEN,
                      "body": json.dumps(config)
                  }))


# Only start bot if running as main and not import
if __name__ == '__main__':

    # Fetch config
    get_config()

    # Enable intents
    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True
    bot = commands.Bot(BOT_PREFIX, intents=intents)
    bot.remove_command('help')

    # On ready, fires when fully connected to Discord
    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user}')
    
    # Ignore command not found errors
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, discord.CommandNotFound):
            return
        raise error
    

    while True:
        try:
            loop.run_until_complete(bot.start(DISCORD_TOKEN))
        except discord.LoginFailure:
            # Invalid token
            print("BAD TOKEN!")
            loop.run_until_complete(bot.http.close())
            break
        except aiohttp.ClientConnectorError:
            # Connection to Discord failed
            print("CONNECTION ERROR! Sleeping 30 minutes...")
            loop.run_until_complete(bot.http.close())
            time.sleep(30)
            continue
        except KeyboardInterrupt:
            print("INTERRUPTED BY USER! Exiting...")
            loop.run_until_complete(bot.close())
            break
        loop.run_until_complete(bot.http.close())
        time.sleep(10)
