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
                      aliases=[],
                      check_func=only_staff)
    async def save(self, ctx):
        await utils.defer(ctx)
        if not await utils.save_db():
            title = "💢 Failed to save remote database!"
        else:
            title = "👌 Done!"
        await utils.embed_reply(ctx,
                                title=title,
                                file=discord.File('db.sqlite3'),
                                ephemeral=False)
        await ctx.author.send(file=discord.File('db.sqlite3'))

    @utils.hybcommand(globals.bot,
                      name="restore",
                      description="Restore the bot's database from a backup",
                      usage="{prfx}restore",
                      help="",
                      aliases=[],
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
                                    title="👌 Done!",
                                    ephemeral=False)

    @utils.hybgroup(globals.bot,
                    name="givexp",
                    description="Give a user some xp",
                    usage="{prfx}givexp [ type ] [ user ] [ amount ]",
                    help="type: either level, cred or assistance (required)\n"
                         "user: the user to give xp to (ping, name, id) (required)\n"
                         "amount: how much xp to give (can be negative) (required)",
                    aliases=[],
                    case_insensitive=True)
    async def givexp(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @utils.hybcommand(globals.bot,
                      group=givexp,
                      name="level",
                      aliases=[],
                      check_func=only_staff)
    async def givexp_level(self, ctx, target: discord.Member, amount: int):
        level_xp, _, _ = await db.add_user_xp(target.id, level=amount)
        await utils.embed_reply(ctx,
                                description=(f"👌 Gave {amount} level XP to <@!{target.id}>!\n" if amount >= 0 else f"👌 Took {-amount} level XP from <@!{target.id}>!\n") +
                                             f"New level XP value: `{level_xp}`",
                                ephemeral=False)

    @utils.hybcommand(globals.bot,
                      group=givexp,
                      name="cred",
                      aliases=[],
                      check_func=only_staff)
    async def givexp_cred(self, ctx, target: discord.Member, amount: int):
        _, cred_xp, _ = await db.add_user_xp(target.id, cred=amount)
        await utils.embed_reply(ctx,
                                description=(f"👌 Gave {amount} cred XP to <@!{target.id}>!\n" if amount >= 0 else f"👌 Took {-amount} cred XP from <@!{target.id}>!\n") +
                                             f"New cred XP value: `{cred_xp}`",
                                ephemeral=False)

    @utils.hybcommand(globals.bot,
                      group=givexp,
                      name="assistance",
                      aliases=["assist"],
                      check_func=only_staff)
    async def givexp_assistance(self, ctx, target: discord.Member, amount: int):
        _, _, assistance_xp = await db.add_user_xp(target.id, assistance=amount)
        await utils.embed_reply(ctx,
                                description=(f"👌 Gave {amount} assistance XP to <@!{target.id}>!\n" if amount >= 0 else f"👌 Took {-amount} assistance XP from <@!{target.id}>!\n") +
                                             f"New assistance XP value: `{assistance_xp}`",
                                ephemeral=False)

    @utils.hybgroup(globals.bot,
                    name="setxp",
                    description="Change a user's xp value",
                    usage="{prfx}setxp [ type ] [ user ] [ amount ]",
                    help="type: either level, cred or assistance (required)\n"
                         "user: the user to change the xp of (ping, name, id) (required)\n"
                         "amount: new xp value (negative will set 0) (required)",
                    aliases=[],
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
                                            f"New level XP value: `{level_xp}`",
                                ephemeral=False)

    @utils.hybcommand(globals.bot,
                      group=setxp,
                      name="cred",
                      aliases=[],
                      check_func=only_staff)
    async def setxp_cred(self, ctx, target: discord.Member, amount: int):
        _, cred_xp, _ = await db.set_user_xp(target.id, cred=amount)
        await utils.embed_reply(ctx,
                                description=f"👌 Set <@!{target.id}>'s cred XP successfully!\n"
                                            f"New cred XP value: `{cred_xp}`",
                                ephemeral=False)

    @utils.hybcommand(globals.bot,
                      group=setxp,
                      name="assistance",
                      aliases=["assist"],
                      check_func=only_staff)
    async def setxp_assistance(self, ctx, target: discord.Member, amount: int):
        _, _, assistance_xp = await db.set_user_xp(target.id, assistance=amount)
        await utils.embed_reply(ctx,
                                description=f"👌 Set <@!{target.id}>'s assistance XP successfully!\n"
                                            f"New assistance XP value: `{assistance_xp}`",
                                ephemeral=False)

    @utils.hybcommand(globals.bot,
                      name="restart",
                      description="Save DB and restart the bot",
                      usage="{prfx}restart",
                      help="",
                      aliases=[],
                      check_func=only_staff)
    async def restart(self, ctx):
        await utils.embed_reply(ctx,
                                title="👌 Restarting...")
        await utils.restart()

    @utils.hybcommand(globals.bot,
                      name="ban",
                      description="Ban a user from the server",
                      usage="{prfx}ban [ user ] [ purge days ] [ reason ]",
                      help="user: the user to ban\n"
                           "purge days: number of days to purge messages for (optional)\n"
                           "reason: reason for the ban (optional)",
                      aliases=[],
                      check_func=only_staff)
    async def ban(self, ctx, user: discord.Member, purge_days: int = 0, *, reason: str = ""):
        await user.ban(delete_message_days=purge_days, reason=f"Issuer: {ctx.author}" + (f": {reason}" if reason else ""))
        await utils.embed_reply(ctx,
                                title="👌 Begone, choom!",
                                description=f"{user.mention} was just **banned** by {ctx.author.mention}!\n" +
                                            (f"**Reason**: {reason}\n" if reason else "") +
                                            f"Purged last **{purge_days} day{'' if purge_days == 1 else 's'}** worth of messages",
                                ephemeral=False)

    @utils.hybcommand(globals.bot,
                      name="unban",
                      description="Unban a user from the server",
                      usage="{prfx}unban [ user ] [ reason ]",
                      help="user: the user to unban\n"
                           "reason: reason for the unban (optional)",
                      aliases=[],
                      check_func=only_staff)
    async def unban(self, ctx, user: discord.Member, *, reason: str = ""):
        await user.unban(reason=f"Issuer: {ctx.author}" + (f": {reason}" if reason else ""))
        await utils.embed_reply(ctx,
                                title="👌 Behave, or else...",
                                description=f"{user.mention} was just **unbanned** by {ctx.author.mention}!\n" +
                                            (f"**Reason**: {reason}" if reason else ""),
                                ephemeral=False)

    @utils.hybcommand(globals.bot,
                      name="kick",
                      description="Kick a user from the server",
                      usage="{prfx}kick [ user ] [ reason ]",
                      help="user: the user to kick\n"
                           "reason: reason for the kick (optional)",
                      aliases=[],
                      check_func=only_staff)
    async def kick(self, ctx, user: discord.Member, *, reason: str = ""):
        await user.kick(reason=f"Issuer: {ctx.author}" + (f": {reason}" if reason else ""))
        await utils.embed_reply(ctx,
                                title="👌 Out of here, punk!",
                                description=f"{user.mention} was just **kicked** by {ctx.author.mention}!\n" +
                                            (f"**Reason**: {reason}" if reason else ""),
                                ephemeral=False)

    @utils.hybcommand(globals.bot,
                      name="mute",
                      description="Mute a user from all channels",
                      usage="{prfx}mute [ user ] [ reason ]",
                      help="user: the user to mute\n"
                           "reason: reason for the mute (optional)",
                      aliases=[],
                      check_func=only_staff)
    async def mute(self, ctx, user: discord.Member, *, reason: str = ""):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await utils.embed_reply(ctx,
                                    title="💢 There is no 'Muted' role configured!")
            return
        if muted_role in user.roles:
            await utils.embed_reply(ctx,
                                    title="💢 This user is already muted!")
            return
        await user.add_roles(muted_role, reason=f"Mute command, Issuer: {ctx.author}" + (f": {reason}" if reason else ""))
        await utils.embed_reply(ctx,
                                title="👌 Silence, scum!",
                                description=f"{user.mention} was just **muted** by {ctx.author.mention}!\n" +
                                            (f"**Reason**: {reason}" if reason else ""),
                                ephemeral=False)

    @utils.hybcommand(globals.bot,
                      name="unmute",
                      description="Unmute a user from all channels",
                      usage="{prfx}unmute [ user ] [ reason ]",
                      help="user: the user to unmute\n"
                           "reason: reason for the unmute (optional)",
                      aliases=[],
                      check_func=only_staff)
    async def unmute(self, ctx, user: discord.Member, *, reason: str = ""):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            await utils.embed_reply(ctx,
                                    title="💢 There is no 'Muted' role configured!")
            return
        if muted_role not in user.roles:
            await utils.embed_reply(ctx,
                                    title="💢 This user is not muted!")
            return
        await user.remove_roles(muted_role, reason=f"Unmute command, Issuer: {ctx.author}" + (f": {reason}" if reason else ""))
        await utils.embed_reply(ctx,
                                title="👌 Please think before speaking...",
                                description=f"{user.mention} was just **unmuted** by {ctx.author.mention}!\n" +
                                            (f"**Reason**: {reason}" if reason else ""),
                                ephemeral=False)


async def setup(bot):
    await bot.add_cog(Staff(bot))
