from fuzzywuzzy import process, fuzz
from PIL import Image, ImageFont
from discord.ext import commands
from discord import app_commands
import itertools
import traceback
import datetime
import aiofiles
import discord
import inspect
import asyncio
import base64
import zlib
import json
import sys
import ast
import io
import os

# Local imports
from modules import globals, db, errors, xp


# Get database
async def get_db():
    if not os.path.exists("db.sqlite3"):
        if globals.DB_HOST_TYPE == "github":
            async with globals.http.get(f'https://gist.githubusercontent.com/{globals.GITHUB_GIST_USER}/{globals.GITHUB_GIST_ID}/raw',
                                        headers={
                                            'Authorization': f'Token {globals.GITHUB_GIST_TOKEN}'
                                        }) as req:
                db_data = await req.text()
        elif globals.DB_HOST_TYPE == "writeas":
            async with globals.http.post('https://write.as/api/auth/login',
                                         headers={
                                             'Content-Type': 'application/json'
                                         },
                                         data=json.dumps({
                                             "alias": globals.WRITE_AS_USER,
                                             "pass": globals.WRITE_AS_PASS
                                         })) as req:
                globals.write_as_token = (await req.json())["data"]["access_token"]
            async with globals.http.get(f"https://write.as/{globals.WRITE_AS_USER}/{globals.WRITE_AS_POST_ID}.txt") as req:
                db_data = await req.text()
        else:
            raise Exception("No valid DB type specified!")
        decoded = base64.b85decode(db_data.encode("utf-8"))
        decompressed = zlib.decompress(decoded)
        async with aiofiles.open('db.sqlite3', 'wb') as f:
            await f.write(decompressed)
    await db.init_db()
    globals.log.info("Initialized DB")


# Save database
async def save_db():
    if globals.db is not None:
        if globals.db._running is True:
            await db.save_to_disk()
        async with aiofiles.open('db.sqlite3', 'rb') as f:
            raw = await f.read()
        compressed = zlib.compress(raw, zlib.Z_BEST_COMPRESSION)
        encoded = base64.b85encode(compressed)
        db_data = encoded.decode("utf-8")
        if globals.DB_HOST_TYPE == "github":
            async with globals.http.patch(f'https://api.github.com/gists/{globals.GITHUB_GIST_ID}',
                                          headers={
                                              'Accept': 'application/vnd.github.v3+json',
                                              'Authorization': f'Token {globals.GITHUB_GIST_TOKEN}'
                                          },
                                          data=json.dumps({
                                              "files": {
                                                  f"{globals.GITHUB_GIST_FILENAME}": {
                                                      "content": db_data
                                                  }
                                              }
                                          })) as req:
                if not req.ok:
                    globals.log.error(f"Failed to save config, code: {req.status}, message: {await req.text()}")
                    return False
                return True
        elif globals.DB_HOST_TYPE == "writeas":
            async with globals.http.post(f'https://write.as/api/collections/{globals.WRITE_AS_USER}/posts/{globals.WRITE_AS_POST_ID}',
                                         headers={
                                             'Authorization': f'Token {globals.write_as_token}',
                                             'Content-Type': 'application/json'
                                         },
                                         data=json.dumps({
                                             "body": db_data,
                                             "font": "code"
                                         })) as req:
                if not req.ok:
                    globals.log.error(f"Failed to save config, code: {req.status}, message: {await req.text()}")
                    return False
                return True
        else:
            raise Exception("No valid DB type specified!")


# Restart the bot
async def restart():
    globals.log.info("Saving DB...")
    await db.save_to_disk()
    admin = globals.bot.get_user(globals.ADMIN_ID)
    if admin:
        await admin.send(file=discord.File('db.sqlite3'))
    await save_db()
    await globals.db.close()
    globals.log.info("Restarting...")
    import main  # I know, I know, please Lord forgive me
    os.execl(sys.executable, 'python', main.__file__, *sys.argv[1:])


