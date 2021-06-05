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
                                                f"{globals.bot.command_prefix}**cookie**: Treat someone to a CyberCookie\n"
                                                f"{globals.bot.command_prefix}**burrito**: Deliver someone a SpaceBurrito\n"
                                                f"\n"
                                                f"Lookup a command with `{globals.bot.command_prefix}help command` (the command goes without `{globals.bot.command_prefix}`)\n"
                                                f"You can't add me to your server, but [the code is open-source!](https://github.com/Willy-JL/altiera-bot)")

    @help.command(name="help")
    async def help_help(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ A.L.T.I.E.R.A. Help > {globals.bot.command_prefix}help",
                                description=f"Why are you like this?\n"
                                            f"Ugh, I guess I'll explain this too...\n"
                                            f"\n"
                                            f"See a list of commands / Look up info and usage of a command\n"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}help [ command ]`\n"
                                            f"command: the command to look up (optional)\n"
                                            f"\n"
                                            f"Aliases: `N/A`")

    @help.command(name="stats")
    async def help_stats(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ A.L.T.I.E.R.A. Help > {globals.bot.command_prefix}stats",
                                description=f"See your server stats (level, cred, assistance)\n"
                                            f"You earn level from chatting anywhere (except in bot commands channels)\n"
                                            f"Cred is only earned by users with modder role and only in modding channels\n"
                                            f"Assistance XP is generated in the hospital and support channels, everyone earns, modders earn 2x\n"
                                            f"There are cooldowns, spamming won't get you far\n"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}stats [ user ]`\n"
                                            f"user: the user to check stats for (ping, name, id) (optional)\n"
                                            f"\n"
                                            f"Aliases: " + ", ".join([f"`{globals.bot.command_prefix}{alias}`" for alias in ["levels", "level", "cred", "assistance", "assist"]]))

    @help.command(name="xp")
    async def help_xp(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ A.L.T.I.E.R.A. Help > {globals.bot.command_prefix}xp",
                                description=f"See your XP amounts (levels depend on XP amount)\n"
                                            f"LVL1 = 1000XP, LVL2 = 2000XP, LVL3 = 3000XP, LVL4 = 4000XP and so on...\n"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}xp [ user ]`\n"
                                            f"user: the user to check xp amounts for (ping, name, id) (optional)\n"
                                            f"\n"
                                            f"Aliases: " + ", ".join([f"`{globals.bot.command_prefix}{alias}`" for alias in ["xpamount", "levelxp", "credxp", "assistancexp", "assistxp"]]))

    @help.command(name="top")
    async def help_top(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ A.L.T.I.E.R.A. Help > {globals.bot.command_prefix}top",
                                description=f"List top ten users per XP type\n"
                                            f"And then cry yourself to sleep when you realize Halvkyrie will always be first\n"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}top [ type ]`\n"
                                            f"type: either level, cred or assist (required)\n"
                                            f"\n"
                                            f"Aliases: " + ", ".join([f"`{globals.bot.command_prefix}{alias}`" for alias in ["top10", "leaderboard", "ranking"]]))

    @help.command(name="rep")
    async def help_rep(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ A.L.T.I.E.R.A. Help > {globals.bot.command_prefix}rep",
                                description=f"Gift a cool person some reputation (500 cred XP)\n"
                                            f"Only once every 24 hours (or sooner if bot restarts unexpectedly)\n"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}rep [ user ]`\n"
                                            f"user: the user to give rep to (ping, name, id) (required)\n"
                                            f"\n"
                                            f"Aliases: " + ", ".join([f"`{globals.bot.command_prefix}{alias}`" for alias in ["reputation", "giverep", "givereputation"]]))

    @help.command(name="daily")
    async def help_daily(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ A.L.T.I.E.R.A. Help > {globals.bot.command_prefix}daily",
                                description=f"Claim your daily reward (500 level XP)\n"
                                            f"Only once every 24 hours (or sooner if bot restarts unexpectedly)\n"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}daily`\n"
                                            f"\n"
                                            f"Aliases: " + ", ".join([f"`{globals.bot.command_prefix}{alias}`" for alias in ["riseandshine", "ijustwokeup", "gibreward", "claimdaily", "gibdaily"]]))

    @help.command(name="dice")
    async def help_dice(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ A.L.T.I.E.R.A. Help > {globals.bot.command_prefix}dice",
                                description=f"Roll some dice\n"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}dice [ max ]`\n"
                                            f"**Usage**: `{globals.bot.command_prefix}dice [ throws ] [ max ]`\n"
                                            f"**Usage**: `{globals.bot.command_prefix}dice [ throws ] [ max ] [ modifier ]`\n"
                                            f"throws: number of dice throws, default 1, max 10 (optional)\n"
                                            f"max: number of faces (aka max per dice), default 6 max 100 (optional)\n"
                                            f"modifier: number to add or subtract from result, default 0, max +100/-100 (optional)\n"
                                            f"\n"
                                            f"Aliases: " + ", ".join([f"`{globals.bot.command_prefix}{alias}`" for alias in ["diceroll", "rolldice", "roll"]]))

    @help.command(name="cookie")
    async def help_cookie(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ A.L.T.I.E.R.A. Help > {globals.bot.command_prefix}cookie",
                                description=f"Treat someone to a CyberCookie\n"
                                            f"Purely cosmetic, no rewards whatsoever\n"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}cookie [ user ]`\n"
                                            f"user: the user to give a cookie to (ping, name, id) (optional)\n"
                                            f"\n"
                                            f"Aliases: " + ", ".join([f"`{globals.bot.command_prefix}{alias}`" for alias in ["cybcookie", "cybercookie"]]))

    @help.command(name="burrito")
    async def help_burrito(self, ctx):
        await utils.embed_reply(ctx,
                                title=f"⁉️ A.L.T.I.E.R.A. Help > {globals.bot.command_prefix}burrito",
                                description=f"Deliver someone a SpaceBurrito\n"
                                            f"Purely cosmetic, no rewards whatsoever\n"
                                            f"\n"
                                            f"**Usage**: `{globals.bot.command_prefix}burrito [ user ]`\n"
                                            f"user: the user to give a burrito to (ping, name, id) (optional)\n"
                                            f"\n"
                                            f"Aliases: " + ", ".join([f"`{globals.bot.command_prefix}{alias}`" for alias in ["spaceburrito", "galacticburrito"]]))


def setup(bot):
    bot.add_cog(Help(bot))
