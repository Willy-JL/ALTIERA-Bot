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


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            await utils.embed_reply(ctx,
                                    title=f"⁉️ A.L.T.I.E.R.A. Help",
                                    description=f"Here you have a list of commands:\n"
                                                f"\n"
                                                f"{globals.bot.command_prefix}**help**: Think real hard and guess what that does\n"
                                                f"{globals.bot.command_prefix}**stats**: See your server stats (level, cred, assistance)\n"
                                                f"{globals.bot.command_prefix}**xp**: See your XP amounts (levels depend on XP amount)\n"
                                                f"{globals.bot.command_prefix}**top**: List top ten users per XP type\n"
                                                f"{globals.bot.command_prefix}**rep**: Gift a cool person some reputation (500 cred XP)\n"
                                                f"{globals.bot.command_prefix}**daily**: Claim your daily reward (500 level XP)\n"
                                                f"{globals.bot.command_prefix}**dice**: Roll some dice\n"
                                                f"\n"
                                                f"You can see more info on any of these by using `{globals.bot.command_prefix}help commandname` (the command name goes without `{globals.bot.command_prefix}`!)\n"
                                                f"No, you can't add me to your server, this bot is exclusive to this community. [The code is open-source however!](https://github.com/Willy-JL/altiera-bot)")

    @help.command(name="help")
    async def help_help(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ {globals.bot.command_prefix}help",
                                description=f"Why are you like this?\n"
                                            f"Ugh, I guess I'll explain this too...\n"
                                            f"\n"
                                            f"See a list of commands / Look up info as usage of a command"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}help [command]`\n"
                                            f"command: the command to look up (optional)\n"
                                            f"\n"
                                            f"Aliases: N/A\n")


def setup(bot):
    bot.add_cog(Help(bot))
