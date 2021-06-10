from fuzzywuzzy import process, fuzz
from PIL import Image, ImageFont
import datetime
import discord
import asqlite
import aiohttp
import base64
import zlib
import json
import sys
import io
import os

# Local imports
from modules import db, globals


# Get database
async def get_db():
    async with aiohttp.ClientSession() as client:
        async with client.post('https://write.as/api/auth/login',
                               headers={
                                   'Content-Type': 'application/json'
                               },
                               data=json.dumps({
                                   "alias": globals.WRITE_AS_USER,
                                   "pass": globals.WRITE_AS_PASS
                               })) as req:
            globals.write_as_token = (await req.json())["data"]["access_token"]
        async with client.get(f"https://write.as/{globals.WRITE_AS_USER}/{globals.WRITE_AS_POST_ID}.txt") as req:
            db_data = await req.text()
        decoded = base64.b85decode(db_data.encode("utf-8"))
        decompressed = zlib.decompress(decoded)
        with open('db.sqlite3', 'wb') as f:
            f.write(decompressed)
        globals.db = await asqlite.connect("db.sqlite3")
        await db.init_db()
        print("Fetched DB!")


# Save database
async def save_db():
    if globals.db is not None:
        await globals.db.commit()
        with open('db.sqlite3', 'rb') as f:
            raw = f.read()
        compressed = zlib.compress(raw, zlib.Z_BEST_COMPRESSION)
        encoded = base64.b85encode(compressed)
        db_data = encoded.decode("utf-8")
        async with aiohttp.ClientSession() as client:
            async with client.post(f'https://write.as/api/collections/{globals.WRITE_AS_USER}/posts/{globals.WRITE_AS_POST_ID}',
                                   headers={
                                       'Authorization': f'Token {globals.write_as_token}',
                                       'Content-Type': 'application/json'
                                   },
                                   data=json.dumps({
                                       "body": db_data,
                                       "font": "code"
                                   })) as req:
                if not req.ok:
                    print(f"Failed to save config! Code: {req.status}, Message: {await req.text()}")
                    return False
                return True


# Restart the bot, dyno restart on heroku
async def restart():
    if os.environ.get("DYNO"):
        async with aiohttp.ClientSession() as client:
            async with client.delete(f'https://api.heroku.com/apps/altiera/dynos/{os.environ["DYNO"]}',
                                     headers={
                                         'Authorization': f'Bearer {globals.HEROKU_TOKEN}',
                                         'Accept':        f'application/vnd.heroku+json; version=3'
                                     }) as req:
                response = await req.text()
                if not req.ok:
                    admin = globals.bot.get_user(globals.ADMIN_ID)
                    if admin:
                        await admin.send(embed=custom_embed(list(globals.bot.guilds)[0],
                                                            title="Failed to Restart!",
                                                            description=response,
                                                            fields=[
                                                                ["Status:", f"{req.status}", True]
                                                            ]))
    else:
        import main  # I know, I know, please Lord forgive me
        os.execl(sys.executable, 'python', main.__file__, *sys.argv[1:])


# Setup persistent image components
def setup_persistent_components():
    globals.font47 = ImageFont.truetype("assets/square.ttf", 47)
    globals.font35 = ImageFont.truetype("assets/square.ttf", 35)
    globals.font30 = ImageFont.truetype("assets/square.ttf", 30)
    globals.font24 = ImageFont.truetype("assets/square.ttf", 24)
    globals.font20 = ImageFont.truetype("assets/square.ttf", 20)
    globals.font16 = ImageFont.truetype("assets/square.ttf", 16)

    globals.default_avatar = Image.open('assets/default_avatar.png').resize((200, 200))

    globals.overlays_default = Image.open('assets/overlays/default.png')
    globals.overlays_staff =   Image.open('assets/overlays/staff.png'  )
    globals.overlays_admin =   Image.open('assets/overlays/admin.png'  )

    globals.shards_orange = Image.open("assets/shards/orange.png").resize((33, 28))
    globals.shards_white =  Image.open("assets/shards/white.png" ).resize((33, 28))
    globals.shards_teal =   Image.open("assets/shards/teal.png"  ).resize((33, 28))

    globals.bars = {}
    for color in ["blue_white", "orange_white", "teal_white", "white_blue", "white_orange"]:
        globals.bars[color] = []
        for i in range(11):
            globals.bars[color].append(Image.open(f"assets/bars/{color}/{i}.png"))

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


