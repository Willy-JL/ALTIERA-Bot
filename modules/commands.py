import io
import math
import discord
from typing import Union
from discord.ext import commands
from PIL import Image, ImageDraw

# Local imports
from modules import utils, globals, xp


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def stats(self, ctx, target: Union[discord.Member, discord.User, int] = None):  
        # Convert target input to discord.Member
        if not target:
            target = ctx.author
        if isinstance(target, int):
            target = ctx.guild.get_member(target)
        elif isinstance(target, discord.User):
            target = ctx.guild.get_member(target.id)
        elif isinstance(target, discord.Member):
            pass
        else:
            await ctx.message.reply("That is not a valid user!")
            return
        if not target:
            await ctx.message.reply("That is not a valid user!")
            return

        # Actual command

        xp.ensure_user_data(target.id)
        print(globals.config)
        level =  xp.xp_to_lvl(globals.config[str(target.id)][0])
        cred =   xp.xp_to_lvl(globals.config[str(target.id)][1])
        assist = xp.xp_to_lvl(globals.config[str(target.id)][2])
        level_next =  math.floor((level[2]  - level[1] ) * 100 / level[2] )
        cred_next =   math.floor((level[2]  - level[1] ) * 100 / level[2] )
        assist_next = math.floor((assist[2] - assist[1]) * 100 / assist[2])

        # Setup image foundation
        img = Image.open("assets/background.png")
        draw = ImageDraw.Draw(img)
        # Draw user avatar
        avatar = utils.pil_img_from_link(str(target.avatar_url))
        img.paste(avatar, (24, 18), avatar)
        # Apply base overlay
        if globals.STAFF_ROLE_ID in [role.id for role in target.roles]:
            img.paste(globals.staff_overlay, (0, 0), globals.staff_overlay)
        else:
            img.paste(globals.overlay,       (0, 0), globals.overlay      )
        # Draw username
        username = target.name.encode('ascii', 'replace').decode('ascii')  # Remove non-ascii glyphs
        utils.draw_text(draw, globals.font35, username, "#FFFFFF", (268, 79), 298)
        # Draw main level and cred values
        utils.draw_text(draw, globals.font47, f"LV:{level[0]}", "#009EDF", (277, 135), 999)
        utils.draw_text(draw, globals.font47, f"SC:{cred[0]}",  "#F06B02", (434, 135), 999)
        # Draw trophy shards
        x = 267
        for i in range(utils.get_trophy_amount(target)):
            if i % 2:
                img.paste(globals.shard_white,  (x, 194), globals.shard_white )
            else:
                img.paste(globals.shard_orange, (x, 194), globals.shard_orange)
            x += 24
        # Draw single level values
        utils.draw_text(draw, globals.font16, f"LVL:",        "#FFFFFF", (274, 422), 999)
        utils.draw_text(draw, globals.font24, f"{level[0]}",  "#FFFFFF", (308, 420), 999)
        utils.draw_text(draw, globals.font16, f"LVL:",        "#FFFFFF", (274, 515), 999)
        utils.draw_text(draw, globals.font24, f"{cred[0]}",   "#FFFFFF", (308, 513), 999)
        utils.draw_text(draw, globals.font16, f"LVL:",        "#F06B02", (274, 616), 999)
        utils.draw_text(draw, globals.font24, f"{assist[0]}", "#F06B02", (308, 614), 999)
        # Draw single percentage values
        if level_next >= 100:
            utils.draw_text(draw, globals.font30, f"MAX",           "#090D18", (569-globals.font30.getsize(f"MAX")[0],           392), 999, "rt")
        else:
            utils.draw_text(draw, globals.font30, f"{level_next}",  "#090D18", (565-globals.font30.getsize(f"{level_next}")[0],  392), 999, "rt")
            utils.draw_text(draw, globals.font20, f"%",             "#090D18", (565,                                             401), 999      )
        if cred_next >= 100:
            utils.draw_text(draw, globals.font30, f"MAX",           "#090D18", (569-globals.font30.getsize(f"MAX")[0],           485), 999, "rt")
        else:
            utils.draw_text(draw, globals.font30, f"{cred_next}",   "#090D18", (565-globals.font30.getsize(f"{cred_next}")[0],   485), 999, "rt")
            utils.draw_text(draw, globals.font20, f"%",             "#090D18", (565,                                             494), 999      )
        if assist_next >= 100:
            utils.draw_text(draw, globals.font30, f"MAX",           "#090D18", (569-globals.font30.getsize(f"MAX")[0],           588), 999, "rt")
        else:
            utils.draw_text(draw, globals.font30, f"{assist_next}", "#090D18", (565-globals.font30.getsize(f"{assist_next}")[0], 588), 999, "rt")
            utils.draw_text(draw, globals.font20, f"%",             "#090D18", (565,                                             597), 999      )
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
        await ctx.message.reply(file=discord.File(binary, filename=username[:16] + ".png"))


def setup(bot):
    bot.add_cog(Commands(bot))
