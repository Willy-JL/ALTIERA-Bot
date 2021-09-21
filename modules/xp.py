from PIL import Image, ImageDraw
import discord
import asyncio
import time
import io

# Local imports
from modules import globals, db, utils

cooldowns         = {}
contrib_cooldowns = {}


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
    level_xp, cred_xp, assistance_xp = await db.get_user_xp(message.author.id)
    level      = xp_to_lvl(level_xp     )[0]
    cred       = xp_to_lvl(cred_xp      )[0]
    assistance = xp_to_lvl(assistance_xp)[0]
    # Regular XP
    level_xp_to_add      = 0
    cred_xp_to_add       = 0
    assistance_xp_to_add = 0
    try:
        cooldowns[message.author.id]
    except KeyError:
        level_xp_to_add += globals.XP_AMOUNT  # Server level for anyone
        if utils.user_has_a_role(message.author, globals.MODDER_ROLE_IDS):
            if (message.channel.category.id if message.channel.category else 0) in globals.MODDER_CATEGORY_IDS:
                cred_xp_to_add += globals.XP_AMOUNT  # Server cred if modder in modder categories
            if (message.channel.category.id if message.channel.category else 0) in globals.ASSISTANCE_CATEGORY_IDS or "support" in message.channel.name:
                assistance_xp_to_add += (2 * globals.XP_AMOUNT)  # Double assistance if modder and assistance categories
        elif (message.channel.category.id if message.channel.category else 0) in globals.ASSISTANCE_CATEGORY_IDS or "support" in message.channel.name:
            assistance_xp_to_add += globals.XP_AMOUNT  # Assistance if assistance categories
        level_xp, cred_xp, assistance_xp = await db.add_user_xp(message.author.id, level=level_xp_to_add, cred=cred_xp_to_add, assistance=assistance_xp_to_add)
        cooldowns[message.author.id] = time.time() + globals.XP_COOLDOWN
    # Contrib xp (e.g. tutorial, resource, mod release...)
    added_contrib_boost = False
    level_xp_to_add  = 0
    cred_xp_to_add   = 0
    assistance_xp_to_add = 0
    if message.channel.id in globals.CONTRIB_CHANNELS_IDS:
        try:
            contrib_cooldowns[message.author.id]
        except KeyError:
            cred_xp_to_add += globals.CONTRIB_AMOUNT  # Server cred boost
            level_xp, cred_xp, assistance_xp = await db.add_user_xp(message.author.id, level=level_xp_to_add, cred=cred_xp_to_add, assistance=assistance_xp_to_add)
            contrib_cooldowns[message.author.id] = time.time() + globals.CONTRIB_COOLDOWN
            added_contrib_boost = True
    # Notify levelups
    new_level      = xp_to_lvl(level_xp     )[0]
    new_cred       = xp_to_lvl(cred_xp      )[0]
    new_assistance = xp_to_lvl(assistance_xp)[0]
    if new_level > level:
        await notify_level_up(message, "level",      level,      new_level     )
    if new_cred > cred:
        await notify_level_up(message, "cred",       cred,       new_cred      )
    if new_assistance > assistance:
        await notify_level_up(message, "assistance", assistance, new_assistance)
    # Revert contrib boost if message is deleted
    if added_contrib_boost:
        try:
            await globals.bot.wait_for('message_delete', check=lambda msg: message == msg, timeout=600)
            # Message was deleted, remove boost
            await db.add_user_xp(message.author.id, level=-level_xp_to_add, cred=-cred_xp_to_add, assistance=-assistance_xp_to_add)
            while globals.ticking_cooldowns:
                await asyncio.sleep(0.25)
            del contrib_cooldowns[message.author.id]
        except asyncio.TimeoutError:
            # Message not deleted, leave boost
            pass


async def notify_level_up(message, xp_type, old_lvl, new_lvl):
    if str(message.guild.id) in globals.LEVEL_NOTIF_CHANNEL_IDS:
        # Setup image foundation
        img = Image.open(f"assets/levelup/{xp_type}_bg.png")
        draw = ImageDraw.Draw(img)
        # Draw user avatar
        if str(message.author.avatar_url).startswith("https://cdn.discordapp.com/embed/avatars"):
            avatar = globals.default_avatar.resize((84, 84))
        else:
            avatar = (await utils.pil_img_from_link(str(message.author.avatar_url))).resize((84, 84,))
        try:
            img.paste(avatar, (5, 5,), avatar)
        except ValueError:
            img.paste(avatar, (5, 5,))
        # Apply base overlay
        img.paste(globals.levelups[xp_type]["overlay"], (0, 0,), globals.levelups[xp_type]["overlay"])
        # Draw old and new level values
        utils.draw_text(draw, globals.font47, f"{old_lvl}", globals.levelups[xp_type]["color"], (344, 56,), 999)
        utils.draw_text(draw, globals.font47, f"{new_lvl}", globals.levelups[xp_type]["color"], (530, 56,), 999)
        # Send image
        binary = io.BytesIO()
        img.save(binary, format="PNG")
        binary.seek(0)
        channel = message.guild.get_channel(globals.LEVEL_NOTIF_CHANNEL_IDS[str(message.guild.id)])
        await channel.send(f"<@!{message.author.id}>", file=discord.File(binary, filename=f"levelup_{xp_type}.png"), allowed_mentions=discord.AllowedMentions(users=[]))


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
