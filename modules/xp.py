import time
import asyncio

# Local imports
from modules import utils, globals

cooldowns = {}


def process_xp(message):
    if not message.author:
        return
    if message.author.bot:
        return
    try:
        cooldowns[message.author.id]
        return
    except KeyError:
        cooldowns[message.author.id] = time.time() + globals.XP_COOLDOWN


async def tick_cooldowns():
    while True:
        await asyncio.sleep(5)
        to_remove = []
        for user_id in cooldowns:
            if cooldowns[user_id] < time.time():
                to_remove.append(user_id)
        for user_id in to_remove:
            del cooldowns[user_id]


asyncio.get_event_loop().create_task(tick_cooldowns())
