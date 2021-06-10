from discord.ext import commands
import datetime
import discord
import psutil
import os

# Local imports
from modules import globals, utils


class Bot(commands.Cog,
          description="Commands regarding the bot instance"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help",
                      description="Think real hard and guess what this does\n"
                                  "Why are you like this?\n"
                                  "Ugh, I guess I'll explain this one too...",
                      usage="{prfx}help [ subcommand ]",
                      help="subcommand: the submenu/command to look up (optional)",
                      aliases=[])
    async def help(self, ctx, subcommand=None):
        prfx = globals.bot.command_prefix
        if subcommand and subcommand.startswith(prfx):
            subcommand = subcommand[len(prfx):]
        if subcommand:
            subcommand = subcommand.lower()
            for cog_name in globals.bot.cogs:
                if cog_name.lower() == "jishaku":
                    continue
                if cog_name.lower() == subcommand:
                    cog = globals.bot.get_cog(cog_name)
                    desc = ""
                    if "staff" in cog_name.lower() and not utils.is_staff(ctx.author):
                        desc += "These are **staff only** commands, you can't use them!\n\n"
                    desc += cog.description + "\n\n"
                    for command in cog.get_commands():
                        desc += f'{prfx}**{command.name}**: ' + (command.description[:command.description.find("\n")] if "\n" in command.description else command.description) + '\n'
                    desc += f"\nYou can use `{prfx}help [ command ]` to see more info about it!\n"
                    desc += f"**\nA.L.T.I.E.R.A. Bot**{(' `' + os.environ.get('HEROKU_RELEASE_VERSION') + '`') if os.environ.get('HEROKU_RELEASE_VERSION') else ''}, made with ❤️ by [WillyJL](https://linktr.ee/WillyJL)"
                    await utils.embed_reply(ctx,
                                            title=f"⁉️   A.L.T.I.E.R.A. Help  >  {cog_name}",
                                            description=desc)
                    return
            for command in globals.bot.commands:
                cog_name = command.cog.qualified_name
                if cog_name.lower() == "jishaku":
                    continue
                aliases = [alias.lower() for alias in command.aliases]
                if command.name.lower() == subcommand or subcommand in aliases:
                    desc = ""
                    if "staff" in cog_name.lower() and not utils.is_staff(ctx.author):
                        desc += "This is a **staff only** command, you can't use it!\n\n"
                    desc += command.description + "\n\n"
                    desc += "**Usage**: `" + command.usage.format(prfx=prfx) + "`\n"
                    if command.help:
                        desc += command.help + "\n"
                    if aliases:
                        desc += f"\n**Aliases**: `{prfx}" + f"`, `{prfx}".join(aliases) + "`\n"
                    desc += f"**\nA.L.T.I.E.R.A. Bot**{(' `' + os.environ.get('HEROKU_RELEASE_VERSION') + '`') if os.environ.get('HEROKU_RELEASE_VERSION') else ''}, made with ❤️ by [WillyJL](https://linktr.ee/WillyJL)"
                    await utils.embed_reply(ctx,
                                            title=f"⁉️   A.L.T.I.E.R.A. Help  >  {cog_name}  >  {prfx}{command.name}",
                                            description=desc)
                    return
        desc = "You can use these commands to see a category of commands:\n\n"
        for cog_name in globals.bot.cogs:
            if cog_name.lower() == "jishaku":
                continue
            if "staff" in cog_name.lower() and not utils.is_staff(ctx.author):
                continue
            cog = globals.bot.get_cog(cog_name)
            desc += f"{prfx}help **{cog_name.lower()}**: " + (cog.description[:cog.description.find('\n')] if '\n' in cog.description else cog.description) + "\n"
        desc += f"\nYou can use `{prfx}help [ command ]` to see more info about it!\n"
        desc += f"\n**A.L.T.I.E.R.A. Bot**{(' `' + os.environ.get('HEROKU_RELEASE_VERSION') + '`') if os.environ.get('HEROKU_RELEASE_VERSION') else ''}, made with ❤️ by [WillyJL](https://linktr.ee/WillyJL)"
        await utils.embed_reply(ctx,
                                title=f"⁉️   A.L.T.I.E.R.A. Help",
                                description=desc)
        return

    @commands.command(name="info",
                      description="Show info and details about the bot",
                      usage="{prfx}info",
                      help="",
                      aliases=["botinfo"])
    async def info(self, ctx):
        await utils.embed_reply(ctx,
                                title="📊 Bot Info",
                                fields=[
                                    ["♾️ Uptime:",          f"{utils.time_from_start()}",                                                                                                                                          True],
                                    ["☯️ Next Restart In:", f"{utils.time_to_restart()}",                                                                                                                                          True],
                                    ["⏳ Ping:",            f"{int(globals.bot.latency * 1000)}ms",                                                                                                                                True],
                                    ["📟 CPU Usage",        f"{psutil.cpu_percent()}%",                                                                                                                                            True],
                                    ["💾 RAM Usage",        f"{utils.pretty_size(psutil.Process(os.getpid()).memory_info().rss)}/{'512MB' if os.environ.get('DYNO') else utils.pretty_size(psutil.virtual_memory().total)}",       True],
                                    ["🚀 Last Update",      f"{datetime.datetime.fromisoformat(os.environ.get('HEROKU_RELEASE_CREATED_AT')[:-1]).strftime('%d/%m/%Y') if os.environ.get('HEROKU_RELEASE_CREATED_AT') else 'N/A'}", True],
                                    ["👨‍💻 Developer",        f"[WillyJL](https://linktr.ee/WillyJL)",                                                                                                                               True],
                                    ["📚 Library",          f"discord.py v{discord.__version__}",                                                                                                                                  True],
                                    ["📦 Version",          f"{os.environ.get('HEROKU_RELEASE_VERSION') if os.environ.get('HEROKU_RELEASE_VERSION') else 'N/A'}",                                                                  True],
                                ],
                                thumbnail=globals.bot.user.avatar_url)


def setup(bot):
    bot.add_cog(Bot(bot))
