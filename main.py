from discord.ext import commands, tasks
import datetime
import discord
import aiohttp
import asyncio
import logging
import signal
import uvloop
import json
import io
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
        for key, value in config.items():
            if isinstance(value, (dict, list)):
                config[key] = json.dumps(value)
            else:
                config[key] = str(value)
        os.environ.update(config)
        globals.log.info("Loaded custom config")

# Local imports
from modules import db, utils, xp

globals.ADMIN_ID                   = int       (os.environ.get("ADMIN_ID")                   or 0)
globals.ASSISTANCE_CATEGORY_IDS    = json.loads(os.environ.get("ASSISTANCE_CATEGORY_IDS")    or "[]")
globals.BLACKLISTED_CHANNELS_IDS   = json.loads(os.environ.get("BLACKLISTED_CHANNELS_IDS")   or "[]")
globals.BOT_PREFIX                 = str       (os.environ.get("BOT_PREFIX")                 or "a/")
globals.CONTRIB_AMOUNT             = int       (os.environ.get("CONTRIB_AMOUNT")             or 1000)
globals.CONTRIB_CHANNELS_IDS       = json.loads(os.environ.get("CONTRIB_CHANNELS_IDS")       or "[]")
globals.CONTRIB_COOLDOWN           = int       (os.environ.get("CONTRIB_COOLDOWN")           or 3600)
globals.DAILY_LEVEL_AMOUNT         = int       (os.environ.get("DAILY_LEVEL_AMOUNT")         or 500)
globals.DB_HOST_TYPE               = str       (os.environ.get("DB_HOST_TYPE")               or "github")
globals.DISCORD_TOKEN              = str       (os.environ.get("DISCORD_TOKEN")              or "")
globals.GITHUB_GIST_FILENAME       = str       (os.environ.get("GITHUB_GIST_FILENAME")       or "db")
globals.GITHUB_GIST_ID             = str       (os.environ.get("GITHUB_GIST_ID")             or "")
globals.GITHUB_GIST_TOKEN          = str       (os.environ.get("GITHUB_GIST_TOKEN")          or "")
globals.GITHUB_GIST_USER           = str       (os.environ.get("GITHUB_GIST_USER")           or "")
globals.ICON_ROLE_IDS              = json.loads(os.environ.get("ICON_ROLE_IDS")              or "{}")
globals.IMGUR_CLIENT_ID            = str       (os.environ.get("IMGUR_CLIENT_ID")            or "")
globals.JOIN_LOG_CHANNEL_IDS       = json.loads(os.environ.get("JOIN_LOG_CHANNEL_IDS")       or "{}")
globals.LEVEL_NOTIF_CHANNEL_IDS    = json.loads(os.environ.get("LEVEL_NOTIF_CHANNEL_IDS")    or "{}")
globals.MODDER_CATEGORY_IDS        = json.loads(os.environ.get("MODDER_CATEGORY_IDS")        or "[]")
globals.MODDER_ROLE_IDS            = json.loads(os.environ.get("MODDER_ROLE_IDS")            or "[]")
globals.NO_PERM_ICON               = str       (os.environ.get("NO_PERM_ICON")               or "https://cdn.discordapp.com/emojis/778028443417313290.png")
globals.RELEASES_FILTER_CHANNELS   = json.loads(os.environ.get("RELEASES_FILTER_CHANNELS")   or "{}")
globals.RELEASES_FILTER_NOTIF_CHAN = json.loads(os.environ.get("RELEASES_FILTER_NOTIF_CHAN") or "{}")
globals.RELEASES_FILTER_WORDS      = json.loads(os.environ.get("RELEASES_FILTER_WORDS")      or "[]")
globals.REP_CRED_AMOUNT            = int       (os.environ.get("REP_CRED_AMOUNT")            or 500)
globals.REP_ICON                   = str       (os.environ.get("REP_ICON")                   or "https://cdn.discordapp.com/emojis/766042961929699358.png")
globals.REQUESTS_CHANNEL_IDS       = json.loads(os.environ.get("REQUESTS_CHANNEL_IDS")       or "{}")
globals.REQUESTS_COOLDOWN          = int       (os.environ.get("REQUESTS_COOLDOWN")          or 600)
globals.REQUESTS_ICONS             = json.loads(os.environ.get("REQUESTS_ICONS")             or '{"Waiting": "https://cdn.discordapp.com/emojis/889210410899746897.png", "WIP": "https://cdn.discordapp.com/emojis/889210383523536896.png", "Released": "https://cdn.discordapp.com/emojis/889210365362184272.png", "Already Exists": "https://cdn.discordapp.com/emojis/889210365362184272.png"}')
globals.STAFF_ROLE_IDS             = json.loads(os.environ.get("STAFF_ROLE_IDS")             or "[]")
globals.TROPHY_ROLES               = json.loads(os.environ.get("TROPHY_ROLES")               or "[]")
globals.WRITE_AS_PASS              = str       (os.environ.get("WRITE_AS_PASS")              or "")
globals.WRITE_AS_POST_ID           = str       (os.environ.get("WRITE_AS_POST_ID")           or "")
globals.WRITE_AS_USER              = str       (os.environ.get("WRITE_AS_USER")              or "")
globals.XP_AMOUNT                  = int       (os.environ.get("XP_AMOUNT")                  or 50)
globals.XP_COOLDOWN                = int       (os.environ.get("XP_COOLDOWN")                or 30)


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
                    globals.log.error("Failed to DM database backup")
            await utils.save_db()
    asyncio.get_event_loop().create_task(database_loop())

    # Create bot
    globals.bot = commands.Bot(
        command_prefix=utils.case_insensitive(globals.BOT_PREFIX),
        case_insensitive=True,
        description="Custom Discord bot for the Cyberpunk 2077 Modding Servers",
        intents=discord.Intents.default() | discord.Intents(discord.Intents.message_content.flag) | discord.Intents(discord.Intents.members.flag) | discord.Intents(discord.Intents.presences.flag),
        allowed_mentions=discord.AllowedMentions(everyone=False, roles=False) # Avoid unwanted chaos
    )
    globals.bot.remove_command('help')
    await globals.bot.load_extension('cogs.bot')
    await globals.bot.load_extension('cogs.fun')
    await globals.bot.load_extension('cogs.levelling')
    await globals.bot.load_extension('cogs.requests')
    await globals.bot.load_extension('cogs.utilities')
    await globals.bot.load_extension('cogs.staff')
    await globals.bot.load_extension('jishaku')
    globals.log.info('Loaded cogs')

    # On ready, fires when fully connected to Discord
    @globals.bot.event
    async def on_ready():
        globals.log.info(f"Logged in as: {globals.bot.user}")
        await globals.bot.tree.sync()
        globals.log.info("Synced slash commands")
        if not update_presence_loop.is_running():
            update_presence_loop.start()
        globals.log.info("Started status loop")
        globals.start_dt = datetime.datetime.utcnow()

    # Ignore command not found errors
    @globals.bot.event
    async def on_command_error(ctx, error):
        def is_(e_type):
            if isinstance(error, e_type):
                return True
            for inherit in type(error).__mro__:
                if inherit.__name__ == e_type.__name__:
                    return True
            return False
        e = commands.errors
        # No cooldown for command errors
        if not is_(e.CommandOnCooldown) and ctx.command and hasattr(ctx.command, "reset_cooldown"):
            ctx.command.reset_cooldown(ctx)
        # Actual error handling
        if is_(e.CommandNotFound) or is_(e.DisabledCommand):
            await utils.embed_reply(ctx,
                                    title=f'💢 Unknown command "a/{ctx.invoked_with}"!',
                                    description=f"Did you mean **`{globals.BOT_PREFIX.lower()}{utils.get_best_command_match(ctx.invoked_with)}`**?")
        elif is_(e.CommandOnCooldown):
            c = error.cooldown
            retry_in = str(datetime.timedelta(seconds=int(error.retry_after)))
            title = (ctx.command.extras.get("cooldown_title", None) or "You're on cooldown!").format(retry_in=retry_in)
            desc = ctx.command.extras.get("cooldown_desc", None)
            if desc is False:
                desc = ""
            else:
                desc = (desc or f"You can only do that {'once' if c.rate == 1 else f'{c.rate} times'} every **{f'{c.per/3600:.0f} hours' if c.per > 3600 else f'{c.per/60:.0f} minutes' if c.per > 60 else f'{c.per/3600:.0f} seconds'}**").format(retry_in=retry_in)
            await utils.embed_reply(ctx,
                                    title=f"💢 {title}",
                                    description=desc + "\n"
                                                f"Come back in **{retry_in}** and try again")
        elif is_(e.MissingRequiredArgument) or is_(e.MissingRequiredAttachment):
            await utils.embed_reply(ctx,
                                    title=f"💢 Missing argument for '{ctx.current_parameter.name}'!",
                                    description=f"**Usage**: `{ctx.command.usage.format(prfx=globals.BOT_PREFIX.lower())}`\n" +
                                                ctx.command.help)
        elif is_(e.BadArgument) or is_(e.BadUnionArgument) or is_(e.BadLiteralArgument) or is_(e.ConversionError):
            await utils.embed_reply(ctx,
                                    title=f"💢 Bad argument for '{ctx.current_parameter.name}'!",
                                    description=f"**Your input**: {ctx.current_argument}\n" +
                                                str(error))
        elif is_(e.ArgumentParsingError):
            await utils.embed_reply(ctx,
                                    title=f"💢 Failed parsing command input!",
                                    description=f"**Usage**: `{ctx.command.usage.format(prfx=globals.BOT_PREFIX.lower())}`\n" +
                                                ctx.command.help)
        elif is_(e.NotOwner) or is_(e.CheckFailure) or is_(e.CheckAnyFailure):
            title = ctx.command.extras.get("check_title", None)
            desc = ctx.command.extras.get("check_desc", None)
            if title or desc:
                await utils.embed_reply(ctx,
                                        title=f"💢 {title}",
                                        description=desc)
            else:
                await utils.embed_reply(ctx,
                                        title="💢 Yea, that's not happening buddy!",
                                        description="Nice try kid lmao",
                                        thumbnail=globals.NO_PERM_ICON)
        elif is_(e.CommandInvokeError):
            globals.log.error(utils.get_traceback(error))
            try:
                await utils.embed_reply(ctx,
                                        title=f"💢 Error executing command!",
                                        description="Check the **attached text file** for a full traceback.",
                                        file=discord.File(io.StringIO(utils.get_traceback(error)), filename="traceback.txt", spoiler=True))
            except discord.errors.DiscordException:
                pass
        else:
            raise error

    @globals.bot.tree.error
    async def on_error(interaction, error):
        ctx = await commands.Context.from_interaction(interaction)
        return await on_command_error(ctx, error)

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
        lowered_content = message.content and message.content.lower()
        if message.channel.id in (globals.RELEASES_FILTER_CHANNELS.get(str(message.guild.id)) or []) and (message.author.bot or message.webhook_id):
            for word in globals.RELEASES_FILTER_WORDS:
                word = word.lower()
                match_final = False
                search = lambda text: (word in (text.lower() or "") and (text or ""))
                match_final = match_final or search(message.content)
                match_embeds = bool(message.embeds)
                for embed in message.embeds:
                    match = False
                    match = match or search(embed.author.name)
                    match = match or search(embed.title)
                    match = match or search(embed.description)
                    for field in embed.fields:
                        match = match or search(field.name)
                        match = match or search(field.value)
                    match = match or search(embed.footer.text)
                    match_embeds = match_embeds and match  # All embeds must match
                match_final = match_final or match_embeds
                if match_final:
                    await message.delete()
                    notif_chan = globals.RELEASES_FILTER_NOTIF_CHAN.get(str(message.guild.id)) or 0
                    if notif_chan:
                        notif_chan = message.guild.get_channel(notif_chan)
                        await notif_chan.send(embed=utils.custom_embed(message.guild,
                                                                       title="💢 Begone, mod!",
                                                                       description=f"A mod release post was just **removed** from <#{message.channel.id}>\n"
                                                                                   f"**Matching filter**: `{word}`\n"
                                                                                   f"**Incriminating text**: ||{(match_final[:999] + '...') if len(match_final) > 999 else match_final}||"))
                    break
        if message.channel.id in (globals.REQUESTS_CHANNEL_IDS.get(str(message.guild.id)) or []):
            if message.content and utils.is_requests_command(lowered_content):
                await globals.bot.process_commands(message)
            elif message.author.bot:
                if message.author.id != globals.bot.user.id:
                    await message.delete()
            elif not utils.is_staff(message.author):
                await utils.embed_reply(message,
                                        title="💢 Only mod request commands here!",
                                        description="Check the pinned messages for more information!")
        elif message.content and lowered_content.startswith(globals.BOT_PREFIX.lower()):
            await globals.bot.process_commands(message)
        else:
            await xp.process_xp(message)

    # Handle deleting requests by staff
    @globals.bot.event
    async def on_raw_message_delete(payload):
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(payload.guild_id)) or []
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

    # Exit after saving DB
    async def graceful_exit():
        globals.log.info("Saving DB...")
        try:
            await db.save_to_disk()
        except Exception:
            globals.log.error("Failed to save DB to disk")
        try:
            await utils.save_db()
        except Exception:
            globals.log.error("Failed to save remote DB")
        try:
            admin = globals.bot.get_user(globals.ADMIN_ID)
            if admin:
                await admin.send(file=discord.File('db.sqlite3'))
        except Exception:
            globals.log.error("Failed to DM database backup")
        try:
            await globals.db.close()
        except Exception:
            globals.log.error("Failed to close DB gracefully")
        globals.log.info("Exiting...")
        update_presence_loop.stop()
        asyncio.get_event_loop().stop()
        os._exit(os.EX_OK)
    # Schedule graceful exit for kill signals
    for signame in ['SIGINT', 'SIGTERM']:
        asyncio.get_event_loop().add_signal_handler(getattr(signal, signame), lambda: asyncio.get_event_loop().create_task(graceful_exit()))

    # Actually run the bot
    await globals.bot.start(globals.DISCORD_TOKEN)

# Only start bot if running as main and not import
if __name__ == '__main__':
    asyncio.run(main())
