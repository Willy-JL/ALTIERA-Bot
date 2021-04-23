from discord.ext import commands
from typing import Union
import datetime
import discord
import random
import time

# Local imports
from modules import globals, utils, xp


rep_cooldown_users = set()


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["diceroll", "rolldice", "roll"])
    async def dice(self, ctx, arg1: str = None, arg2: str = None):
        try:
            max = int(arg1)
        except (ValueError, TypeError):
            await utils.embed_reply(ctx,
                                    title=f"💢 Please provide a valid number!")
            return

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

        throws_capped = False
        max_capped = False
        if throws > 10:
            throws = 10
            throws_capped = True
        if max > 100:
            max = 100
            max_capped = True

        result = 0
        rolls = []
        for _ in range(throws):
            roll = random.randint(1, max)
            result += roll
            rolls.append(str(roll))
        await utils.embed_reply(ctx,
                                title=f"🎲 Dice roll!",
                                description=f'Throws: {throws}{" (capped)" if throws_capped else ""}\n'
                                            f'Max: {max}{" (capped)" if max_capped else ""}\n'
                                            f'\n'
                                            f'__**Result**__: __**`{str(result)}`**__ ( {", ".join(rolls)} )')

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
                                    description=f"<@!{ctx.author.id}> likes what you do and showed their gratitude by gifting you **{globals.REP_CRED_AMOUNT} server cred xp**!",
                                    thumbnail="https://cdn.discordapp.com/emojis/766042961929699358.png")
        else:
            await utils.embed_reply(ctx,
                                    title=f"💢 You're on cooldown!",
                                    description=f"You can only use that command once every **24 hours**!\n"
                                                f"You'll be able to use it again in roughly **{datetime.timedelta(seconds=int(86369-(time.time()-globals.start_timestamp)))}**")


def setup(bot):
    bot.add_cog(Commands(bot))
