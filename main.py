from discord.ext import commands, tasks
import datetime
import discord
import aiohttp
import asyncio
import logging
import signal
import uvloop
import json
import os

# Asyncio drop-in replacement, 2-4x faster
uvloop.install()

# Setup globals and logging
from modules import globals
_log = logging.getLogger()
_log.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(discord.utils._ColourFormatter())
_log.addHandler(_handler)
globals.log = logging.getLogger(__name__.strip("_"))
globals.cur_presence = 0
if os.path.exists("config.json"):
    with open("config.json", "rb") as f:
        config = json.load(f)
        os.environ.update(config)
        globals.log.info("Loaded custom config")

# Local imports
from modules import db, utils, xp

globals.ADMIN_ID                 = int       (os.environ.get("ADMIN_ID")                 or 0)
globals.ASSISTANCE_CATEGORY_IDS  = json.loads(os.environ.get("ASSISTANCE_CATEGORY_IDS")  or "[]")
globals.BLACKLISTED_CHANNELS_IDS = json.loads(os.environ.get("BLACKLISTED_CHANNELS_IDS") or "[]")
globals.BOT_PREFIX               = str       (os.environ.get("BOT_PREFIX")               or "a/")
globals.CONTRIB_AMOUNT           = int       (os.environ.get("CONTRIB_AMOUNT")           or 1000)
globals.CONTRIB_CHANNELS_IDS     = json.loads(os.environ.get("CONTRIB_CHANNELS_IDS")     or "[]")
globals.CONTRIB_COOLDOWN         = int       (os.environ.get("CONTRIB_COOLDOWN")         or 3600)
globals.DAILY_LEVEL_AMOUNT       = int       (os.environ.get("DAILY_LEVEL_AMOUNT")       or 500)
globals.DB_HOST_TYPE             = str       (os.environ.get("DB_HOST_TYPE")             or "github")
globals.DISCORD_TOKEN            = str       (os.environ.get("DISCORD_TOKEN")            or "")
globals.GITHUB_GIST_FILENAME     = str       (os.environ.get("GITHUB_GIST_FILENAME")     or "db")
globals.GITHUB_GIST_ID           = str       (os.environ.get("GITHUB_GIST_ID")           or "")
globals.GITHUB_GIST_TOKEN        = str       (os.environ.get("GITHUB_GIST_TOKEN")        or "")
globals.GITHUB_GIST_USER         = str       (os.environ.get("GITHUB_GIST_USER")         or "")
globals.HEROKU_TOKEN             = str       (os.environ.get("HEROKU_TOKEN")             or "")
globals.ICON_ROLE_IDS            = json.loads(os.environ.get("ICON_ROLE_IDS")            or "{}")
globals.IMGUR_CLIENT_ID          = str       (os.environ.get("IMGUR_CLIENT_ID")          or "")
globals.JOIN_LOG_CHANNEL_IDS     = json.loads(os.environ.get("JOIN_LOG_CHANNEL_IDS")     or "{}")
globals.LEVEL_NOTIF_CHANNEL_IDS  = json.loads(os.environ.get("LEVEL_NOTIF_CHANNEL_IDS")  or "{}")
globals.MODDER_CATEGORY_IDS      = json.loads(os.environ.get("MODDER_CATEGORY_IDS")      or "[]")
globals.MODDER_ROLE_IDS          = json.loads(os.environ.get("MODDER_ROLE_IDS")          or "[]")
globals.NO_PERM_ICON             = str       (os.environ.get("NO_PERM_ICON")             or "https://cdn.discordapp.com/emojis/778028443417313290.png")
globals.REP_CRED_AMOUNT          = int       (os.environ.get("REP_CRED_AMOUNT")          or 500)
globals.REP_ICON                 = str       (os.environ.get("REP_ICON")                 or "https://cdn.discordapp.com/emojis/766042961929699358.png")
globals.REQUESTS_CHANNEL_IDS     = json.loads(os.environ.get("REQUESTS_CHANNEL_IDS")     or "{}")
globals.REQUESTS_COOLDOWN        = int       (os.environ.get("REQUESTS_COOLDOWN")        or 600)
globals.REQUESTS_ICONS           = json.loads(os.environ.get("REQUESTS_ICONS")           or '{"Waiting": "https://cdn.discordapp.com/emojis/889210410899746897.png", "WIP": "https://cdn.discordapp.com/emojis/889210383523536896.png", "Released": "https://cdn.discordapp.com/emojis/889210365362184272.png", "Already Exists": "https://cdn.discordapp.com/emojis/889210365362184272.png"}')
globals.STAFF_ROLE_IDS           = json.loads(os.environ.get("STAFF_ROLE_IDS")           or "[]")
globals.TROPHY_ROLES             = json.loads(os.environ.get("TROPHY_ROLES")             or "[]")
globals.WRITE_AS_PASS            = str       (os.environ.get("WRITE_AS_PASS")            or "")
globals.WRITE_AS_POST_ID         = str       (os.environ.get("WRITE_AS_POST_ID")         or "")
globals.WRITE_AS_USER            = str       (os.environ.get("WRITE_AS_USER")            or "")
globals.XP_AMOUNT                = int       (os.environ.get("XP_AMOUNT")                or 50)
globals.XP_COOLDOWN              = int       (os.environ.get("XP_COOLDOWN")              or 30)


