from fuzzywuzzy import process, fuzz
from PIL import Image, ImageFont
import requests
import datetime
import discord
import atexit
import json
import time
import io

# Local imports
from modules import globals, xp


# Get config
def get_config():
    r = requests.post('https://write.as/api/auth/login',
                      headers={
                          'Content-Type': 'application/json'
                      },
                      data=json.dumps({
                          "alias": globals.WRITE_AS_USER,
                          "pass": globals.WRITE_AS_PASS
                      }))
    globals.write_as_token = json.loads(r.text)["data"]["access_token"]
    globals.config = json.loads(requests.get(f"https://write.as/{globals.WRITE_AS_USER}/{globals.WRITE_AS_POST_ID}.txt").text)
    print("Fetched config!")


# Save config
@atexit.register
def save_config():
    if globals.config is not None:
        globals.config["time"] = time.time()
        r = requests.post(f'https://write.as/api/collections/{globals.WRITE_AS_USER}/posts/{globals.WRITE_AS_POST_ID}',
                          headers={
                              'Authorization': f'Token {globals.write_as_token}',
                              'Content-Type': 'application/json'
                          },
                          data=json.dumps({
                              "body": json.dumps(globals.config),
                              "font": "code"
                          }))
        if not r.ok:
            print(f"Failed to save config! Code: {r.status_code}, Message: {r.text}")
            return False
        return True


# Setup persistent image components
def setup_persistent_components():
    globals.font47 = ImageFont.truetype("assets/square.ttf", 47)
    globals.font35 = ImageFont.truetype("assets/square.ttf", 35)
    globals.font30 = ImageFont.truetype("assets/square.ttf", 30)
    globals.font24 = ImageFont.truetype("assets/square.ttf", 24)
    globals.font20 = ImageFont.truetype("assets/square.ttf", 20)
    globals.font16 = ImageFont.truetype("assets/square.ttf", 16)

    globals.default_avatar = Image.open('assets/default_avatar.png').resize((200, 200))

    globals.overlay = Image.open('assets/overlay.png')
    globals.staff_overlay = Image.open('assets/staff_overlay.png')

    globals.shard_orange = Image.open("assets/shard_orange.png").resize((33, 28))
    globals.shard_white = Image.open("assets/shard_white.png").resize((33, 28))

    globals.bars = {}
    for color in ["blue", "orange", "white"]:
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
def pil_img_from_link(link):
    link = link[:link.rfind(".")] + ".png?size=256"
    r = requests.get(link)
    img = Image.open(bytes_to_binary_object(r.content))
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


# Check for staff role
def is_staff(user):
    return globals.STAFF_ROLE_ID in [role.id for role in user.roles]


# Find member, ensure xp and return value
def xp_from_name(ctx, name, index):
    member_id_str = str(ctx.guild.get_member_named(name).id)
    xp.ensure_user_data(member_id_str)
    globals.config[member_id_str][index]


# Fuzzy string match for usernames
def get_best_member_match(ctx, target):
    name_list = []
    for user in ctx.guild.members:
        name_list.append(user.name)
        if user.nick:
            name_list.append(user.nick)
    results = [result[0] for result in process.extract(target, name_list, scorer=fuzz.ratio, limit=20)]
    results.sort(key=lambda name: xp_from_name(ctx, name, 0), reverse=True)
    return ctx.guild.get_member_named(results[0])


# Streamlined embeds
def custom_embed(guild, *, title="", description="", fields=[], thumbnail=None, image=None):
    embed_to_send = (discord.Embed(title=title,
                                  description=description,
                                  color=discord.Color(0xEDE400),
                                  timestamp=datetime.datetime.utcnow())
                                  .set_footer(text=guild.name,
                                              icon_url=guild.icon_url))
    if image:
        embed_to_send.set_image(url=image)
    elif thumbnail:
        embed_to_send.set_thumbnail(url=thumbnail)
    for field in fields:
        embed_to_send.add_field(name=field[0], value=field[1], inline=field[2])
    return embed_to_send


# Cleaner reply function
async def embed_reply(ctx, *, content="", title="", description="", fields=[], thumbnail=None, image=None):
    embed_to_send = custom_embed(ctx.guild, content=content, title=title, description=description, fields=fields, thumbnail=thumbnail, image=image)
    await ctx.reply(content,
                    embed=embed_to_send)
