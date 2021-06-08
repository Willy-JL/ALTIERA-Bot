from discord.ext import commands
from typing import Union
import datetime
import discord
import random
import time

# Local imports
from modules import db, globals, utils


rep_cooldown_users   = set()
daily_cooldown_users = set()


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["diceroll", "rolldice", "roll"])
    async def dice(self, ctx, arg1: str = None, arg2: str = None, arg3: str = None):
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

        if arg3 is not None:
            try:
                mod = int(arg3)
            except (ValueError, TypeError):
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide valid numbers!")
                return
        else:
            mod = 0

        throws_adjusted = False
        max_adjusted = False
        mod_adjusted = False
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
        if mod > 100:
            mod = 100
            mod_adjusted = True
        if mod < -100:
            mod = -100
            mod_adjusted = True

        result = 0
        rolls = []
        for _ in range(throws):
            roll = random.randint(1, max)
            result += roll
            rolls.append(str(roll))
        result += mod
        await utils.embed_reply(ctx,
                                title=f"🎲 Dice roll!",
                                description=f'Throws: {throws}{" (adjusted)" if throws_adjusted else ""}\n'
                                            f'Max: {max}{" (adjusted)" if max_adjusted else ""}\n'
                                            f'Modifier: {mod:+}{" (adjusted)" if mod_adjusted else ""}\n'
                                            f'\n'
                                            f'Result:  __**{str(result)}**__ ( `{", ".join(rolls)}{f", {mod:+}" if mod != 0 else ""}` )',
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
                target = await utils.get_best_member_match(ctx, target)
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
            await db.add_user_xp(target.id, cred=globals.REP_CRED_AMOUNT)
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
            await db.add_user_xp(ctx.author.id, level=globals.DAILY_LEVEL_AMOUNT)
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

    @commands.command(aliases=["cybcookie", "cybercookie"])
    async def cookie(self, ctx, target: Union[discord.Member, discord.User, int, str] = None):
        # Convert target input to discord.Member
        if not target:
            target = ctx.author
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            target = await utils.get_best_member_match(ctx, target)
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
            return
        # Actual command
        if target.id != ctx.author.id:
            await utils.embed_reply(ctx,
                                    content=f"<@!{target.id}>",
                                    title=f"🍪 CyberCookie!",
                                    description=f"<@!{ctx.author.id}> just gave you a delicious Cyber🤖Cookie🍪!\n"
                                                f"Eat it before it vaporizes you!",
                                    thumbnail="https://cdn.discordapp.com/emojis/766054797673496596.png")
        else:
            await utils.embed_reply(ctx,
                                    title=f"🍪 CyberCookie!",
                                    description=f"<@!{ctx.author.id}> doesn't have any friends yet so they treated themselves to a delicious Cyber🤖Cookie🍪!\n"
                                                f"Time to eagerly eat it in complete silence!",
                                    thumbnail="https://cdn.discordapp.com/emojis/766054797673496596.png")

    @commands.command(aliases=["spaceburrito", "galacticburrito"])
    async def burrito(self, ctx, target: Union[discord.Member, discord.User, int, str] = None):
        # Convert target input to discord.Member
        if not target:
            target = ctx.author
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            target = await utils.get_best_member_match(ctx, target)
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
            return
        # Actual command
        if target.id != ctx.author.id:
            await utils.embed_reply(ctx,
                                    content=f"<@!{target.id}>",
                                    title=f"🌯 SpaceBurrito!",
                                    description=f"<@!{ctx.author.id}> just delivered you a delicious Space🌌Burrito🌯!\n"
                                                f"Eat it before it gets cold!",
                                    thumbnail="https://cdn.discordapp.com/emojis/779465397903949825.png")
        else:
            await utils.embed_reply(ctx,
                                    title=f"🌯 SpaceBurrito!",
                                    description=f"<@!{ctx.author.id}> doesn't have any friends yet so they bought themselves a delicious Space🌌Burrito🌯!\n"
                                                f"Time to eagerly enjoy it in complete silence!",
                                    thumbnail="https://cdn.discordapp.com/emojis/779465397903949825.png")


def setup(bot):
    bot.add_cog(Commands(bot))