# Setup persistent image components
def setup_persistent_components():
    # Fonts
    globals.font47 = ImageFont.truetype("assets/square.ttf", 47)
    globals.font35 = ImageFont.truetype("assets/square.ttf", 35)
    globals.font30 = ImageFont.truetype("assets/square.ttf", 30)
    globals.font24 = ImageFont.truetype("assets/square.ttf", 24)
    globals.font20 = ImageFont.truetype("assets/square.ttf", 20)
    globals.font16 = ImageFont.truetype("assets/square.ttf", 16)
    # Avatars
    globals.default_avatar = Image.open('assets/default_avatar.png').resize((200, 200))
    # Overlays
    globals.overlays_default = Image.open('assets/overlays/default.png')
    globals.overlays_staff   = Image.open('assets/overlays/staff.png'  )
    globals.overlays_admin   = Image.open('assets/overlays/admin.png'  )
    # Shards
    globals.shards_orange = Image.open("assets/shards/orange.png").resize((33, 28))
    globals.shards_white  = Image.open("assets/shards/white.png" ).resize((33, 28))
    globals.shards_teal   = Image.open("assets/shards/teal.png"  ).resize((33, 28))
    # Bars
    globals.bars = {}
    for color in ["blue_white", "orange_white", "teal_white", "white_blue", "white_orange"]:
        globals.bars[color] = []
        for i in range(11):
            globals.bars[color].append(Image.open(f"assets/bars/{color}/{i}.png"))
    # Levelups
    globals.levelups = {}
    for xp_type in ["level", "cred", "assistance"]:
        globals.levelups[xp_type] = {}
        globals.levelups[xp_type]["overlay"] = Image.open(f"assets/levelup/{xp_type}.png")
        globals.levelups[xp_type]["color"] = "#FFFFFF" if xp_type == "level" else "#FFFFFF" if xp_type == "cred" else "#F06B02" if xp_type == "assistance" else ""


# Save bytes array into a readable binary object
def bytes_to_binary_object(bytes_arr):
    binary = io.BytesIO()
    binary.write(bytes_arr)
    binary.seek(0)
    return binary


# Dump traceback as string
def get_traceback(*exc_info: list):
    exc_info = exc_info or sys.exc_info()
    tb_lines = traceback.format_exception(*exc_info)
    tb = "".join(tb_lines)
    return tb


# Save link image into an image object for use with pillow
async def pil_img_from_link(link):
    link = link[:link.rfind(".")] + ".png?size=256"
    async with globals.http.get(link) as req:
        img_bytes = await req.read()
    img = Image.open(bytes_to_binary_object(img_bytes))
    return img


# Draw text at coords with max width
def draw_text(draw, font, text, color, position, max_width, alignment="lt"):
    if font.getsize(text)[0] > max_width:
        cutoff = 1
        while font.getsize(text[:-cutoff] + "...")[0] > max_width:
            cutoff += 1
        draw.text(position, text[:-cutoff] + "...", fill=color, font=font, anchor=alignment)
    else:
        draw.text(position, text, fill=color, font=font, anchor=alignment)


# Get trophy count for user to draw correct amount of shards
def get_trophy_amount(user):
    count = 0
    for role in user.roles:
        if role.id in globals.TROPHY_ROLES:
            count += 1
    return count