async def main():

    # Make persistent image components
    utils.setup_persistent_components()

    # Create persistent aiohttp session
    globals.http = aiohttp.ClientSession()

    # Fetch database
    await utils.get_db()

    # Periodically save database
    async def database_loop():
        while True:
            await asyncio.sleep(900)
            await db.save_to_disk()
            if globals.bot.user:  # Check if logged in
                admin = globals.bot.get_user(globals.ADMIN_ID)
                if admin:
                    await admin.send(file=discord.File('db.sqlite3'))
                else:
                    globals.log.warn("Couldn't DM database backup!")
            await utils.save_db()
    asyncio.get_event_loop().create_task(database_loop())

    # Enable intents
    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True
    # Avoid unwanted chaos
    allowed_mentions = discord.AllowedMentions(everyone=False, roles=False)
    # Create bot
    globals.bot = commands.Bot(
        command_prefix=utils.case_insensitive(globals.BOT_PREFIX),
        case_insensitive=True,
        description="Custom Discord bot for the Cyberpunk 2077 Modding Servers",
        intents=discord.Intents.default() | discord.Intents(discord.Intents.message_content.flag) | discord.Intents(discord.Intents.members.flag) | discord.Intents(discord.Intents.presences.flag),
        allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
    )
    globals.bot.remove_command('help')
    await globals.bot.load_extension('cogs.bot')
    await globals.bot.load_extension('cogs.fun')
    await globals.bot.load_extension('cogs.levelling')
    await globals.bot.load_extension('cogs.requests')
    await globals.bot.load_extension('cogs.utilities')
    await globals.bot.load_extension('cogs.staff')
    await globals.bot.load_extension('jishaku')
    globals.log.info('Loaded cogs!')

    # On ready, fires when fully connected to Discord
    @globals.bot.event
    async def on_ready():
        globals.log.info(f"Logged in as: {globals.bot.user}")
        if not update_presence_loop.is_running():
            update_presence_loop.start()
        # Compute next restart time
        now = datetime.datetime.utcnow()
        midnight = datetime.time(0, 0)
        next_midnight = datetime.datetime.combine(now, midnight)
        if next_midnight < now:
            next_midnight += datetime.timedelta(days=1)
        globals.start_dt = now
        globals.restart_dt = next_midnight
        # Exit after saving DB
        async def graceful_exit():
            globals.log.info("Saving DB...")
            await db.save_to_disk()
            admin = globals.bot.get_user(globals.ADMIN_ID)
            if admin:
                await admin.send(file=discord.File('db.sqlite3'))
            await utils.save_db()
            await globals.db.close()
            globals.log.info("Exiting...")
            update_presence_loop.stop()
            asyncio.get_event_loop().stop()
            os._exit(os.EX_OK)
        # Schedule graceful exit for kill signals
        for signame in ['SIGINT', 'SIGTERM']:
            asyncio.get_event_loop().add_signal_handler(getattr(signal, signame), lambda: asyncio.get_event_loop().create_task(graceful_exit()))
        # Wait until restart time
        await asyncio.sleep(max((next_midnight - now).total_seconds(), 0))
        # Force restart
        await utils.restart()

    # Ignore command not found errors
    @globals.bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            await utils.embed_reply(ctx,
                                    title=f'💢 Unknown command "{ctx.invoked_with}"!',
                                    description=f"Did you mean **`{globals.BOT_PREFIX.lower()}{utils.get_best_command_match(ctx.invoked_with)}`**?")
            return
        if isinstance(error, commands.errors.NotOwner):
            await utils.embed_reply(ctx,
                                    title="💢 Yea, that's not happening buddy!",
                                    thumbnail=globals.NO_PERM_ICON)
            return
        raise error

    # Greet user when they join
    @globals.bot.event
    async def on_member_join(member):
        if str(member.guild.id) in globals.JOIN_LOG_CHANNEL_IDS:
            channel = member.guild.get_channel(globals.JOIN_LOG_CHANNEL_IDS[str(member.guild.id)]["join_channel_id"])
            await channel.send(content=f"<@!{member.id}>",
                               embed=utils.custom_embed(member.guild,
                                                        title="👋 Welcome!",
                                                        description=f"Welcome <@!{member.id}> to Night City!\n"
                                                                    "\n" +
                                                                    (f"Make sure you have read through <#{globals.JOIN_LOG_CHANNEL_IDS[str(member.guild.id)]['rules_channel_id']}>!\n" if globals.JOIN_LOG_CHANNEL_IDS[str(member.guild.id)]["rules_channel_id"] else "") +
                                                                    (f"You can pick your poisons in <#{globals.JOIN_LOG_CHANNEL_IDS[str(member.guild.id)]['selfrole_channel_id']}>!\n" if globals.JOIN_LOG_CHANNEL_IDS[str(member.guild.id)]["selfrole_channel_id"] else "") +
                                                                    "Enjoy your stay!",
                                                        thumbnail=member.display_avatar.url))

    # Message handler and callback dispatcher
    @globals.bot.event
    async def on_message(message):
        if not message.guild:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(message.guild.id)) or ()
        if message.channel.id in req_channels:
            if message.content and utils.is_requests_command(message.content):
                await globals.bot.process_commands(message)
            elif not utils.is_staff(message.author):
                await message.delete()
                try:
                    await message.author.send(embed=utils.custom_embed(message.guild,
                                                                       title="💢 Only relevant commands are allowed in mod requests channels!",
                                                                       description="Check the pinned messages for more information!"))
                except Exception:
                    pass
        elif message.content and message.content.lower().startswith(globals.BOT_PREFIX.lower()):
            await globals.bot.process_commands(message)
        else:
            await xp.process_xp(message)

    # Handle deleting requests by staff
    @globals.bot.event
    async def on_raw_message_delete(payload):
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(payload.guild_id)) or ()
        if payload.channel_id in req_channels:
            await db.delete_request(msg=payload)

    # Change status every 15 seconds
    @tasks.loop(seconds=15)
    async def update_presence_loop():
        if globals.cur_presence == 0:
            await globals.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name='Cyberspace'),     status=discord.Status.dnd)
            globals.cur_presence = 1
        elif globals.cur_presence == 1:
            count = 0
            for guild in globals.bot.guilds:
                count += guild.member_count
            await globals.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'{count} users'), status=discord.Status.dnd)
            globals.cur_presence = 2
        elif globals.cur_presence == 2:
            await globals.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,  name='the Blackwall'),  status=discord.Status.dnd)
            globals.cur_presence = 0

    # Actually run the bot
    await globals.bot.start(globals.DISCORD_TOKEN)

# Only start bot if running as main and not import
if __name__ == '__main__':
    asyncio.run(main())
