from discord.ext import commands
from typing import Union
import datetime
import discord
import random
import time

# Local imports
from modules import globals, utils, xp


rep_cooldown_users   = set()
daily_cooldown_users = set()


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["diceroll", "rolldice", "roll"])
    async def dice(self, ctx, arg1: str = None, arg2: str = None):
        if arg1 is not None:
            try:
                max = int(arg1)
            except (ValueError, TypeError):
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide a valid number!")
                return
        else:
            max = 6

        if arg2 is not None:
            throws = max
            try:
                max = int(arg2)
            except (ValueError, TypeError):
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide valid numbers!")
                return
        else:
            throws = 1

        throws_adjusted = False
        max_adjusted = False
        if throws > 10:
            throws = 10
            throws_adjusted = True
        if throws < 1:
            throws = 1
            throws_adjusted = True
        if max > 100:
            max = 100
            max_adjusted = True
        if max < 2:
            max = 2
            max_adjusted = True

        result = 0
        rolls = []
        for _ in range(throws):
            roll = random.randint(1, max)
            result += roll
            rolls.append(str(roll))
        await utils.embed_reply(ctx,
                                title=f"🎲 Dice roll!",
                                description=f'Throws: {throws}{" (adjusted)" if throws_adjusted else ""}\n'
                                            f'Max: {max}{" (adjusted)" if max_adjusted else ""}\n'
                                            f'\n'
                                            f'Result:  __**{str(result)}**__ ( `{", ".join(rolls)}` )',
                                add_timestamp=False)

    @commands.command(aliases=["reputation", "giverep", "givereputation"])
    async def rep(self, ctx, target: Union[discord.Member, discord.User, int, str] = None):
        if not str(ctx.author.id) in rep_cooldown_users:
            # Convert target input to discord.Member
            if not target:
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide a user to give reputation to!")
                return
            if isinstance(target, int):
                target = ctx.guild.get_member(target)
            elif isinstance(target, str):
                target = utils.get_best_member_match(ctx, target)
            elif isinstance(target, discord.User):
                target = ctx.guild.get_member(target.id)
            elif isinstance(target, discord.Member):
                pass
            else:
                await utils.embed_reply(ctx,
                                        title=f"💢 That is not a valid user!")
                return
            if not target:
                await utils.embed_reply(ctx,
                                        title=f"💢 That is not a valid user!")
                return
            if target.id == ctx.author.id:
                await utils.embed_reply(ctx,
                                        title=f"💢 Thats low even by your standards...")
                return
            # Actual command
            xp.ensure_user_data(str(target.id))
            globals.config[str(target.id)][1] += globals.REP_CRED_AMOUNT
            rep_cooldown_users.add(str(ctx.author.id))
            await utils.embed_reply(ctx,
                                    content=f"<@!{target.id}>",
                                    title=f"💌 You got some reputation!",
                                    description=f"<@!{ctx.author.id}> likes what you do and showed their gratitude by gifting you **{globals.REP_CRED_AMOUNT} server cred XP**!",
                                    thumbnail="https://cdn.discordapp.com/emojis/766042961929699358.png")
        else:
            await utils.embed_reply(ctx,
                                    title=f"💢 You're on cooldown!",
                                    description=f"You can only use that command once every **24 hours**!\n"
                                                f"You'll be able to use it again in roughly **{datetime.timedelta(seconds=int(86369-(time.time()-globals.start_timestamp)))}**")

    @commands.command(aliases=["riseandshine", "ijustwokeup", "gibreward", "claimdaily", "gibdaily"])
    async def daily(self, ctx):
        if not str(ctx.author.id) in daily_cooldown_users:
            xp.ensure_user_data(str(ctx.author.id))
            globals.config[str(ctx.author.id)][0] += globals.DAILY_LEVEL_AMOUNT
            daily_cooldown_users.add(str(ctx.author.id))
            await utils.embed_reply(ctx,
                                    title=f"📅 Daily reward claimed!",
                                    description=f"You just grabbed yourself a cool **{globals.DAILY_LEVEL_AMOUNT} server level XP**!\n"
                                                f"Come back in roughly **{datetime.timedelta(seconds=int(86369-(time.time()-globals.start_timestamp)))}** for more!",
                                    thumbnail=ctx.author.avatar_url)
        else:
            await utils.embed_reply(ctx,
                                    title=f"💢 It's called \"daily\" for a reason!",
                                    description=f"Come back in roughly **{datetime.timedelta(seconds=int(86369-(time.time()-globals.start_timestamp)))}** for your next daily reward")


def setup(bot):
    bot.add_cog(Commands(bot))
