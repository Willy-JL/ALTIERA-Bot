from PIL import Image, ImageDraw
from discord.ext import commands
from typing import Union
import discord
import math
import io

# Local imports
from modules import db, globals, utils, xp


rep_cooldown_users   = set()
daily_cooldown_users = set()


class Levelling(commands.Cog,
                description="Everything to do with levels and XP\n"
                            "There are 3 types of XP: level, cred and assistance\n"
                            "You earn level from chatting anywhere (except in bot commands channels)\n"
                            "Cred is only earned by users with modder role and only in modding channels\n"
                            "Assistance XP is generated in the hospital and support channels, everyone earns, modders earn 2x\n"
                            "There are cooldowns, spamming won't get you far"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stats",
                      description="See your server stats (level, cred, assistance)",
                      usage="{prfx}stats [ user ]",
                      help="user: the user to check stats for (ping, name, id) (optional)",
                      aliases=["levels", "level", "cred", "assistance", "assist"])
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
        if target.id == globals.ADMIN_ID:
            img = Image.open("assets/backgrounds/admin.png"  )
        elif utils.is_staff(target):
            img = Image.open("assets/backgrounds/staff.png"  )
        else:
            img = Image.open("assets/backgrounds/default.png")
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
        if target.id == globals.ADMIN_ID:
            img.paste(globals.overlays_admin,   (0, 0), globals.overlays_admin  )
        elif utils.is_staff(target):
            img.paste(globals.overlays_staff,   (0, 0), globals.overlays_staff  )
        else:
            img.paste(globals.overlays_default, (0, 0), globals.overlays_default)

        # Draw username
        username = target.name.encode('ascii', 'replace').decode('ascii')  # Remove non-ascii glyphs
        utils.draw_text(draw, globals.font35, username, "#FFFFFF", (268, 85), 298)

        # Draw main level and cred values
        utils.draw_text(draw, globals.font47, f"LV:{level[0]}", "#009EDF", (277, 141), 999)
        if target.id == globals.ADMIN_ID:
            utils.draw_text(draw, globals.font47, f"SC:{cred[0]}",  "#16F2D6", (434, 141), 999)
        else:
            utils.draw_text(draw, globals.font47, f"SC:{cred[0]}",  "#F06B02", (434, 141), 999)

        # Draw trophy shards
        x = 267
        for i in range(utils.get_trophy_amount(target)):
            if i % 2:
                img.paste(    globals.shards_white,  (x, 194), globals.shards_white )
            else:
                if target.id == globals.ADMIN_ID:
                    img.paste(globals.shards_teal,   (x, 194), globals.shards_teal  )
                else:
                    img.paste(globals.shards_orange, (x, 194), globals.shards_orange)
            x += 24

        # Draw single level values
        if target.id == globals.ADMIN_ID:
            utils.draw_text(draw, globals.font16, f"LVL:",        "#090D18", (275, 425), 999)
            utils.draw_text(draw, globals.font24, f"{level[0]}",  "#090D18", (308, 423), 999)
        else:
            utils.draw_text(draw, globals.font16, f"LVL:",        "#FFFFFF", (275, 425), 999)
            utils.draw_text(draw, globals.font24, f"{level[0]}",  "#FFFFFF", (308, 423), 999)
        utils.draw_text(draw, globals.font16, f"LVL:",        "#FFFFFF", (275, 518), 999)
        utils.draw_text(draw, globals.font24, f"{cred[0]}",   "#FFFFFF", (308, 516), 999)
        if target.id == globals.ADMIN_ID:
            utils.draw_text(draw, globals.font16, f"LVL:",        "#009EDF", (275, 619), 999)
            utils.draw_text(draw, globals.font24, f"{assist[0]}", "#009EDF", (308, 617), 999)
        else:
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
        if target.id == globals.ADMIN_ID:
            level_bar =  globals.bars[ "teal_white" ][utils.get_bar_index_from_lvl_percent(level_next )]
            cred_bar =   globals.bars[ "blue_white" ][utils.get_bar_index_from_lvl_percent( cred_next )]
            assist_bar = globals.bars[ "white_blue" ][utils.get_bar_index_from_lvl_percent(assist_next)]
        else:
            level_bar =  globals.bars[ "blue_white" ][utils.get_bar_index_from_lvl_percent(level_next )]
            cred_bar =   globals.bars["orange_white"][utils.get_bar_index_from_lvl_percent( cred_next )]
            assist_bar = globals.bars["white_orange"][utils.get_bar_index_from_lvl_percent(assist_next)]
        img.paste(level_bar,  (218, 457), level_bar )
        img.paste(cred_bar,   (218, 550), cred_bar  )
        img.paste(assist_bar, (218, 650), assist_bar)

        binary = io.BytesIO()
        img.save(binary, format="PNG")
        binary.seek(0)
        await ctx.reply(file=discord.File(binary, filename=username[:16] + ".png"))

    @commands.command(name="xp",
                      description="See your XP amounts (levels depend on XP amount)\n"
                                  "LVL1 = 1000XP, LVL2 = 2000XP, LVL3 = 3000XP, LVL4 = 4000XP and so on...",
                      usage="{prfx}xp [ user ]",
                      help="user: the user to check xp amounts for (ping, name, id) (optional)",
                      aliases=["xpamount", "levelxp", "credxp", "assistancexp", "assistxp"])
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

    @commands.group(name="top",
                      description="List top ten users per XP type",
                      usage="{prfx}top [ type ]",
                      help="type: either level, cred or assist (required)",
                      aliases=["top10", "leaderboard", "ranking"],
                      case_insensitive=True)
    async def top(self, ctx):
        if ctx.invoked_subcommand is None:
            await utils.embed_reply(ctx,
                                    title=f"🏆 Leaderboard Categories:",
                                    description=f"{globals.bot.command_prefix}top **level**: Top 10 members for Server Level\n"
                                                f"{globals.bot.command_prefix}top **cred**: Top 10 members for Server Cred\n"
                                                f"{globals.bot.command_prefix}top **assistance**: Top 10 member for Assistance")

    @top.command(name="level",
                 aliases=[])
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

    @top.command(name="cred",
                 aliases=[])
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

    @top.command(name="assistance",
                 aliases=["assist"])
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

    @commands.command(name="rep",
                      description="Gift a cool person some reputation (500 cred XP)\n"
                                  "Only once every 24 hours (or sooner if the bot restarts)",
                      usage="{prfx}rep [ user ]",
                      help="user: the user to give rep to (ping, name, id) (required)",
                      aliases=["reputation", "giverep", "givereputation"])
    async def rep(self, ctx, target: Union[discord.Member, discord.User, int, str] = None):
        if not str(ctx.author.id) in rep_cooldown_users:
            # Convert target input to discord.Member
            if not target:
                await utils.embed_reply(ctx,
                                        title=f"💢 Please provide a user to give reputation to!")
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
            if target.id == ctx.author.id:
                await utils.embed_reply(ctx,
                                        title=f"💢 Thats low even by your standards...")
                return
            # Actual command
            await db.add_user_xp(target.id, cred=globals.REP_CRED_AMOUNT)
            rep_cooldown_users.add(str(ctx.author.id))
            await utils.embed_reply(ctx,
                                    content=f"<@!{target.id}>",
                                    title=f"💌 You got some reputation!",
                                    description=f"<@!{ctx.author.id}> likes what you do and showed their gratitude by gifting you **{globals.REP_CRED_AMOUNT} server cred XP**!",
                                    thumbnail="https://cdn.discordapp.com/emojis/766042961929699358.png")
        else:
            await utils.embed_reply(ctx,
                                    title=f"💢 You're on cooldown!",
                                    description=f"You can only use that command once every **24 hours**!\n"
                                                f"You'll be able to use it again in roughly **{utils.time_to_restart()}**")

    @commands.command(name="daily",
                      description="Claim your daily reward (500 level XP)\n"
                                  "Only once every 24 hours (or sooner if the bot restarts)",
                      usage="{prfx}daily",
                      help="",
                      aliases=["riseandshine", "ijustwokeup", "gibreward", "claimdaily", "gibdaily"])
    async def daily(self, ctx):
        if not str(ctx.author.id) in daily_cooldown_users:
            await db.add_user_xp(ctx.author.id, level=globals.DAILY_LEVEL_AMOUNT)
            daily_cooldown_users.add(str(ctx.author.id))
            await utils.embed_reply(ctx,
                                    title=f"📅 Daily reward claimed!",
                                    description=f"You just grabbed yourself a cool **{globals.DAILY_LEVEL_AMOUNT} server level XP**!\n"
                                                f"Come back in roughly **{utils.time_to_restart()}** for more!",
                                    thumbnail=ctx.author.avatar_url)
        else:
            await utils.embed_reply(ctx,
                                    title=f"💢 It's called \"daily\" for a reason!",
                                    description=f"Come back in roughly **{utils.time_to_restart()}** for your next daily reward")


def setup(bot):
    bot.add_cog(Levelling(bot))
