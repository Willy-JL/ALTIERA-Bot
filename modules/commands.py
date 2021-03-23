import io
import math
import json
import discord
import datetime
from typing import Union
from discord.ext import commands
from PIL import Image, ImageDraw
from fuzzywuzzy import process, fuzz

# Local imports
from modules import utils, globals, xp


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def stats(self, ctx, target: Union[discord.Member, discord.User, int, str] = None):  
        # Convert target input to discord.Member
        if not target:
            target = ctx.author
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            name_list = [user.name for user in ctx.guild.members] + [user.nick for user in ctx.guild.members if user.nick]
            results = [result[0] for result in process.extract(target, name_list, scorer=fuzz.ratio, limit=20)]
            results.sort(key=lambda x: [xp.ensure_user_data(str(ctx.guild.get_member_named(x).id)), globals.config[str(ctx.guild.get_member_named(x).id)][0]][1], reverse=True)
            target = ctx.guild.get_member_named(results[0])
        elif isinstance(target, discord.User):
            target = ctx.guild.get_member(target.id)
        elif isinstance(target, discord.Member):
            pass
        else:
            await ctx.reply("That is not a valid user!")
            return
        if not target:
            await ctx.reply("That is not a valid user!")
            return

        # Actual command

        xp.ensure_user_data(str(target.id))
        level =  xp.xp_to_lvl(globals.config[str(target.id)][0])
        cred =   xp.xp_to_lvl(globals.config[str(target.id)][1])
        assist = xp.xp_to_lvl(globals.config[str(target.id)][2])
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
            avatar = utils.pil_img_from_link(str(target.avatar_url))
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

    @commands.command()
    async def xp(self, ctx, target: Union[discord.Member, discord.User, int, str] = None):  
        # Convert target input to discord.Member
        if not target:
            target = ctx.author
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, str):
            name_list = [user.name for user in ctx.guild.members] + [user.nick for user in ctx.guild.members if user.nick]
            results = [result[0] for result in process.extract(target, name_list, scorer=fuzz.ratio, limit=20)]
            results.sort(key=lambda x: [xp.ensure_user_data(str(ctx.guild.get_member_named(x).id)), globals.config[str(ctx.guild.get_member_named(x).id)][0]][1], reverse=True)
            target = ctx.guild.get_member_named(results[0])
        elif isinstance(target, discord.User):
            target = ctx.guild.get_member(target.id)
        elif isinstance(target, discord.Member):
            pass
        else:
            await ctx.reply("That is not a valid user!")
            return
        if not target:
            await ctx.reply("That is not a valid user!")
            return

        # Actual command
        xp.ensure_user_data(str(target.id))
        await ctx.reply(embed=discord.Embed(title=f"{target.name}'s XP:",
                                            color=discord.Color(0xEDE400),
                                            timestamp=datetime.datetime.utcnow())
                                            .add_field(name="Level",
                                                       value=f"{globals.config[str(target.id)][0]}",
                                                       inline=True)
                                            .add_field(name="Cred",
                                                       value=f"{globals.config[str(target.id)][1]}",
                                                       inline=True)
                                            .add_field(name="Assistance",
                                                       value=f"{globals.config[str(target.id)][2]}",
                                                       inline=True)
                                            .set_thumbnail(url=target.avatar_url)
                                            .set_footer(text=ctx.guild.name,
                                                        icon_url=ctx.guild.icon_url))

    @commands.group()
    async def top(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply(embed=discord.Embed(title="Leaderboard Categories:",
                                                description=f"{globals.bot.command_prefix}top **level**: Top 10 members for Server Level\n"
                                                            f"{globals.bot.command_prefix}top **cred**: Top 10 members for Server Cred\n"
                                                            f"{globals.bot.command_prefix}top **assistance**: Top 10 member for Assistance",
                                                color=discord.Color(0xEDE400),
                                                timestamp=datetime.datetime.utcnow())
                                                .set_footer(text=ctx.guild.name,
                                                            icon_url=ctx.guild.icon_url))

    @top.command(name="level")
    async def top_level(self, ctx):
        uids = [uid for uid in globals.config if isinstance(globals.config[uid], list) and len(globals.config[uid]) == 3]
        uids.sort(key=lambda x: globals.config[x][0], reverse=True)
        uids = uids[:10]
        max_line_length = 34
        lines = []
        lines.append("User:" + "".join([" " for _ in range(max_line_length+2-len("User:")-len("Server Level XP:"))]) + "Server Level XP:")
        for i, uid in enumerate(uids):
            user = globals.bot.get_user(int(uid))
            if user:
                name = str(user.name)
            else:
                name = uid
            xp = globals.config[uid][0]
            # I know, I'm also ashamed by this one liner
            line = (name if len(name) <= (max_line_length-(len(str(xp))+1)) else name[:(max_line_length-(len(str(xp))+1))-3] + "...") + "".join([" " for _ in range(max_line_length-len((name if len(name) <= (max_line_length-(len(str(xp))+1)) else name[:(max_line_length-(len(str(xp))+1))-3] + "..."))-len(str(xp)))]) + str(xp)
            lines.append(("+ " if i % 2 else "= ") + line)
        await ctx.reply(embed=discord.Embed(title="Server Level Leaderboard:",
                                            description="```asciidoc\n" + "\n".join(lines) + "\n```",
                                            color=discord.Color(0xEDE400),
                                            timestamp=datetime.datetime.utcnow())
                                            .set_footer(text=ctx.guild.name,
                                                        icon_url=ctx.guild.icon_url))

    @top.command(name="cred")
    async def top_cred(self, ctx):
        uids = [uid for uid in globals.config if isinstance(globals.config[uid], list) and len(globals.config[uid]) == 3]
        uids.sort(key=lambda x: globals.config[x][1], reverse=True)
        uids = uids[:10]
        max_line_length = 34
        lines = []
        lines.append("User:" + "".join([" " for _ in range(max_line_length+2-len("User:")-len("Server Cred XP:"))]) + "Server Cred XP:")
        for i, uid in enumerate(uids):
            user = globals.bot.get_user(int(uid))
            if user:
                name = str(user.name)
            else:
                name = uid
            xp = globals.config[uid][1]
            # I know, I'm also ashamed by this one liner
            line = (name if len(name) <= (max_line_length-(len(str(xp))+1)) else name[:(max_line_length-(len(str(xp))+1))-3] + "...") + "".join([" " for _ in range(max_line_length-len((name if len(name) <= (max_line_length-(len(str(xp))+1)) else name[:(max_line_length-(len(str(xp))+1))-3] + "..."))-len(str(xp)))]) + str(xp)
            lines.append(("+ " if i % 2 else "= ") + line)
        await ctx.reply(embed=discord.Embed(title="Server Cred Leaderboard:",
                                            description="```asciidoc\n" + "\n".join(lines) + "\n```",
                                            color=discord.Color(0xEDE400),
                                            timestamp=datetime.datetime.utcnow())
                                            .set_footer(text=ctx.guild.name,
                                                        icon_url=ctx.guild.icon_url))

    @top.command(name="assistance", aliases=["assist"])
    async def top_assistance(self, ctx):
        uids = [uid for uid in globals.config if isinstance(globals.config[uid], list) and len(globals.config[uid]) == 3]
        uids.sort(key=lambda x: globals.config[x][2], reverse=True)
        uids = uids[:10]
        max_line_length = 34
        lines = []
        lines.append("User:" + "".join([" " for _ in range(max_line_length+2-len("User:")-len("Assistance XP:"))]) + "Assistance XP:")
        for i, uid in enumerate(uids):
            user = globals.bot.get_user(int(uid))
            if user:
                name = str(user.name)
            else:
                name = uid
            xp = globals.config[uid][2]
            # I know, I'm also ashamed by this one liner
            line = (name if len(name) <= (max_line_length-(len(str(xp))+1)) else name[:(max_line_length-(len(str(xp))+1))-3] + "...") + "".join([" " for _ in range(max_line_length-len((name if len(name) <= (max_line_length-(len(str(xp))+1)) else name[:(max_line_length-(len(str(xp))+1))-3] + "..."))-len(str(xp)))]) + str(xp)
            lines.append(("+ " if i % 2 else "= ") + line)
        await ctx.reply(embed=discord.Embed(title="Assistance Leaderboard:",
                                            description="```asciidoc\n" + "\n".join(lines) + "\n```",
                                            color=discord.Color(0xEDE400),
                                            timestamp=datetime.datetime.utcnow())
                                            .set_footer(text=ctx.guild.name,
                                                        icon_url=ctx.guild.icon_url))

    @commands.command(aliases=["backup"])
    async def save(self, ctx):
        if utils.is_staff(ctx.author):
            if not utils.save_config():
                await ctx.reply("Failed to save remote config!")
            else:
                await ctx.message.add_reaction('👌')
            binary = utils.bytes_to_binary_object(json.dumps(globals.config).encode())
            await ctx.reply(file=discord.File(binary, filename="backup.json"))
            binary.seek(0)
            await ctx.author.send(file=discord.File(binary, filename="backup.json"))

    @commands.group()
    async def gibxp(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @gibxp.command(name="level")
    async def gibxp_level(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if utils.is_staff(ctx.author):
            # Convert target input to discord.Member
            if not target:
                await ctx.reply("Please provide a valid user!")
                return
            if isinstance(target, int):
                target = ctx.guild.get_member(target)
            elif isinstance(target, str):
                name_list = [user.name for user in ctx.guild.members] + [user.nick for user in ctx.guild.members if user.nick]
                results = [result[0] for result in process.extract(target, name_list, scorer=fuzz.ratio, limit=20)]
                results.sort(key=lambda x: [xp.ensure_user_data(str(ctx.guild.get_member_named(x).id)), globals.config[str(ctx.guild.get_member_named(x).id)][0]][1], reverse=True)
                target = ctx.guild.get_member_named(results[0])
            elif isinstance(target, discord.User):
                target = ctx.guild.get_member(target.id)
            elif isinstance(target, discord.Member):
                pass
            else:
                await ctx.reply("That is not a valid user!")
                return
            if not target:
                await ctx.reply("That is not a valid user!")
                return
            # Actual command
            xp.ensure_user_data(str(target.id))
            globals.config[str(target.id)][0] += amount
            await ctx.reply(f"Gave <@!{target.id}> {amount} level XP!" if amount >= 0 else f"Took {-amount} level XP from <@!{target.id}>!", allowed_mentions=discord.AllowedMentions(users=[ctx.author]))

    @gibxp.command(name="cred")
    async def gibxp_cred(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if utils.is_staff(ctx.author):
            # Convert target input to discord.Member
            if not target:
                await ctx.reply("Please provide a valid user!")
                return
            if isinstance(target, int):
                target = ctx.guild.get_member(target)
            elif isinstance(target, str):
                name_list = [user.name for user in ctx.guild.members] + [user.nick for user in ctx.guild.members if user.nick]
                results = [result[0] for result in process.extract(target, name_list, scorer=fuzz.ratio, limit=20)]
                results.sort(key=lambda x: [xp.ensure_user_data(str(ctx.guild.get_member_named(x).id)), globals.config[str(ctx.guild.get_member_named(x).id)][0]][1], reverse=True)
                target = ctx.guild.get_member_named(results[0])
            elif isinstance(target, discord.User):
                target = ctx.guild.get_member(target.id)
            elif isinstance(target, discord.Member):
                pass
            else:
                await ctx.reply("That is not a valid user!")
                return
            if not target:
                await ctx.reply("That is not a valid user!")
                return
            # Actual command
            xp.ensure_user_data(str(target.id))
            globals.config[str(target.id)][1] += amount
            await ctx.reply(f"Gave <@!{target.id}> {amount} level XP!" if amount >= 0 else f"Took {-amount} level XP from <@!{target.id}>!", allowed_mentions=discord.AllowedMentions(users=[ctx.author]))

    @gibxp.command(name="assistance", aliases=["assist"])
    async def gibxp_assistance(self, ctx, target: Union[discord.Member, discord.User, int, str] = None, amount: int = 0):
        if utils.is_staff(ctx.author):
            # Convert target input to discord.Member
            if not target:
                await ctx.reply("Please provide a valid user!")
                return
            if isinstance(target, int):
                target = ctx.guild.get_member(target)
            elif isinstance(target, str):
                name_list = [user.name for user in ctx.guild.members] + [user.nick for user in ctx.guild.members if user.nick]
                results = [result[0] for result in process.extract(target, name_list, scorer=fuzz.ratio, limit=20)]
                results.sort(key=lambda x: [xp.ensure_user_data(str(ctx.guild.get_member_named(x).id)), globals.config[str(ctx.guild.get_member_named(x).id)][0]][1], reverse=True)
                target = ctx.guild.get_member_named(results[0])
            elif isinstance(target, discord.User):
                target = ctx.guild.get_member(target.id)
            elif isinstance(target, discord.Member):
                pass
            else:
                await ctx.reply("That is not a valid user!")
                return
            if not target:
                await ctx.reply("That is not a valid user!")
                return
            # Actual command
            xp.ensure_user_data(str(target.id))
            globals.config[str(target.id)][2] += amount
            await ctx.reply(f"Gave <@!{target.id}> {amount} level XP!" if amount >= 0 else f"Took {-amount} level XP from <@!{target.id}>!", allowed_mentions=discord.AllowedMentions(users=[ctx.author]))


def setup(bot):
    bot.add_cog(Commands(bot))
