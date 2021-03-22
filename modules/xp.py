import time
import asyncio

# Local imports
from modules import globals

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
    # Regular XP
    try:
        cooldowns[message.author.id]
    except KeyError:
        ensure_user_data(str(message.author.id))
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
    if message.channel.id in globals.CONTRIB_CHANNELS_IDS:
        try:
            contrib_cooldowns[message.author.id]
        except KeyError:
            ensure_user_data(str(message.author.id))
            globals.config[str(message.author.id)][1] += globals.CONTRIB_AMOUNT  # Server cred boost
            contrib_cooldowns[message.author.id] = time.time() + globals.CONTRIB_COOLDOWN
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
