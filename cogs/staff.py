from discord.ext import commands
from typing import Union
import discord

# Local imports
from modules import db, globals, utils


class Staff(commands.Cog,
            description="Mod abooz pls demot"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=       "save",
                      description="Save the bot's database and send a copy of it",
                      usage=      "{prfx}save",
                      help=       "",
                      aliases=    ["backup"])
    async def save(self, ctx):
        if utils.is_staff(ctx.author):
            if not await utils.save_db():
                await utils.embed_reply(ctx,
                                        title=f"💢 Failed to save remote config!")
            else:
                await ctx.message.add_reaction('👌')
            await ctx.reply(file=discord.File('db.sqlite3'))
            await ctx.author.send(file=discord.File('db.sqlite3'))

    @commands.group(name=            "gibxp",
                    description=     "Give a user some xp",
                    usage=           "{prfx}gibxp [ type ] [ user ] [ amount ]",
                    help=            "type: either level, cred or assist (required)\n"
                                     "user: the user to give xp to (ping, name, id) (required)\n"
                                     "amount: how much xp to give (can be negative) (required)",
                    aliases=         ["givexp"],
                    case_insensitive=True)
    async def gibxp(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @gibxp.command(name=   "level",
                   aliases=[])
    async def gibxp_level(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if utils.is_staff(ctx.author):
            # Convert target input to discord.Member
            if not target:
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide a valid user!")
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
            # Actual command
            xp_data = await db.add_user_xp(target.id, level=amount)
            await utils.embed_reply(ctx,
                                    description=(f"👌 Gave {amount} level XP to <@!{target.id}>!" if amount >= 0 else f"👌 Took {-amount} level XP from <@!{target.id}>!") + f"\nNew level XP value: `{xp_data['level']}`")

    @gibxp.command(name=   "cred",
                   aliases=[])
    async def gibxp_cred(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if utils.is_staff(ctx.author):
            # Convert target input to discord.Member
            if not target:
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide a valid user!")
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
            # Actual command
            xp_data = await db.add_user_xp(target.id, cred=amount)
            await utils.embed_reply(ctx,
                                    description=(f"👌 Gave {amount} cred XP to <@!{target.id}>!" if amount >= 0 else f"👌 Took {-amount} cred XP from <@!{target.id}>!") + f"\nNew cred XP value: `{xp_data['cred']}`")

    @gibxp.command(name=   "assistance",
                   aliases=["assist"])
    async def gibxp_assistance(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if utils.is_staff(ctx.author):
            # Convert target input to discord.Member
            if not target:
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide a valid user!")
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
            # Actual command
            xp_data = await db.add_user_xp(target.id, assistance=amount)
            await utils.embed_reply(ctx,
                                    description=(f"👌 Gave {amount} assistance XP to <@!{target.id}>!" if amount >= 0 else f"👌 Took {-amount} assistance XP from <@!{target.id}>!") + f"\nNew assistance XP value: `{xp_data['assistance']}`")

    @commands.group(name=            "setxp",
                    description=     "Change a user's xp value",
                    usage=           "{prfx}setxp [ type ] [ user ] [ amount ]",
                    help=            "type: either level, cred or assist (required)\n"
                                     "user: the user to change the xp of (ping, name, id) (required)\n"
                                     "amount: new xp value (negative will set 0) (required)",
                    aliases=         ["changexp"],
                    case_insensitive=True)
    async def setxp(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @setxp.command(name=   "level",
                   aliases=[])
    async def setxp_level(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if utils.is_staff(ctx.author):
            # Convert target input to discord.Member
            if not target:
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide a valid user!")
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
            # Actual command
            xp_data = await db.set_user_xp(target.id, level=amount)
            await utils.embed_reply(ctx,
                                    description=f"👌 Set <@!{target.id}>'s level XP to {xp_data['level']}!")

    @setxp.command(name=   "cred",
                   aliases=[])
    async def setxp_cred(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if utils.is_staff(ctx.author):
            # Convert target input to discord.Member
            if not target:
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide a valid user!")
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
            # Actual command
            xp_data = await db.set_user_xp(target.id, cred=amount)
            await utils.embed_reply(ctx,
                                    description=f"👌 Set <@!{target.id}>'s cred XP to {xp_data['cred']}!")

    @setxp.command(name=   "assistance",
                   aliases=["assist"])
    async def setxp_assistance(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if utils.is_staff(ctx.author):
            # Convert target input to discord.Member
            if not target:
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide a valid user!")
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
            # Actual command
            xp_data = await db.set_user_xp(target.id, assistance=amount)
            await utils.embed_reply(ctx,
                                    description=f"👌 Set <@!{target.id}>'s assistance XP to {xp_data['assistance']}!")


def setup(bot):
    bot.add_cog(Staff(bot))
