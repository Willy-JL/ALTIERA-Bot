from discord.ext import commands
import datetime
import discord
import json
import io

# Local imports
from modules import globals, db, errors, utils


requests_channel_check = {
    "check_func": lambda ctx: ctx.channel.id in (globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or []),
    "check_title": "No requests here!",
    "check_desc": "You can use request related commands in the designated mod requests channel"
}


class Requests(commands.Cog,
               description="Mod requests / ideas management\n"
                           "These commands can only be used in the dedicated mod requests channels\n"
                           "There is a 10 minute cooldown on new requests, you can add 1 image per request\n"
                           "If you are a modder and wish to work on a request, claim it with `a/claim [ id ]`\n"
                           "When it is complete, release it with `a/release [ id ] [ link ]`\n"
                           "If a request already exists in a mod, link it with `a/link [ id ] [ link ]`"):
    def __init__(self, bot):
        self.bot = bot

    @utils.hybcommand(globals.bot,
                      name="new",
                      description="Create a new mod request",
                      usage="{prfx}new [ description ]",
                      help="description: your request (required), you can optionally add a single image (attachment)",
                      aliases=["create", "request", "suggest"],
                      cooldown_rate=1,
                      cooldown_key=lambda ctx: ctx.author.id,
                      cooldown_time=datetime.timedelta(minutes=10).total_seconds(),
                      **requests_channel_check)
    async def new(self, ctx, *, description: str, image: discord.Attachment = None):
        await utils.defer(ctx)
        attached_image = image
        description = utils.strip_argument(description)
        # Image stuff
        image = ""
        if not attached_image:
            for attachment in ctx.message.attachments:
                if "image" in str(attachment.content_type):
                    attached_image = attachment
                    break
        if attached_image:
            img_bytes = await attached_image.read(use_cached=True)
            try:
                image = await utils.imgur_image_upload(img_bytes)
            except errors.FileTooBig as exc:
                await utils.embed_reply(ctx,
                                        title="💢 The image you attached is too large!",
                                        description=f"Only files smaller than {utils.pretty_size(exc.maximum)} are allowed. The image you attached is {utils.pretty_size(exc.size, 1)} and has been therefore ignored.")
            except errors.ImgurError as exc:
                exc_str = utils.get_traceback(exc)
                resp_str = json.dumps(exc.resp, indent=4)
                await utils.embed_reply(ctx,
                                        title="💢 Something went wrong with your image!",
                                        description="Please report this issue [here](https://github.com/Willy-JL/ALTIERA-Bot/issues) with the attached error info file.",
                                        file=discord.File(io.StringIO(f"{exc_str}\n\nResponse:\n{resp_str}"), filename="error_info.txt"))
        # Actual command
        req_id = await db.create_request(ctx.author.id, description, image)
        req_msg = await ctx.channel.send(embed=utils.custom_embed(ctx.guild,
                                                                  title=f"Request #`{req_id}`",
                                                                  description=description,
                                                                  fields=[
                                                                      ["Requester:", f"{ctx.author.mention}\n(`{ctx.author}`)", True],
                                                                      ["Status:",    "Waiting",                                 True],
                                                                      ["Modder:",    "TBD",                                     True]
                                                                  ],
                                                                  thumbnail=globals.REQUESTS_ICONS["Waiting"],
                                                                  image=image))
        await db.add_request_message_info(req_id, req_msg)
        if not ctx.interaction:
            await ctx.message.delete()
        else:
            await utils.embed_reply(ctx,
                                    title="👌 Done!")

    @utils.hybcommand(globals.bot,
                      name="edit",
                      description="Edit a mod request's description",
                      usage="{prfx}edit [ id ] [ description ]",
                      help="id: the id of the request to edit (required)\n"
                           "description: your request (required), you can optionally add a single image (attachment)\n"
                           "if you don't add a new image this will keep the old image, or you can remove it by adding `REMOVE IMAGE` anywhere in the description",
                      aliases=["modify"],
                      **requests_channel_check)
    async def edit(self, ctx, id: int, *, description: str, image: discord.Attachment = None):
        await utils.defer(ctx)
        req_id = id
        attached_image = image
        description = utils.strip_argument(description)
        # Database stuff
        try:
            requester_id, modder_id, status, link, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "link", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await utils.embed_reply(ctx,
                                    title=f"💢 There is no request with id `{req_id}`!")
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id not in (requester_id, modder_id,):
                await utils.embed_reply(ctx,
                                        title="💢 You cannot edit someone else's request!")
                return
            if status in ("Already Exists", "Released", "WIP",) and ctx.author.id == requester_id:
                await utils.embed_reply(ctx,
                                        title="💢 You cannot edit a request that has been claimed!")
                return
        # Image stuff
        remove_image = "REMOVE IMAGE" in description
        if remove_image:
            description = description.replace("REMOVE IMAGE", "")
        new_image = ""
        if not attached_image:
            for attachment in ctx.message.attachments:
                if "image" in str(attachment.content_type):
                    attached_image = attachment
                    break
        if attached_image:
            img_bytes = await attached_image.read(use_cached=True)
            try:
                new_image = await utils.imgur_image_upload(img_bytes)
            except errors.FileTooBig as exc:
                await utils.embed_reply(ctx,
                                        title="💢 The image you attached is too large!",
                                        description=f"Only files smaller than {utils.pretty_size(exc.maximum)} are allowed. The image you attached is {utils.pretty_size(exc.size, 1)} and has been therefore ignored.")
            except errors.ImgurError as exc:
                exc_str = utils.get_traceback(exc)
                resp_str = json.dumps(exc.resp, indent=4)
                await utils.embed_reply(ctx,
                                        title="💢 Something went wrong with your image!",
                                        description="Please report this issue [here](https://github.com/Willy-JL/ALTIERA-Bot/issues) with the attached error info file.",
                                        file=discord.File(io.StringIO(f"{exc_str}\n\nResponse:\n{resp_str}"), filename="error_info.txt"))
        if not remove_image:
            new_image = new_image or image
        # Actual command
        await db.edit_request(req_id, description, new_image)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)",                                                                      True],
                                                        ["Status:",    f"[Released]({link})" if status == "Released" else f"[Already Exists]({link})" if status == "Already Exists" else status,                     True],
                                                        ["Modder:",    "TBD" if status == "Waiting" else "N/A" if status == "Already Exists" else f"<@{modder_id}>\n(`{globals.bot.get_user(modder_id) or 'N/A'}`)", True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS[status],
                                                    image=new_image))
        if not ctx.interaction:
            await ctx.message.delete()
        else:
            await utils.embed_reply(ctx,
                                    title="👌 Done!")

    @utils.hybcommand(globals.bot,
                      name="delete",
                      description="Delete a mod request",
                      usage="{prfx}delete [ id ]",
                      help="id: the id of the request to delete (required)",
                      aliases=["remove"],
                      **requests_channel_check)
    async def delete(self, ctx, id: int):
        await utils.defer(ctx)
        req_id = id
        # Database stuff
        try:
            requester_id, status, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "status", "channel_id", "message_id")
        except FileNotFoundError:
            await utils.embed_reply(ctx,
                                    title=f"💢 There is no request with id `{req_id}`!")
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != requester_id:
                await utils.embed_reply(ctx,
                                        title="💢 You cannot delete someone else's request!")
                return
            if status in ("Already Exists", "Released", "WIP",):
                await utils.embed_reply(ctx,
                                        title="💢 You cannot delete a request that has been claimed!")
                return
        # Actual command
        await db.delete_request(req_id=req_id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.delete()
        if not ctx.interaction:
            await ctx.message.delete()
        else:
            await utils.embed_reply(ctx,
                                    title="👌 Done!")

    @utils.hybcommand(globals.bot,
                      name="claim",
                      description="Claim a mod request, mark it as WIP",
                      usage="{prfx}claim [ id ]",
                      help="id: the id of the request to claim (required)",
                      aliases=["wip"],
                      **requests_channel_check)
    async def claim(self, ctx, id: int):
        await utils.defer(ctx)
        req_id = id
        # Database stuff
        try:
            requester_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await utils.embed_reply(ctx,
                                    title=f"💢 There is no request with id `{req_id}`!")
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if not utils.user_has_a_role(ctx.author, globals.MODDER_ROLE_IDS):
                await utils.embed_reply(ctx,
                                        title="💢 Only users with Modder role can claim requests!")
                return
            if status in ("Already Exists", "Released", "WIP",):
                await utils.embed_reply(ctx,
                                        title="💢 You cannot claim a request that has already been claimed!")
                return
        # Actual command
        await db.claim_request(req_id, ctx.author.id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    "WIP",                                                                   True],
                                                        ["Modder:",    f"{ctx.author.mention}\n(`{ctx.author}`)",                               True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["WIP"],
                                                    image=image))
        if not ctx.interaction:
            await ctx.message.delete()
        else:
            await utils.embed_reply(ctx,
                                    title="👌 Done!")

    @utils.hybcommand(globals.bot,
                      name="unclaim",
                      description="Unclaim a mod request, remove WIP status",
                      usage="{prfx}unclaim [ id ]",
                      help="id: the id of the request to unclaim (required)",
                      aliases=["abandon"],
                      **requests_channel_check)
    async def unclaim(self, ctx, id: int):
        await utils.defer(ctx)
        req_id = id
        # Database stuff
        try:
            requester_id, modder_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await utils.embed_reply(ctx,
                                    title=f"💢 There is no request with id `{req_id}`!")
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != modder_id:
                await utils.embed_reply(ctx,
                                        title="💢 Only the modder assigned to this request can unclaim it!")
                return
            if status in ("Released", "Already Exists",):
                await utils.embed_reply(ctx,
                                        title="💢 You cannot unclaim a request that has been released!")
                return
        # Actual command
        await db.unclaim_request(req_id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    "Waiting",                                                               True],
                                                        ["Modder:",    "TBD",                                                                   True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["Waiting"],
                                                    image=image))
        if not ctx.interaction:
            await ctx.message.delete()
        else:
            await utils.embed_reply(ctx,
                                    title="👌 Done!")

    @utils.hybcommand(globals.bot,
                      name="release",
                      description="Release a mod request, needs to be claimed first",
                      usage="{prfx}release [ id ] [ link ]",
                      help="id: the id of the request to release (required)\n"
                           "link: the link to the released mod (required)",
                      aliases=["publish"],
                      **requests_channel_check)
    async def release(self, ctx, id: int, link: str):
        await utils.defer(ctx)
        req_id = id
        link = utils.strip_argument(link)
        # Database stuff
        try:
            requester_id, modder_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await utils.embed_reply(ctx,
                                    title=f"💢 There is no request with id `{req_id}`!")
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != modder_id:
                await utils.embed_reply(ctx,
                                        title="💢 Only the modder assigned to this request can release it!")
                return
            if status in ("Already Exists",):
                await utils.embed_reply(ctx,
                                        title="💢 You cannot release a request that has been linked!")
                return
        # Actual command
        await db.release_request(req_id, ctx.author.id, link)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    f"[Released]({link})",                                                   True],
                                                        ["Modder:",    f"{ctx.author.mention}\n(`{ctx.author}`)",                               True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["Released"],
                                                    image=image))
        if not ctx.interaction:
            await ctx.message.delete()
        else:
            await utils.embed_reply(ctx,
                                    title="👌 Done!")

    @utils.hybcommand(globals.bot,
                      name="unrelease",
                      description="Unrelease a mod request, remove release link and status",
                      usage="{prfx}unrelease [ id ]",
                      help="id: the id of the request to unrelease (required)",
                      aliases=["takedown"],
                      **requests_channel_check)
    async def unrelease(self, ctx, id: int):
        await utils.defer(ctx)
        req_id = id
        # Database stuff
        try:
            requester_id, modder_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await utils.embed_reply(ctx,
                                    title=f"💢 There is no request with id `{req_id}`!")
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != modder_id:
                await utils.embed_reply(ctx,
                                        title="💢 Only the modder assigned to this request can unrelease it!")
                return
            if status in ("WIP", "Already Released",):
                await utils.embed_reply(ctx,
                                        title="💢 You cannot unrelease a request that has not been released!")
                return
        # Actual command
        await db.unrelease_request(req_id, ctx.author.id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    "WIP",                                                                   True],
                                                        ["Modder:",    f"{ctx.author.mention}\n(`{ctx.author}`)",                               True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["WIP"],
                                                    image=image))
        if not ctx.interaction:
            await ctx.message.delete()
        else:
            await utils.embed_reply(ctx,
                                    title="👌 Done!")

    @utils.hybcommand(globals.bot,
                      name="link",
                      description="Link a mod request, mark as Already Exists",
                      usage="{prfx}link [ id ] [ link ]",
                      help="id: the id of the request to link (required)\n"
                           "link: the link to the released mod (required)",
                      aliases=["exists", "alreadyexists"],
                      **requests_channel_check)
    async def link(self, ctx, id: int, link: str):
        await utils.defer(ctx)
        req_id = id
        link = utils.strip_argument(link)
        # Database stuff
        try:
            requester_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await utils.embed_reply(ctx,
                                    title=f"💢 There is no request with id `{req_id}`!")
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if not utils.user_has_a_role(ctx.author, globals.MODDER_ROLE_IDS):
                await utils.embed_reply(ctx,
                                        title="💢 Only users with Modder role can link requests!")
                return
            if status in ("Already Exists", "Released", "WIP",):
                await utils.embed_reply(ctx,
                                        title="💢 You cannot link a request that has already been claimed!")
                return
        # Actual command
        await db.link_request(req_id, ctx.author.id, link)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    f"[Already Exists]({link})",                                             True],
                                                        ["Modder:",    "N/A",                                                                   True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["Already Exists"],
                                                    image=image))
        if not ctx.interaction:
            await ctx.message.delete()
        else:
            await utils.embed_reply(ctx,
                                    title="👌 Done!")

    @utils.hybcommand(globals.bot,
                      name="unlink",
                      description="Unlink a mod request, remove Already Exists status and link",
                      usage="{prfx}unlink [ id ]",
                      help="id: the id of the request to unlink (required)",
                      aliases=["nolongerexists"],
                      **requests_channel_check)
    async def unlink(self, ctx, id: int):
        await utils.defer(ctx)
        req_id = id
        # Database stuff
        try:
            requester_id, modder_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await utils.embed_reply(ctx,
                                    title=f"💢 There is no request with id `{req_id}`!")
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != modder_id:
                await utils.embed_reply(ctx,
                                        title="💢 Only the modder assigned to this request can unlink it!")
                return
            if status in ("Released", "WIP",):
                await utils.aiofiles(ctx,
                                    title="💢 You cannot unlink a request that has not been linked!")
                return
        # Actual command
        await db.unlink_request(req_id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    "Waiting",                                                               True],
                                                        ["Modder:",    "TBD",                                                                   True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["Waiting"],
                                                    image=image))
        if not ctx.interaction:
            await ctx.message.delete()
        else:
            await utils.embed_reply(ctx,
                                    title="👌 Done!")


async def setup(bot):
    await bot.add_cog(Requests(bot))