# Save link image into an image object for use with pillow
async def pil_img_from_link(link):
    link = link[:link.rfind(".")] + ".png?size=256"
    async with aiohttp.ClientSession() as client:
        async with client.get(link) as req:
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


# Check if user has role id
def user_has_role(user, role_id):
    return role_id in [role.id for role in user.roles]


# Check if user has a role id
def user_has_a_role(user, roles):
    for role in user.roles:
        if role.id in roles:
            return True
    return False


# Check if user is staff
def is_staff(user):
    return user.id == globals.ADMIN_ID or user_has_a_role(user, globals.STAFF_ROLE_IDS)


# Find member, ensure xp and return value
async def xp_from_name(ctx, name, type):
    member_id = ctx.guild.get_member_named(name).id
    return (await db.get_user_xp(member_id))[type]


# Fuzzy string match for usernames
async def get_best_member_match(ctx, target):
    name_list = []
    for user in ctx.guild.members:
        name_list.append(user.name)
        if user.nick:
            name_list.append(user.nick)
    results = [result[0] for result in process.extract(target, name_list, scorer=fuzz.ratio, limit=20)]
    sort_helper = [(await xp_from_name(ctx, name, 'level'), name) for name in results]
    sort_helper.sort(key=lambda item: item[0], reverse=True)
    return ctx.guild.get_member_named(sort_helper[0][1])


# Format time elapsed from bot start
def time_from_start():
    now = datetime.datetime.utcnow()
    elapsed_seconds = (now - globals.start_dt).total_seconds()
    return str(datetime.timedelta(seconds=int(elapsed_seconds)))


# Format time until next bot restart
def time_to_restart():
    now = datetime.datetime.utcnow()
    missing_seconds = (globals.restart_dt - now).total_seconds()
    return str(datetime.timedelta(seconds=int(missing_seconds)))


# Convert byte size amount into human readable format
def pretty_size(size, precision=0):
    suffixes = ['B','KB','MB','GB','TB']
    suffix_index = 0
    while size > 1024 and suffix_index < 4:
        suffix_index += 1
        size = size / 1024.0
    return "%.*f%s" % (precision, size, suffixes[suffix_index])


# Streamlined embeds
def custom_embed(guild, *, title="", description="", fields=[], thumbnail=None, image=None, add_timestamp=True):
    if add_timestamp:
        embed_to_send = (discord.Embed(title=title,
                                    description=description,
                                    color=discord.Color(0xEDE400),
                                    timestamp=datetime.datetime.utcnow())
                                    .set_footer(text=guild.name,
                                                icon_url=guild.icon_url))
    else:
        embed_to_send = (discord.Embed(title=title,
                                    description=description,
                                    color=discord.Color(0xEDE400))
                                    .set_footer(text=guild.name,
                                                icon_url=guild.icon_url))
    if image:
        embed_to_send.set_image(url=image)
    if thumbnail:
        embed_to_send.set_thumbnail(url=str(thumbnail))
    for field in fields:
        embed_to_send.add_field(name=field[0], value=field[1], inline=field[2])
    return embed_to_send


# Cleaner reply function
async def embed_reply(ctx, *, content="", title="", description="", fields=[], thumbnail=None, image=None, add_timestamp=True):
    embed_to_send = custom_embed(ctx.guild, title=title, description=description, fields=fields, thumbnail=thumbnail, image=image, add_timestamp=add_timestamp)
    await ctx.reply(content,
                    embed=embed_to_send)
