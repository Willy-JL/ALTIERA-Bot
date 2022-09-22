from discord.ext import commands
import aiofiles
import discord

# Local imports
from modules import globals, db, utils


def only_staff(ctx):
    return utils.is_staff(ctx.author)


class Staff(commands.Cog,
            description="Mod abooz pls demot"):
    def __init__(self, bot):
        self.bot = bot

    @utils.hybcommand(globals.bot,
                      name="save",
                      description="Save the bot's database and send a copy of it",
                      usage="{prfx}save",
                      help="",
                      aliases=["backup"],
                      check_func=only_staff)
    async def save(self, ctx: commands.Context):
        await utils.defer(ctx)
        if not await utils.save_db():
            title = "💢 Failed to save remote database!"
        else:
            title = "👌 Done!"
        await utils.embed_reply(ctx,
                                title=title,
                                file=discord.File('db.sqlite3'))
        await ctx.author.send(file=discord.File('db.sqlite3'))

    @utils.hybcommand(globals.bot,
                      name="restore",
                      description="Restore the bot's database from a backup",
                      usage="{prfx}restore",
                      help="",
                      aliases=["restorebackup"],
                      check_func=only_staff)
    async def restore(self, ctx, database: discord.Attachment = None):
        await utils.defer(ctx)
        if not database:
            for attachment in ctx.message.attachments:
                if attachment.filename == "db.sqlite3":
                    database = attachment
                    break
        if database:
            db_bytes = await database.read(use_cached=True)
        else:
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
            await utils.embed_reply(ctx,
                                    title="👌 Done!")

    @utils.hybgroup(globals.bot,
                    name="gibxp",
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

    @utils.hybcommand(globals.bot,
                      group=gibxp,
                      name="level",
                      aliases=[],
                      check_func=only_staff)
    async def gibxp_level(self, ctx, target: discord.Member, amount: int):
        level_xp, _, _ = await db.add_user_xp(target.id, level=amount)
        await utils.embed_reply(ctx,
                                description=(f"👌 Gave {amount} level XP to <@!{target.id}>!\n" if amount >= 0 else f"👌 Took {-amount} level XP from <@!{target.id}>!\n") +
                                             f"New level XP value: `{level_xp}`")

    @utils.hybcommand(globals.bot,
                      group=gibxp,
                      name="cred",
                      aliases=[],
                      check_func=only_staff)
    async def gibxp_cred(self, ctx, target: discord.Member, amount: int):
        _, cred_xp, _ = await db.add_user_xp(target.id, cred=amount)
        await utils.embed_reply(ctx,
                                description=(f"👌 Gave {amount} cred XP to <@!{target.id}>!\n" if amount >= 0 else f"👌 Took {-amount} cred XP from <@!{target.id}>!\n") +
                                             f"New cred XP value: `{cred_xp}`")

    @utils.hybcommand(globals.bot,
                      group=gibxp,
                      name="assistance",
                      aliases=["assist"],
                      check_func=only_staff)
    async def gibxp_assistance(self, ctx, target: discord.Member, amount: int):
        _, _, assistance_xp = await db.add_user_xp(target.id, assistance=amount)
        await utils.embed_reply(ctx,
                                description=(f"👌 Gave {amount} assistance XP to <@!{target.id}>!\n" if amount >= 0 else f"👌 Took {-amount} assistance XP from <@!{target.id}>!\n") +
                                             f"New assistance XP value: `{assistance_xp}`")

    @utils.hybgroup(globals.bot,
                    name="setxp",
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

    @utils.hybcommand(globals.bot,
                      group=setxp,
                      name="level",
                      aliases=[],
                      check_func=only_staff)
    async def setxp_level(self, ctx, target: discord.Member, amount: int):
        level_xp, _, _ = await db.set_user_xp(target.id, level=amount)
        await utils.embed_reply(ctx,
                                description=f"👌 Set <@!{target.id}>'s level XP successfully!\n"
                                            f"New level XP value: `{level_xp}`")

    @utils.hybcommand(globals.bot,
                      group=setxp,
                      name="cred",
                      aliases=[],
                      check_func=only_staff)
    async def setxp_cred(self, ctx, target: discord.Member, amount: int):
        _, cred_xp, _ = await db.set_user_xp(target.id, cred=amount)
        await utils.embed_reply(ctx,
                                description=f"👌 Set <@!{target.id}>'s cred XP successfully!\n"
                                            f"New cred XP value: `{cred_xp}`")

    @utils.hybcommand(globals.bot,
                      group=setxp,
                      name="assistance",
                      aliases=["assist"],
                      check_func=only_staff)
    async def setxp_assistance(self, ctx, target: discord.Member, amount: int):
        _, _, assistance_xp = await db.set_user_xp(target.id, assistance=amount)
        await utils.embed_reply(ctx,
                                description=f"👌 Set <@!{target.id}>'s assistance XP successfully!\n"
                                            f"New assistance XP value: `{assistance_xp}`")

    @utils.hybcommand(globals.bot,
                      name="restart",
                      description="Save DB and restart the bot",
                      usage="{prfx}restart",
                      help="",
                      aliases=["reboot", "reload"],
                      check_func=only_staff)
    async def restart(self, ctx):
        await utils.embed_reply(ctx,
                                title="👌 Restarting...")
        await utils.restart()


async def setup(bot):
    await bot.add_cog(Staff(bot))
