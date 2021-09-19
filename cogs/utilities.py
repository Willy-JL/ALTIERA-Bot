from discord.ext import commands
import random

# Local imports
from modules import globals, utils


class Utilities(commands.Cog,
                description="Some handy commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dice",
                      description="Roll some dice",
                      usage="{prfx}dice [ max ]`\n**Usage**: `"
                            "{prfx}dice [ throws ] [ max ]`\n**Usage**: `"
                            "{prfx}dice [ throws ] [ max ] [ modifier ]",
                      help="throws: number of dice throws, default 1, max 10 (optional)\n"
                           "max: number of faces (aka max per dice), default 6 max 100 (optional)\n"
                           "modifier: number to add or subtract from result, default 0, max +100/-100 (optional)",
                      aliases=["diceroll", "rolldice", "roll"])
    async def dice(self, ctx, arg1: str = None, arg2: str = None, arg3: str = None):
        if arg1 is not None:
            try:
                max = int(arg1)
            except (ValueError, TypeError):
                await utils.embed_reply(ctx,
                                        title="💢 Please provide a valid number!")
                return
        else:
            max = 6

        if arg2 is not None:
            throws = max
            try:
                max = int(arg2)
            except (ValueError, TypeError):
                await utils.embed_reply(ctx,
                                        title="💢 Please provide valid numbers!")
                return
        else:
            throws = 1

        if arg3 is not None:
            try:
                mod = int(arg3)
            except (ValueError, TypeError):
                await utils.embed_reply(ctx,
                                        title="💢 Please provide valid numbers!")
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
                                title="🎲 Dice roll!",
                                description=f'Throws: {throws}{" (adjusted)" if throws_adjusted else ""}\n'
                                            f'Max: {max}{" (adjusted)" if max_adjusted else ""}\n'
                                            f'Modifier: {mod:+}{" (adjusted)" if mod_adjusted else ""}\n'
                                            '\n'
                                            f'Result:  __**{str(result)}**__ ( `{", ".join(rolls)}{f", {mod:+}" if mod != 0 else ""}` )',
                                add_timestamp=False)


def setup(bot):
    bot.add_cog(Utilities(bot))
