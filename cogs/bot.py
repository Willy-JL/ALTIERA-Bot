from discord.ext import commands
import os

# Local imports
from modules import globals, utils


class Bot(commands.Cog,
          description="Commands regarding the running bot instance"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=       "help",
                      description="See info about bot commands",
                      usage=      "{prfx}help [ subcommand ]",
                      help=       "subcommand: the submenu/command to look up (optional)",
                      aliases=    [])
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
                    desc += f"\nYou can use `{prfx}help [ command ]` to see more info about it!\n\n"
                    desc += f"**A.L.T.I.E.R.A. Bot**{(' `' + os.environ.get('HEROKU_RELEASE_VERSION') + '`') if os.environ.get('HEROKU_RELEASE_VERSION') else ''}, made with ❤️ by [WillyJL](https://linktr.ee/WillyJL)"
                    await utils.embed_reply(ctx,
                                            title=f"⁉️   A.L.T.I.E.R.A. Help > {cog_name}",
                                            description=desc)
                    return
            for command in globals.bot.commands:
                if command.cog.qualified_name.lower() == "jishaku":
                    continue
                aliases = [alias.lower() for alias in command.aliases]
                if command.name.lower() == subcommand or subcommand in aliases:
                    desc = ""
                    if "staff" in command.cog.qualified_name.lower() and not utils.is_staff(ctx.author):
                        desc += "This is a **staff only** command, you can't use it!\n\n"
                    desc += command.description + "\n\n"
                    desc += "**Usage**: `" + command.usage.format(prfx=prfx) + "`\n"
                    if command.help:
                        desc += command.help + "\n"
                    if aliases:
                        desc += f"\n**Aliases**: `{prfx}" + f"`, `{prfx}".join(aliases) + "`\n"
                    desc += f"**A.L.T.I.E.R.A. Bot**{(' `' + os.environ.get('HEROKU_RELEASE_VERSION') + '`') if os.environ.get('HEROKU_RELEASE_VERSION') else ''}, made with ❤️ by [WillyJL](https://linktr.ee/WillyJL)"
                    await utils.embed_reply(ctx,
                                            title=f"⁉️   A.L.T.I.E.R.A. Help > {command.name.title()}",
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
        desc += f"\nYou can use `{prfx}help [ command ]` to see more info about it!\n\n"
        desc += f"**A.L.T.I.E.R.A. Bot**{(' `' + os.environ.get('HEROKU_RELEASE_VERSION') + '`') if os.environ.get('HEROKU_RELEASE_VERSION') else ''}, made with ❤️ by [WillyJL](https://linktr.ee/WillyJL)"
        await utils.embed_reply(ctx,
                                title=f"⁉️   A.L.T.I.E.R.A. Help",
                                description=desc)
        return


def setup(bot):
    bot.add_cog(Bot(bot))
