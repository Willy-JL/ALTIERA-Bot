from discord.ext import commands
import builtins
import random

# Local imports
from modules import globals, utils


class Utilities(commands.Cog,
                description="Some handy commands"):
    def __init__(self, bot):
        self.bot = bot

    @utils.hybcommand(globals.bot,
                      name="dice",
                      description="Roll some dice",
                      usage="{prfx}dice [ max ] [ throws ] [ modifier ]",
                      help="max: number of faces (aka max per dice), default 6 max 100 (optional)\n"
                           "throws: number of dice throws, default 1, max 10 (optional)\n"
                           "modifier: number to add or subtract from result, default 0, max +100/-100 (optional)",
                      aliases=["diceroll", "rolldice", "roll"])
    async def dice(self, ctx, max: int = None, throws: int = None, modifier: int = None):
        # Defaults
        max = max if max is not None else 6
        throws = throws if throws is not None else 1
        modifier = modifier if modifier is not None else 0
        # Adjustments
        _max = builtins.min(builtins.max(max, 2), 100)
        _throws = builtins.min(builtins.max(throws, 1), 10)
        _modifier = builtins.min(builtins.max(modifier, -100), 100)
        max_adjusted = _max != max
        throws_adjusted = _throws != throws
        modifier_adjusted = _modifier != modifier
        max = _max
        throws = _throws
        modifier = _modifier
        # Actual command
        result = 0
        rolls = []
        for _ in range(throws):
            roll = random.randint(1, max)
            result += roll
            rolls.append(str(roll))
        result += modifier
        await utils.embed_reply(ctx,
                                title="🎲 Dice roll!",
                                description=f'Max: {max}{" (adjusted)" if max_adjusted else ""}\n'
                                            f'Throws: {throws}{" (adjusted)" if throws_adjusted else ""}\n'
                                            f'Modifier: {modifier:+}{" (adjusted)" if modifier_adjusted else ""}\n'
                                            '\n'
                                            f'Result:  __**{str(result)}**__ ( `{", ".join(rolls)}{f", {modifier:+}" if modifier != 0 else ""}` )',
                                add_timestamp=False)


async def setup(bot):
    await bot.add_cog(Utilities(bot))
