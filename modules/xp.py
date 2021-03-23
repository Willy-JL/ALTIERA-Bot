import io
import time
import asyncio
import discord
from PIL import Image, ImageDraw

# Local imports
from modules import globals, utils

cooldowns = {}
contrib_cooldowns = {}


# Create config entry for user if it doesn't exist
def ensure_user_data(user_id):
    if not user_id in globals.config:
        globals.config[user_id] = [0, 0, 0]


# Convert xp number to level, missing xp and needed xp for next level
def xp_to_lvl(xp):
    level = 0
    xp_per_level = 1000
    while xp >= 0:
        reduce = False
        if xp >= xp_per_level:
            level += 1
            reduce = True
        xp -= xp_per_level
        if reduce:
            xp_per_level += 1000
    if level >= 100:
        return 100, 0, 1
    # return lvl, missing, needed
    return level, -xp, xp_per_level


async def process_xp(message):
    if not message.author:
        return
    if message.author.bot:
        return
    if message.channel.id in globals.BLACKLISTED_CHANNELS_IDS:
        return
    ensure_user_data(str(message.author.id))
    level =  xp_to_lvl(globals.config[str(message.author.id)][0])[0]
    cred =   xp_to_lvl(globals.config[str(message.author.id)][1])[0]
    assist = xp_to_lvl(globals.config[str(message.author.id)][2])[0]
    # Regular XP
    try:
        cooldowns[message.author.id]
    except KeyError:
        globals.config[str(message.author.id)][0] += globals.XP_AMOUNT  # Server level for anyone
        if globals.MODDER_ROLE_ID in [role.id for role in message.author.roles]:
            if (message.channel.category.id if message.channel.category else 0) in globals.MODDER_CATEGORY_IDS:
                globals.config[str(message.author.id)][1] += globals.XP_AMOUNT  # Server cred if modder in modder categories
            if (message.channel.category.id if message.channel.category else "") == globals.ASSISTANCE_CATEGORY_ID:
                globals.config[str(message.author.id)][2] += (2 * globals.XP_AMOUNT)  # Double assistance if modder and assistance category
        elif (message.channel.category.id if message.channel.category else "") == globals.ASSISTANCE_CATEGORY_ID:
            globals.config[str(message.author.id)][2] += globals.XP_AMOUNT  # Assistance if assistance category
        cooldowns[message.author.id] = time.time() + globals.XP_COOLDOWN
    # Contrib xp (e.g. tutorial, resource, mod release...)
    added_contrib_boost = False
    if message.channel.id in globals.CONTRIB_CHANNELS_IDS:
        try:
            contrib_cooldowns[message.author.id]
        except KeyError:
            globals.config[str(message.author.id)][1] += globals.CONTRIB_AMOUNT  # Server cred boost
            contrib_cooldowns[message.author.id] = time.time() + globals.CONTRIB_COOLDOWN
            added_contrib_boost = True
    new_level =  xp_to_lvl(globals.config[str(message.author.id)][0])[0]
    new_cred =   xp_to_lvl(globals.config[str(message.author.id)][1])[0]
    new_assist = xp_to_lvl(globals.config[str(message.author.id)][2])[0]
    if new_level > level:
        await notify_level_up(message, "level",      level,  new_level )
    if new_cred > cred:
        await notify_level_up(message, "cred",       cred,   new_cred  )
    if new_assist > assist:
        await notify_level_up(message, "assistance", assist, new_assist)
    if added_contrib_boost:
        try:
            await globals.bot.wait_for('message_delete', check=lambda msg: message == msg, timeout=600)
            # Message was deleted, remove boost
            globals.config[str(message.author.id)][1] -= globals.CONTRIB_AMOUNT
            while globals.ticking_cooldowns:
                await asyncio.sleep(0.25)
            del contrib_cooldowns[message.author.id]
        except TimeoutError:
            # Message not deleted, leave boost
            pass


async def notify_level_up(message, xp_type, old_lvl, new_lvl):
    # Setup image foundation
    img = Image.open(f"assets/levelup/{xp_type}_bg.png")
    draw = ImageDraw.Draw(img)
    # Draw user avatar
    if str(message.author.avatar_url).startswith("https://cdn.discordapp.com/embed/avatars"):
        avatar = globals.default_avatar.resize((84, 84))
    else:
        avatar = utils.pil_img_from_link(str(message.author.avatar_url)).resize((84, 84))
    try:
        img.paste(avatar, (5, 5), avatar)
    except ValueError:
        img.paste(avatar, (5, 5))
    # Apply base overlay
    img.paste(globals.levelups[xp_type]["overlay"], (0, 0), globals.levelups[xp_type]["overlay"])
    # Draw old and new level values
    utils.draw_text(draw, globals.font47, f"{old_lvl}", globals.levelups[xp_type]["color"], (344, 56), 999)
    utils.draw_text(draw, globals.font47, f"{new_lvl}", globals.levelups[xp_type]["color"], (530, 56), 999)

    binary = io.BytesIO()
    img.save(binary, format="PNG")
    binary.seek(0)
    channel = message.guild.get_channel(globals.LEVEL_NOTIF_CHANNEL_ID)
    await channel.send(f"<@!{message.author.id}>", file=discord.File(binary, filename=f"levelup_{xp_type}.png"))


async def tick_cooldowns():
    while True:
        await asyncio.sleep(5)
        globals.ticking_cooldowns = True
        to_remove = []
        for user_id in cooldowns:
            if cooldowns[user_id] < time.time():
                to_remove.append(user_id)
        for user_id in to_remove:
            del cooldowns[user_id]
        to_remove = []
        for user_id in contrib_cooldowns:
            if contrib_cooldowns[user_id] < time.time():
                to_remove.append(user_id)
        for user_id in to_remove:
            del contrib_cooldowns[user_id]
        globals.ticking_cooldowns = False


asyncio.get_event_loop().create_task(tick_cooldowns())
