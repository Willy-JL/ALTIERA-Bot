import random
import discord
import datetime
from typing import Union
from discord.ext import commands
from fuzzywuzzy import process, fuzz

# Local imports
from modules import globals, xp


rep_cooldown_users = set()


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["diceroll", "rolldice", "roll"])
    async def dice(self, ctx, arg1: str = None, arg2: str = None):
        try:
            max = int(arg1)
        except (ValueError, TypeError):
            await ctx.reply('Please provide a valid number!')
            return

        if arg2 is not None:
            throws = max
            try:
                max = int(arg2)
            except (ValueError, TypeError):
                await ctx.reply('Please provide valid numbers!')
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
            rolls.append(roll)
        await ctx.reply(embed=discord.Embed(title=f"🎲 Dice roll!",
                                            description=f"Throws: {str(throws)}{' (capped)' if throws_capped else ''}\n"
                                                        f"Max: {str(max)}{' (capped)' if max_capped else ''}\n"
                                                        f"\n__**Result**__: `{str(result)}` ( {', '.join(rolls)} )",
                                            color=discord.Color(0xEDE400),
                                            timestamp=datetime.datetime.utcnow())
                                            .set_footer(text=ctx.guild.name,
                                                        icon_url=ctx.guild.icon_url))

    @commands.command(aliases=["reputation", "giverep", "givereputation"])
    async def rep(self, ctx, target: Union[discord.Member, discord.User, int, str] = None):
        if not str(ctx.author.id) in rep_cooldown_users:
            # Convert target input to discord.Member
            if not target:
                await ctx.reply("Please provide a user to give reputation to!")
                return
            if isinstance(target, int):
                target = ctx.guild.get_member(target)
            elif isinstance(target, str):
                name_list = [user.name for user in ctx.guild.members] + [user.nick for user in ctx.guild.members if user.nick]
                results = [result[0] for result in process.extract(target, name_list, scorer=fuzz.ratio, limit=20)]
                results.sort(key=lambda x: [xp.ensure_user_data(str(ctx.guild.get_member_named(x).id)), globals.config[str(ctx.guild.get_member_named(x).id)][0]][1], reverse=True)
                target = ctx.guild.get_member_named(results[0])
            elif isinstance(target, discord.User):
                target = ctx.guild.get_member(target.id)
            elif isinstance(target, discord.Member):
                pass
            else:
                await ctx.reply("That is not a valid user!")
                return
            if not target:
                await ctx.reply("That is not a valid user!")
                return
            # Actual command
            xp.ensure_user_data(str(target.id))
            globals.config[str(target.id)][1] += globals.REP_CRED_AMOUNT
            rep_cooldown_users.add(str(ctx.author.id))
            await ctx.reply(f"<@!{target.id}>",
                            embed=discord.Embed(title=f"💌 You got some reputation!",
                                                description=f"<@!{ctx.author.id}> likes what you do and showed their gratitude by gifting you **500 server cred xp**!",
                                                color=discord.Color(0xEDE400),
                                                timestamp=datetime.datetime.utcnow())
                                                .set_thumbnail(url="https://cdn.discordapp.com/emojis/766042961929699358.png")
                                                .set_footer(text=ctx.guild.name,
                                                            icon_url=ctx.guild.icon_url))
        else:
            await ctx.reply(embed=discord.Embed(title=f"💢 You're on cooldown!",
                                                description=f"You can only use that command once every **24 hours** (once per bot restart to be exact)!",
                                                color=discord.Color(0xEDE400),
                                                timestamp=datetime.datetime.utcnow())
                                                .set_footer(text=ctx.guild.name,
                                                            icon_url=ctx.guild.icon_url))


def setup(bot):
    bot.add_cog(Commands(bot))
