from PIL import Image, ImageDraw
from discord.ext import commands
from typing import Union
import discord
import math
import io

# Local imports
from modules import db, globals, utils, xp


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["levels", "level", "cred", "assistance", "assist"])
    async def stats(self, ctx, target: Union[discord.Member, discord.User, int, str] = None):
        # Convert target input to discord.Member
        if not target:
            target = ctx.author
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

        xp_data = await db.get_user_xp(target.id)
        level =  xp.xp_to_lvl(xp_data["level"]     )
        cred =   xp.xp_to_lvl(xp_data["cred"]      )
        assist = xp.xp_to_lvl(xp_data["assistance"])
        level_next =  math.floor((level[2]  - level[1] ) * 100 / level[2] )
        cred_next =   math.floor((cred[2]   - cred[1]  ) * 100 / cred[2]  )
        assist_next = math.floor((assist[2] - assist[1]) * 100 / assist[2])

        # Setup image foundation
        img = Image.open("assets/background.png")
        draw = ImageDraw.Draw(img)
        # Draw user avatar
        if str(target.avatar_url).startswith("https://cdn.discordapp.com/embed/avatars"):
            avatar = globals.default_avatar
        else:
            avatar = (await utils.pil_img_from_link(str(target.avatar_url))).resize((200, 200))
        try:
            img.paste(avatar, (24, 18), avatar)
        except ValueError:
            img.paste(avatar, (24, 18))
        # Apply base overlay
        if utils.is_staff(target):
            img.paste(globals.staff_overlay, (0, 0), globals.staff_overlay)
        else:
            img.paste(globals.overlay,       (0, 0), globals.overlay      )
        # Draw username
        username = target.name.encode('ascii', 'replace').decode('ascii')  # Remove non-ascii glyphs
        utils.draw_text(draw, globals.font35, username, "#FFFFFF", (268, 85), 298)
        # Draw main level and cred values
        utils.draw_text(draw, globals.font47, f"LV:{level[0]}", "#009EDF", (277, 141), 999)
        utils.draw_text(draw, globals.font47, f"SC:{cred[0]}",  "#F06B02", (434, 141), 999)
        # Draw trophy shards
        x = 267
        for i in range(utils.get_trophy_amount(target)):
            if i % 2:
                img.paste(globals.shard_white,  (x, 194), globals.shard_white )
            else:
                img.paste(globals.shard_orange, (x, 194), globals.shard_orange)
            x += 24
        # Draw single level values
        utils.draw_text(draw, globals.font16, f"LVL:",        "#FFFFFF", (275, 425), 999)
        utils.draw_text(draw, globals.font24, f"{level[0]}",  "#FFFFFF", (308, 423), 999)
        utils.draw_text(draw, globals.font16, f"LVL:",        "#FFFFFF", (275, 518), 999)
        utils.draw_text(draw, globals.font24, f"{cred[0]}",   "#FFFFFF", (308, 516), 999)
        utils.draw_text(draw, globals.font16, f"LVL:",        "#F06B02", (275, 619), 999)
        utils.draw_text(draw, globals.font24, f"{assist[0]}", "#F06B02", (308, 617), 999)
        # Draw single percentage values
        if level_next >= 100:
            utils.draw_text(draw, globals.font30, f"MAX",           "#090D18", (579-globals.font30.getsize(f"MAX")[0],           398), 999)
        else:
            utils.draw_text(draw, globals.font30, f"{level_next}",  "#090D18", (565-globals.font30.getsize(f"{level_next}")[0],  398), 999)
            utils.draw_text(draw, globals.font20, f"%",             "#090D18", (565,                                             407), 999)
        if cred_next >= 100:
            utils.draw_text(draw, globals.font30, f"MAX",           "#090D18", (579-globals.font30.getsize(f"MAX")[0],           491), 999)
        else:
            utils.draw_text(draw, globals.font30, f"{cred_next}",   "#090D18", (565-globals.font30.getsize(f"{cred_next}")[0],   491), 999)
            utils.draw_text(draw, globals.font20, f"%",             "#090D18", (565,                                             500), 999)
        if assist_next >= 100:
            utils.draw_text(draw, globals.font30, f"MAX",           "#090D18", (579-globals.font30.getsize(f"MAX")[0],           593), 999)
        else:
            utils.draw_text(draw, globals.font30, f"{assist_next}", "#090D18", (565-globals.font30.getsize(f"{assist_next}")[0], 593), 999)
            utils.draw_text(draw, globals.font20, f"%",             "#090D18", (565,                                             602), 999)
        # Overlay percentage bars
        level_bar =  globals.bars[ "blue" ][utils.get_bar_index_from_lvl_percent(level_next )]
        cred_bar =   globals.bars["orange"][utils.get_bar_index_from_lvl_percent( cred_next )]
        assist_bar = globals.bars["white" ][utils.get_bar_index_from_lvl_percent(assist_next)]
        img.paste(level_bar,  (218, 457), level_bar )
        img.paste(cred_bar,   (218, 550), cred_bar  )
        img.paste(assist_bar, (218, 650), assist_bar)

        binary = io.BytesIO()
        img.save(binary, format="PNG")
        binary.seek(0)
        await ctx.reply(file=discord.File(binary, filename=username[:16] + ".png"))

    @commands.command(aliases=["xpamount", "levelxp", "credxp", "assistancexp", "assistxp"])
    async def xp(self, ctx, target: Union[discord.Member, discord.User, int, str] = None):
        # Convert target input to discord.Member
        if not target:
            target = ctx.author
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
        xp_data = await db.get_user_xp(target.id)
        await utils.embed_reply(ctx,
                                title=f"🔥 {target.name}'s XP:",
                                fields=[
                                    ["Level",      f"{xp_data['level']}",      True],
                                    ["Cred",       f"{xp_data['cred']}",       True],
                                    ["Assistance", f"{xp_data['assistance']}", True]
                                ],
                                thumbnail=target.avatar_url)

    @commands.group(aliases=["top10", "leaderboard", "ranking"], case_insensitive=True)
    async def top(self, ctx):
        if ctx.invoked_subcommand is None:
            await utils.embed_reply(ctx,
                                    title=f"🏆 Leaderboard Categories:",
                                    description=f"{globals.bot.command_prefix}top **level**: Top 10 members for Server Level\n"
                                                f"{globals.bot.command_prefix}top **cred**: Top 10 members for Server Cred\n"
                                                f"{globals.bot.command_prefix}top **assistance**: Top 10 member for Assistance")

    @top.command(name="level")
    async def top_level(self, ctx):
        top_users = await db.get_top_users(10, "level")
        max_line_length = 34
        lines = []
        lines.append("User:" + "".join([" " for _ in range(max_line_length+2-len("User:")-len("Server Level XP:"))]) + "Server Level XP:")
        for i, row in enumerate(top_users):
            user = globals.bot.get_user(row["id"])
            if user:
                name = str(user.name)
            else:
                name = row["id"]
            # I know, I'm also ashamed by this one liner
            line = (name if len(name) <= (max_line_length-(len(str(row["level"]))+1)) else name[:(max_line_length-(len(str(row["level"]))+1))-3] + "...") + "".join([" " for _ in range(max_line_length-len((name if len(name) <= (max_line_length-(len(str(row["level"]))+1)) else name[:(max_line_length-(len(str(row["level"]))+1))-3] + "..."))-len(str(row["level"])))]) + str(row["level"])
            lines.append(("+ " if i % 2 else "= ") + line)
        await utils.embed_reply(ctx,
                                title=f"🏆 Server Level Leaderboard:",
                                description=f"```asciidoc\n" + "\n".join(lines) + "\n```")

    @top.command(name="cred")
    async def top_cred(self, ctx):
        top_users = await db.get_top_users(10, "cred")
        max_line_length = 34
        lines = []
        lines.append("User:" + "".join([" " for _ in range(max_line_length+2-len("User:")-len("Server Cred XP:"))]) + "Server Cred XP:")
        for i, row in enumerate(top_users):
            user = globals.bot.get_user(row["id"])
            if user:
                name = str(user.name)
            else:
                name = row["id"]
            # I know, I'm also ashamed by this one liner
            line = (name if len(name) <= (max_line_length-(len(str(row["cred"]))+1)) else name[:(max_line_length-(len(str(row["cred"]))+1))-3] + "...") + "".join([" " for _ in range(max_line_length-len((name if len(name) <= (max_line_length-(len(str(row["cred"]))+1)) else name[:(max_line_length-(len(str(row["cred"]))+1))-3] + "..."))-len(str(row["cred"])))]) + str(row["cred"])
            lines.append(("+ " if i % 2 else "= ") + line)
        await utils.embed_reply(ctx,
                                title=f"🏆 Server Cred Leaderboard:",
                                description=f"```asciidoc\n" + "\n".join(lines) + "\n```")

    @top.command(name="assistance", aliases=["assist"])
    async def top_assistance(self, ctx):
        top_users = await db.get_top_users(10, "assistance")
        max_line_length = 34
        lines = []
        lines.append("User:" + "".join([" " for _ in range(max_line_length+2-len("User:")-len("Assistance XP:"))]) + "Assistance XP:")
        for i, row in enumerate(top_users):
            user = globals.bot.get_user(row["id"])
            if user:
                name = str(user.name)
            else:
                name = row["id"]
            # I know, I'm also ashamed by this one liner
            line = (name if len(name) <= (max_line_length-(len(str(row["assistance"]))+1)) else name[:(max_line_length-(len(str(row["assistance"]))+1))-3] + "...") + "".join([" " for _ in range(max_line_length-len((name if len(name) <= (max_line_length-(len(str(row["assistance"]))+1)) else name[:(max_line_length-(len(str(row["assistance"]))+1))-3] + "..."))-len(str(row["assistance"])))]) + str(row["assistance"])
            lines.append(("+ " if i % 2 else "= ") + line)
        await utils.embed_reply(ctx,
                                title=f"🏆 Server Assistance Leaderboard:",
                                description=f"```asciidoc\n" + "\n".join(lines) + "\n```")

    @commands.command(aliases=["backup"])
    async def save(self, ctx):
        if utils.is_staff(ctx.author):
            if not await utils.save_db():
                await utils.embed_reply(ctx,
                                        title=f"💢 Failed to save remote config!")
            else:
                await ctx.message.add_reaction('👌')
            await ctx.reply(file=discord.File('db.sqlite3'))
            await ctx.author.send(file=discord.File('db.sqlite3'))

    @commands.group(case_insensitive=True)
    async def gibxp(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @gibxp.command(name="level")
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

    @gibxp.command(name="cred")
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

    @gibxp.command(name="assistance", aliases=["assist"])
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

    @commands.group(case_insensitive=True)
    async def setxp(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @setxp.command(name="level")
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

    @setxp.command(name="cred")
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

    @setxp.command(name="assistance", aliases=["assist"])
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
    bot.add_cog(Stats(bot))