# Find what bar to use based on percentage to next level
def get_bar_index_from_lvl_percent(percent):
    return int(str(percent // 10**2 % 10) + str(percent // 10**1 % 10))


# Check if user has a role id
def user_has_a_role(user: discord.Member, roles):
    # Current guild
    for role in user.roles:
        if role.id in roles:
            return True
    # Try all guilds
    for guild in globals.bot.guilds:
        if guild.id == user.guild.id:
            # Ignore guild we already checked
            continue
        member = guild.get_member(user.id)
        if member:
            for role in member.roles:
                if role.id in roles:
                    return True
    return False


# Check if user is staff
def is_staff(user):
    return user.id == globals.ADMIN_ID or user_has_a_role(user, globals.STAFF_ROLE_IDS) or user.id == globals.bot.user.id


# Fuzzy string match for commands
def get_best_command_match(name):
    cmd_list = []
    for cmd in globals.bot.commands:
        cmd_list.append(cmd.name.lower())
        for alias in cmd.aliases:
            cmd_list.append(alias.lower())
    results = [result[0] for result in process.extract(name, cmd_list, scorer=fuzz.ratio, limit=1)]
    return results[0]


# Format time elapsed from bot start
def time_from_start():
    now = datetime.datetime.utcnow()
    elapsed_seconds = (now - globals.start_dt).total_seconds()
    return str(datetime.timedelta(seconds=int(elapsed_seconds)))


# Convert byte size amount into human readable format
def pretty_size(size, precision=0):
    suffixes = ['B','KB','MB','GB','TB']
    suffix_index = 0
    while size > 1000 and suffix_index < 4:
        suffix_index += 1
        size = size / 1000
    return "%.*f%s" % (precision, size, suffixes[suffix_index])


# Hybrid group decorator that syncs aliases with slashcommands
def hybgroup(bot, slash_aliases=True, **kwargs):
    def decorator(func):
        _app_groups = []
        extras = kwargs.pop("extras", {})
        extras.update({
            "_app_groups": _app_groups
        })
        group = commands.group(extras=extras, **kwargs)(func)
        extras.update({
            "_group": group
        })
        short_desc = kwargs.get("description", "").split("\n")[0][:99] or discord.utils.MISSING
        for alias in [kwargs.get("name", discord.utils.MISSING)] + (kwargs.get("aliases", []) if slash_aliases else []):
            # Rename
            if alias is discord.utils.MISSING:
                alias = group.name
            # Create group
            if alias == group.name:
                desc = short_desc
            else:
                desc = f"Alias for /{group.name}. "
                if short_desc is not discord.utils.MISSING:
                    desc += ". " + short_desc[:99 - len(desc)]
            try:
                app_group = app_commands.Group(name=alias, description=desc, extras=extras)
                bot.tree.add_command(app_group)
                _app_groups.append(app_group)
            except app_commands.errors.CommandLimitReached:
                globals.log.warning(f"Command limit reached! Failed to add /{alias} for group {globals.BOT_PREFIX.lower()}{group.name}")
        return group
    return decorator


# Hybrid command decorator that syncs aliases, checks and cooldowns with slashcommands
def hybcommand(bot, group=None, slash_aliases=True, check_func=None, check_title=None, check_desc=None, cooldown_rate=None, cooldown_time=None, cooldown_key=None, cooldown_title=None, cooldown_desc=None, **kwargs):
    def decorator(func):
        _app_commands = []
        extras = kwargs.pop("extras", {})
        extras.update({
            "_app_commands": _app_commands,
            "check_title": check_title,
            "check_desc": check_desc,
            "cooldown_title": cooldown_title,
            "cooldown_desc": cooldown_desc
        })
        if group:
            command = group.command(extras=extras, **kwargs)(func)
        else:
            command = commands.command(extras=extras, **kwargs)(func)
        extras.update({
            "_command": command
        })
        if cooldown_rate:
            async def app_cooldown_key(interaction):
                ctx = await commands.Context.from_interaction(interaction)
                return cooldown_key(ctx)
            cooldown_mapping = {}
            def cooldown_factory(ctx):
                key = cooldown_key(ctx)
                if key not in cooldown_mapping:
                    cooldown_mapping[key] = app_commands.Cooldown(rate=cooldown_rate, per=cooldown_time)
                return cooldown_mapping[key]
            async def app_cooldown_factory(interaction):
                key = await app_cooldown_key(interaction)
                if key not in cooldown_mapping:
                    cooldown_mapping[key] = app_commands.Cooldown(rate=cooldown_rate, per=cooldown_time)
                return cooldown_mapping[key]
            cooldown = commands.dynamic_cooldown(cooldown=cooldown_factory, type=cooldown_key)
            app_cooldown = app_commands.checks.dynamic_cooldown(factory=app_cooldown_factory, key=app_cooldown_key)
            cooldown(command)
        if check_func:
            async def app_check_func(interaction):
                ctx = await commands.Context.from_interaction(interaction)
                return check_func(ctx)
            check = commands.check(check_func)
            app_check = app_commands.check(app_check_func)
            check(command)
        short_desc = kwargs.get("description", "").split("\n")[0][:99] or discord.utils.MISSING
        # Get source and remove decorator(s)
        lines = inspect.getsourcelines(func)[0]
        for i, line in enumerate(lines):
            if line.lstrip().startswith("async def "):
                lines = lines[i:]
                break
        # Remove indentation
        while all(line.startswith(" ") for line in lines):
            for i in range(len(lines)):
                lines[i] = lines[i][1:]
        source = "".join(lines)
        # Parse and manipulate
        ast_tree = ast.parse(source)
        fn = ast_tree.body[0]
        fn.args.args.pop(0)  # Remove "self"
        convert = ast.parse("ctx = await commands.Context.from_interaction(ctx)").body[0]
        fn.body.insert(0, convert)  # Interaction to Context
        for alias in [kwargs.get("name", discord.utils.MISSING)] + (kwargs.get("aliases", []) if slash_aliases else []):
            # Rename
            if alias is discord.utils.MISSING:
                alias = command.name
            fn.name = f"_{command.name}_{alias}"
            # Reassemble
            code = compile(ast_tree,"<string>", mode='exec')
            env = func.__globals__  # Imports and other shenanigans
            exec(code, env)
            new_func = env[fn.name]
            # Create command
            if alias == command.name:
                desc = short_desc
            else:
                desc = f"Alias for /{command.name}"
                if short_desc is not discord.utils.MISSING:
                    desc += ". " + short_desc[:99 - len(desc)]
            try:
                if group:
                    for app_group in group.extras.get("_app_groups", []):
                        app_command = app_group.command(name=alias, description=desc, extras=extras)(new_func)
                        if cooldown_rate:
                            app_cooldown(app_command)
                        if check_func:
                            app_check(app_command)
                else:
                    app_command = bot.tree.command(name=alias, description=desc, extras=extras)(new_func)
                    if cooldown_rate:
                        app_cooldown(app_command)
                    if check_func:
                        app_check(app_command)
                _app_commands.append(app_command)
            except app_commands.errors.CommandLimitReached:
                globals.log.warning(f"Command limit reached! Failed to add /{alias} for command {globals.BOT_PREFIX.lower()}{command.name}")
        return command
    return decorator


# Streamlined embeds
def custom_embed(guild, *, title="", description="", fields=[], thumbnail=None, image=None, add_timestamp=True):
    if add_timestamp:
        embed_to_send = (discord.Embed(title=title,
                                       description=description,
                                       color=discord.Color(0xEDE400),
                                       timestamp=datetime.datetime.utcnow())
                                       .set_footer(text=guild.name,
                                                   icon_url=getattr(guild.icon, "url", None)))
    else:
        embed_to_send = (discord.Embed(title=title,
                                       description=description,
                                       color=discord.Color(0xEDE400))
                                       .set_footer(text=guild.name,
                                                   icon_url=getattr(guild.icon, "url", None)))
    if image:
        embed_to_send.set_image(url=image)
    if thumbnail:
        embed_to_send.set_thumbnail(url=str(thumbnail))
    for field in fields:
        embed_to_send.add_field(name=field[0], value=field[1], inline=field[2])
    return embed_to_send


# Upload image to imgur and retrieve link
async def imgur_image_upload(img: bytes):
    # Convert to jpeg
    img_buffer = io.BytesIO(img)
    conv_buffer = io.BytesIO()
    Image.open(img_buffer).convert().save(conv_buffer, "png")
    conv_buffer.seek(0)
    img = conv_buffer.read()
    # Handle large files
    size = len(img)
    maximum = 10000000
    if size > maximum:
        raise errors.FileTooBig(size=size, maximum=maximum)
    # Actual request
    try:
        resp = None
        async with globals.http.post("https://api.imgur.com/3/image",
                                     headers={
                                         "Authorization": f"Client-ID {globals.IMGUR_CLIENT_ID}"
                                     },
                                     data = {
                                         'image': img
                                     }) as req:
            resp = await req.json()
            if not req.ok:
                globals.log.error(resp)
        return resp["data"]["link"]
    except Exception as exc:
        raise errors.ImgurError(exc_info=sys.exc_info(), resp=resp) from exc


# Defer slash response with ephemeral calculation
async def defer(ctx, ephemeral=None):
    if ctx.channel.id in (globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or []):
        ephemeral = True
    elif ephemeral is None:
        ephemeral = bool(ctx.channel.id not in globals.BLACKLISTED_CHANNELS_IDS)
    await ctx.defer(ephemeral=ephemeral)


# Cleaner reply function
async def embed_reply(ctx, *, content="", title="", description="", fields=[], thumbnail=None, image=None, add_timestamp=True, ephemeral=None, **kwargs):
    embed_to_send = custom_embed(ctx.guild,
                                 title=title,
                                 description=description,
                                 fields=fields,
                                 thumbnail=thumbnail,
                                 image=image,
                                 add_timestamp=add_timestamp)
    if ctx.channel.id in (globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or []):
        ephemeral = True
    elif ephemeral is None:
        ephemeral = bool(ctx.channel.id not in globals.BLACKLISTED_CHANNELS_IDS)
    if ephemeral or ephemeral is not bool(ephemeral):
        if ephemeral is bool(ephemeral):
            ephemeral = 5
        if getattr(ctx, "interaction", None):
            kwargs["ephemeral"] = True
        else:
            kwargs["delete_after"] = ephemeral
    ret = await ctx.reply(content,
                          embed=embed_to_send,
                          **kwargs)
    if ephemeral is not bool(ephemeral) and not getattr(ctx, "interaction", None):
        async def delete_later():
            await asyncio.sleep(ephemeral)
            await getattr(ctx, "message", ctx).delete()
        asyncio.get_event_loop().create_task(delete_later())
    return ret


# Get all possible case variations for a string
def case_insensitive(text):
    return list(set(map(''.join, itertools.product(*((char.upper(), char.lower()) for char in text)))))


# Check if command is related to requests
def is_requests_command(content):
    prfx = globals.BOT_PREFIX.lower()
    cog = globals.bot.get_cog("Requests")
    commands = cog.get_commands()
    command_names = []
    for command in commands:
        command_names.append(prfx + command.name.lower() + " ")
        for alias in command.aliases:
            command_names.append(prfx + alias.lower() + " ")
    for command in command_names:
        if content.startswith(command):
            return True
    return False


def strip_argument(arg):
    return str(arg).strip(" \n\t[]")


async def manage_icon_role_for_user(user: discord.Member):
    icon_sets = globals.ICON_ROLE_IDS.get(str(user.guild.id))
    if not icon_sets:
        return
    user_role_ids = [role.id for role in user.roles]
    for user_role_id in reversed(user_role_ids):
        for icon_set in icon_sets:
            if user_role_id in icon_set["roles"]:
                user_level_xp, _, _ = await db.get_user_xp(user.id)
                user_level = xp.xp_to_lvl(user_level_xp)[0]
                icon_role_id = None
                while user_level > 0:
                    icon_role_id = icon_set.get(str(user_level))
                    if icon_role_id:
                        break
                    user_level -= 1
                if icon_role_id and icon_role_id not in user_role_ids:
                    await user.add_roles(discord.Object(icon_role_id))
                icon_roles_to_remove = []
                for icon_set_ in icon_sets:
                    for value in icon_set_.values():
                        if isinstance(value, int):
                            if value not in user_role_ids or value == icon_role_id:
                                continue
                            icon_roles_to_remove.append(discord.Object(value))
                if icon_roles_to_remove:
                    await user.remove_roles(*icon_roles_to_remove)
                return
