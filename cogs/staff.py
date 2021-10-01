from discord.ext import commands
from typing import Union
import discord

# Local imports
from modules import globals, db, utils


class Staff(commands.Cog,
            description="Mod abooz pls demot"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="save",
                      description="Save the bot's database and send a copy of it",
                      usage="{prfx}save",
                      help="",
                      aliases=["backup"])
    async def save(self, ctx):
        if not utils.is_staff(ctx.author):
            return
        if not await utils.save_db():
            await utils.embed_reply(ctx,
                                    title="💢 Failed to save remote database!")
        else:
            await ctx.message.add_reaction('👌')
        await ctx.reply(file=discord.File('db.sqlite3'))
        await ctx.author.send(file=discord.File('db.sqlite3'))

    @commands.command(name="restore",
                      description="Restore the bot's database from a backup",
                      usage="{prfx}restore",
                      help="",
                      aliases=["restorebackup"])
    async def restore(self, ctx):
        if not utils.is_staff(ctx.author):
            return
        db_bytes = None
        for attachment in ctx.message.attachments:
            if str(attachment.filename) == "db.sqlite3":
                db_bytes = await attachment.read(use_cached=True)
                break
        if not db_bytes:
            await utils.embed_reply(ctx,
                                    title='💢 Please attach a "db.sqlite3"!')
            return
        await globals.db.commit()
        await globals.db.close()
        async with aiofiles.open('db.sqlite3', 'wb') as f:
            await f.write(db_bytes)
        await db.init_db()
        if not await utils.save_db():
            await utils.embed_reply(ctx,
                                    title="💢 Failed to save remote database!")
        else:
            await ctx.message.add_reaction('👌')

    @commands.group(name="gibxp",
                    description="Give a user some xp",
                    usage="{prfx}gibxp [ type ] [ user ] [ amount ]",
                    help="type: either level, cred or assistance (required)\n"
                         "user: the user to give xp to (ping, name, id) (required)\n"
                         "amount: how much xp to give (can be negative) (required)",
                    aliases=["givexp"],
                    case_insensitive=True)
    async def gibxp(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @gibxp.command(name="level",
                   aliases=[])
    async def gibxp_level(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if not utils.is_staff(ctx.author):
            return
        # Convert target input to discord.Member
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 Please provide a valid user!")
            return
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            target = utils.strip_argument(target)
            target = await utils.get_best_member_match(ctx, target)
        elif isinstance(target, discord.User):
            target = ctx.guild.get_member(target.id)
        elif isinstance(target, discord.Member):
            pass
        else:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        # Handle amount
        try:
            amount = int(utils.strip_argument(amount))
        except (TypeError, ValueError,):
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid amount!")
            return
        # Actual command
        level_xp, _, _ = await db.add_user_xp(target.id, level=amount)
        await utils.embed_reply(ctx,
                                description=(f"👌 Gave {amount} level XP to <@!{target.id}>!\n" if amount >= 0 else f"👌 Took {-amount} level XP from <@!{target.id}>!\n") +
                                             f"New level XP value: `{level_xp}`")

    @gibxp.command(name="cred",
                   aliases=[])
    async def gibxp_cred(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if not utils.is_staff(ctx.author):
            return
        # Convert target input to discord.Member
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 Please provide a valid user!")
            return
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            target = utils.strip_argument(target)
            target = await utils.get_best_member_match(ctx, target)
        elif isinstance(target, discord.User):
            target = ctx.guild.get_member(target.id)
        elif isinstance(target, discord.Member):
            pass
        else:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        # Handle amount
        try:
            amount = int(utils.strip_argument(amount))
        except (TypeError, ValueError,):
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid amount!")
            return
        # Actual command
        _, cred_xp, _ = await db.add_user_xp(target.id, cred=amount)
        await utils.embed_reply(ctx,
                                description=(f"👌 Gave {amount} cred XP to <@!{target.id}>!\n" if amount >= 0 else f"👌 Took {-amount} cred XP from <@!{target.id}>!\n") +
                                             f"New cred XP value: `{cred_xp}`")

    @gibxp.command(name="assistance",
                   aliases=["assist"])
    async def gibxp_assistance(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if not utils.is_staff(ctx.author):
            return
        # Convert target input to discord.Member
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 Please provide a valid user!")
            return
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            target = utils.strip_argument(target)
            target = await utils.get_best_member_match(ctx, target)
        elif isinstance(target, discord.User):
            target = ctx.guild.get_member(target.id)
        elif isinstance(target, discord.Member):
            pass
        else:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        # Handle amount
        try:
            amount = int(utils.strip_argument(amount))
        except (TypeError, ValueError,):
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid amount!")
            return
        # Actual command
        _, _, assistance_xp = await db.add_user_xp(target.id, assistance=amount)
        await utils.embed_reply(ctx,
                                description=(f"👌 Gave {amount} assistance XP to <@!{target.id}>!\n" if amount >= 0 else f"👌 Took {-amount} assistance XP from <@!{target.id}>!\n") +
                                             f"New assistance XP value: `{assistance_xp}`")

    @commands.group(name="setxp",
                    description="Change a user's xp value",
                    usage="{prfx}setxp [ type ] [ user ] [ amount ]",
                    help="type: either level, cred or assistance (required)\n"
                         "user: the user to change the xp of (ping, name, id) (required)\n"
                         "amount: new xp value (negative will set 0) (required)",
                    aliases=["changexp"],
                    case_insensitive=True)
    async def setxp(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @setxp.command(name="level",
                   aliases=[])
    async def setxp_level(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if not utils.is_staff(ctx.author):
            return
        # Convert target input to discord.Member
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 Please provide a valid user!")
            return
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            target = utils.strip_argument(target)
            target = await utils.get_best_member_match(ctx, target)
        elif isinstance(target, discord.User):
            target = ctx.guild.get_member(target.id)
        elif isinstance(target, discord.Member):
            pass
        else:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        # Handle amount
        try:
            amount = int(utils.strip_argument(amount))
        except (TypeError, ValueError,):
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid amount!")
            return
        # Actual command
        level_xp, _, _ = await db.set_user_xp(target.id, level=amount)
        await utils.embed_reply(ctx,
                                description=f"👌 Set <@!{target.id}>'s level XP successfully!\n"
                                            f"New level XP value: `{level_xp}`")

    @setxp.command(name="cred",
                   aliases=[])
    async def setxp_cred(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if not utils.is_staff(ctx.author):
            return
        # Convert target input to discord.Member
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 Please provide a valid user!")
            return
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            target = utils.strip_argument(target)
            target = await utils.get_best_member_match(ctx, target)
        elif isinstance(target, discord.User):
            target = ctx.guild.get_member(target.id)
        elif isinstance(target, discord.Member):
            pass
        else:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        # Handle amount
        try:
            amount = int(utils.strip_argument(amount))
        except (TypeError, ValueError,):
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid amount!")
            return
        # Actual command
        _, cred_xp, _ = await db.set_user_xp(target.id, cred=amount)
        await utils.embed_reply(ctx,
                                description=f"👌 Set <@!{target.id}>'s cred XP successfully!\n"
                                            f"New cred XP value: `{cred_xp}`")

    @setxp.command(name="assistance",
                   aliases=["assist"])
    async def setxp_assistance(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if not utils.is_staff(ctx.author):
            return
        # Convert target input to discord.Member
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 Please provide a valid user!")
            return
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            target = utils.strip_argument(target)
            target = await utils.get_best_member_match(ctx, target)
        elif isinstance(target, discord.User):
            target = ctx.guild.get_member(target.id)
        elif isinstance(target, discord.Member):
            pass
        else:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        if not target:
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid user!")
            return
        # Handle amount
        try:
            amount = int(utils.strip_argument(amount))
        except (TypeError, ValueError,):
            await utils.embed_reply(ctx,
                                    title="💢 That is not a valid amount!")
            return
        # Actual command
        _, _, assistance_xp = await db.set_user_xp(target.id, assistance=amount)
        await utils.embed_reply(ctx,
                                description=f"👌 Set <@!{target.id}>'s assistance XP successfully!\n"
                                            f"New assistance XP value: `{assistance_xp}`")

    @commands.command(name="restart",
                      description="Save DB and restart the bot",
                      usage="{prfx}restart",
                      help="",
                      aliases=["reboot"])
    async def restart(self, ctx):
        if not utils.is_staff(ctx.author):
            return
        await utils.embed_reply(ctx,
                                title="👌 Restarting...")
        await utils.restart()


def setup(bot):
    bot.add_cog(Staff(bot))
