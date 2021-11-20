from discord.ext import commands
import traceback
import discord
import asyncio
import json
import time
import io

# Local imports
from modules import globals, db, errors, utils

cooldowns = dict()


class Requests(commands.Cog,
               description="Mod requests / ideas management\n"
                           "These commands can only be used in the dedicated mod requests channels\n"
                           "There is a 10 minute cooldown on new requests, you can add 1 image per request\n"
                           "If you are a modder and wish to work on a request, claim it with `a/claim [ id ]`\n"
                           "When it is complete, release it with `a/release [ id ] [ link ]`\n"
                           "If a request already exists in a mod, link it with `a/link [ id ] [ link ]`"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="new",
                      description="Create a new mod request",
                      usage="{prfx}new [ description ]",
                      help="description: your request (required), you can optionally add a single image (attachment)",
                      aliases=["create", "request", "suggest"])
    async def new(self, ctx, *, description: str = None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or ()
        if ctx.channel.id not in req_channels:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{'>, <#'.join([str(chan) for chan in req_channels])}>")
            return
        # Cooldown
        if ctx.author.id in cooldowns:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 You're on cooldown!",
                                                               description="You can only post one request every 10 minutes!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 You're on cooldown!",
                                                                description="You can only post one request every 10 minutes!"),
                                       delete_after=5)
            return
        # Missing arguments
        description = utils.strip_argument(description)
        if not description:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a description of your request!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a description of your request!"),
                                       delete_after=5)
            return
        # Image stuff
        image = ""
        for attachment in ctx.message.attachments:
            if "image" in str(attachment.content_type):
                img_bytes = await attachment.read(use_cached=True)
                try:
                    image = await utils.imgur_image_upload(img_bytes)
                except errors.FileTooBig as exc:
                    try:
                        await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                       title="💢 The image you attached is too large!",
                                                                       description=f"Only files smaller than {utils.pretty_size(exc.maximum)} are allowed. The image you attached is {utils.pretty_size(exc.size, 1)} and has been therefore ignored."))
                    except Exception:
                        await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                               embed=utils.custom_embed(ctx.guild,
                                                                        title="💢 The image you attached is too large!",
                                                                        description=f"Only files smaller than {utils.pretty_size(exc.maximum)} are allowed. The image you attached is {utils.pretty_size(exc.size, 1)} and has been therefore ignored."),
                                               delete_after=5)
                except errors.ImgurError as exc:
                    exc_str = "".join(traceback.format_exception(*exc.exc_info))
                    resp_str = json.dumps(exc.resp, indent=4)
                    fp = io.BytesIO()
                    fp.write(bytes(exc_str + "\n\nResponse:\n" + resp_str, encoding="utf-8"))
                    try:
                        fp.seek(0)
                        await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                       title="💢 Something went wrong with your image!",
                                                                       description="Please report this issue [here](https://github.com/Willy-JL/ALTIERA-Bot/issues) with the attached error info file."),
                                              file=discord.File(fp, filename="error_info.txt"))
                    except Exception:
                        fp.seek(0)
                        await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                               embed=utils.custom_embed(ctx.guild,
                                                                        title="💢 Something went wrong with your image!",
                                                                        description="Please report this issue [here](https://github.com/Willy-JL/ALTIERA-Bot/issues) with the attached error info file."),
                                               delete_after=5,
                                               file=discord.File(fp, filename="error_info.txt"))
                break
        # Actual command
        req_id = await db.create_request(ctx.author.id, description, image)
        req_msg = await ctx.channel.send(embed=utils.custom_embed(ctx.guild,
                                                                  title=f"Request #`{req_id}`",
                                                                  description=description,
                                                                  fields=[
                                                                      ["Requester:", f"<@!{ctx.author.id}>\n(`{ctx.author}`)", True],
                                                                      ["Status:",    "Waiting",                                True],
                                                                      ["Modder:",    "TBD",                                    True]
                                                                  ],
                                                                  thumbnail=globals.REQUESTS_ICONS["Waiting"],
                                                                  image=image))
        await db.add_request_message_info(req_id, req_msg)
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()
        if not utils.is_staff(ctx.author) and not utils.user_has_a_role(ctx.author, globals.MODDER_ROLE_IDS):
            cooldowns[ctx.author.id] = time.time() + globals.REQUESTS_COOLDOWN

    @commands.command(name="edit",
                      description="Edit a mod request's description",
                      usage="{prfx}edit [ id ] [ description ]",
                      help="id: the id of the request to edit (required)\n"
                           "description: your request (required), you can optionally add a single image (attachment)\n"
                           "if you don't add a new image this will keep the old image, or you can remove it by adding `REMOVE IMAGE` anywhere in the description",
                      aliases=["modify"])
    async def edit(self, ctx, req_id=None, *, description: str = None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or ()
        if ctx.channel.id not in req_channels:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{'>, <#'.join([str(chan) for chan in req_channels])}>")
            return
        # Handle arguments
        try:
            req_id = int(utils.strip_argument(req_id))
        except (TypeError, ValueError,):
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a valid request id!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a valid request id!"),
                                       delete_after=5)
            return
        # Database stuff
        try:
            requester_id, modder_id, status, link, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "link", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 There is no request with id `{req_id}`!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title=f"💢 There is no request with id `{req_id}`!"),
                                       delete_after=5)
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id not in (requester_id, modder_id,):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot edit someone else's request!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot edit someone else's request!"),
                                           delete_after=5)
                return
            if status in ("Already Exists", "Released", "WIP",) and ctx.author.id == requester_id:
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot edit a request that has been claimed!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot edit a request that has been claimed!"),
                                           delete_after=5)
                return
        # Missing arguments
        remove_image = "REMOVE IMAGE" in description
        if remove_image:
            description = description.replace("REMOVE IMAGE", "")
        description = utils.strip_argument(description)
        if not description:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a new description for the request!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a new description for the request!"),
                                       delete_after=5)
            return
        # Image stuff
        new_image = ""
        for attachment in ctx.message.attachments:
            if "image" in str(attachment.content_type):
                img_bytes = await attachment.read(use_cached=True)
                try:
                    new_image = await utils.imgur_image_upload(img_bytes)
                except errors.FileTooBig as exc:
                    try:
                        await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                       title="💢 The image you attached is too large!",
                                                                       description=f"Only files smaller than {utils.pretty_size(exc.maximum)} are allowed. The image you attached is {utils.pretty_size(exc.size, 1)} and has been therefore ignored."))
                    except Exception:
                        await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                               embed=utils.custom_embed(ctx.guild,
                                                                        title="💢 The image you attached is too large!",
                                                                        description=f"Only files smaller than {utils.pretty_size(exc.maximum)} are allowed. The image you attached is {utils.pretty_size(exc.size, 1)} and has been therefore ignored."),
                                               delete_after=5)
                except errors.ImgurError as exc:
                    exc_str = "".join(traceback.format_exception(*exc.exc_info))
                    resp_str = json.dumps(exc.resp, indent=4)
                    fp = io.BytesIO()
                    fp.write(bytes(exc_str + "\n\nResponse:\n" + resp_str, encoding="utf-8"))
                    try:
                        fp.seek(0)
                        await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                       title="💢 Something went wrong with your image!",
                                                                       description="Please report this issue [here](https://github.com/Willy-JL/ALTIERA-Bot/issues) with the attached error info file."),
                                              file=discord.File(fp, filename="error_info.txt"))
                    except Exception:
                        fp.seek(0)
                        await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                               embed=utils.custom_embed(ctx.guild,
                                                                        title="💢 Something went wrong with your image!",
                                                                        description="Please report this issue [here](https://github.com/Willy-JL/ALTIERA-Bot/issues) with the attached error info file."),
                                               delete_after=5,
                                               file=discord.File(fp, filename="error_info.txt"))
                break
        if not remove_image:
            new_image = new_image or image
        # Actual command
        await db.edit_request(req_id, description, new_image)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@!{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)",                                                                      True],
                                                        ["Status:",    f"[Released]({link})" if status == "Released" else f"[Already Exists]({link})" if status == "Already Exists" else status,                      True],
                                                        ["Modder:",    "TBD" if status == "Waiting" else "N/A" if status == "Already Exists" else f"<@!{modder_id}>\n(`{globals.bot.get_user(modder_id) or 'N/A'}`)", True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS[status],
                                                    image=new_image))
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()

    @commands.command(name="delete",
                      description="Delete a mod request",
                      usage="{prfx}delete [ id ]",
                      help="id: the id of the request to delete (required)",
                      aliases=["remove"])
    async def delete(self, ctx, req_id=None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or ()
        if ctx.channel.id not in req_channels:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{'>, <#'.join([str(chan) for chan in req_channels])}>")
            return
        # Handle arguments
        try:
            req_id = int(utils.strip_argument(req_id))
        except (TypeError, ValueError,):
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a valid request id!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a valid request id!"),
                                       delete_after=5)
            return
        # Database stuff
        try:
            requester_id, status, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "status", "channel_id", "message_id")
        except FileNotFoundError:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 There is no request with id `{req_id}`!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title=f"💢 There is no request with id `{req_id}`!"),
                                       delete_after=5)
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != requester_id:
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot delete someone else's request!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot delete someone else's request!"),
                                           delete_after=5)
                return
            if status in ("Already Exists", "Released", "WIP",):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot delete a request that has been claimed!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot delete a request that has been claimed!"),
                                           delete_after=5)
                return
        # Actual command
        await db.delete_request(req_id=req_id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.delete()
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()

    @commands.command(name="claim",
                      description="Claim a mod request, mark it as WIP",
                      usage="{prfx}claim [ id ]",
                      help="id: the id of the request to claim (required)",
                      aliases=["wip"])
    async def claim(self, ctx, req_id=None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or ()
        if ctx.channel.id not in req_channels:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{'>, <#'.join([str(chan) for chan in req_channels])}>")
            return
        # Handle arguments
        try:
            req_id = int(utils.strip_argument(req_id))
        except (TypeError, ValueError,):
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a valid request id!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a valid request id!"),
                                       delete_after=5)
            return
        # Database stuff
        try:
            requester_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 There is no request with id `{req_id}`!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title=f"💢 There is no request with id `{req_id}`!"),
                                       delete_after=5)
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if not utils.user_has_a_role(ctx.author, globals.MODDER_ROLE_IDS):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 Only users with Modder role can claim requests!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 Only users with Modder role can claim requests!"),
                                           delete_after=5)
                return
            if status in ("Already Exists", "Released", "WIP",):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot claim a request that has already been claimed!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot claim a request that has already been claimed!"),
                                           delete_after=5)
                return
        # Actual command
        await db.claim_request(req_id, ctx.author.id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@!{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    "WIP",                                                                    True],
                                                        ["Modder:",    f"<@!{ctx.author.id}>\n(`{ctx.author}`)",                                 True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["WIP"],
                                                    image=image))
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()

    @commands.command(name="unclaim",
                      description="Unclaim a mod request, remove WIP status",
                      usage="{prfx}unclaim [ id ]",
                      help="id: the id of the request to unclaim (required)",
                      aliases=["abandon"])
    async def unclaim(self, ctx, req_id=None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or ()
        if ctx.channel.id not in req_channels:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{'>, <#'.join([str(chan) for chan in req_channels])}>")
            return
        # Handle arguments
        try:
            req_id = int(utils.strip_argument(req_id))
        except (TypeError, ValueError,):
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a valid request id!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a valid request id!"),
                                       delete_after=5)
            return
        # Database stuff
        try:
            requester_id, modder_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 There is no request with id `{req_id}`!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title=f"💢 There is no request with id `{req_id}`!"),
                                       delete_after=5)
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != modder_id:
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 Only the modder assigned to this request can unclaim it!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 Only the modder assigned to this request can unclaim it!"),
                                           delete_after=5)
                return
            if status in ("Released", "Already Exists",):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot unclaim a request that has been released!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot unclaim a request that has been released!"),
                                           delete_after=5)
                return
        # Actual command
        await db.unclaim_request(req_id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@!{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    "Waiting",                                                                True],
                                                        ["Modder:",    "TBD",                                                                    True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["Waiting"],
                                                    image=image))
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()

    @commands.command(name="release",
                      description="Release a mod request, needs to be claimed first",
                      usage="{prfx}release [ id ] [ link ]",
                      help="id: the id of the request to release (required)\n"
                           "link: the link to the released mod (required)",
                      aliases=["publish"])
    async def release(self, ctx, req_id=None, link=None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or ()
        if ctx.channel.id not in req_channels:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{'>, <#'.join([str(chan) for chan in req_channels])}>")
            return
        # Handle arguments
        try:
            req_id = int(utils.strip_argument(req_id))
        except (TypeError, ValueError,):
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a valid request id!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a valid request id!"),
                                       delete_after=5)
            return
        # Database stuff
        try:
            requester_id, modder_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 There is no request with id `{req_id}`!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title=f"💢 There is no request with id `{req_id}`!"),
                                       delete_after=5)
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != modder_id:
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 Only the modder assigned to this request can release it!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 Only the modder assigned to this request can release it!"),
                                           delete_after=5)
                return
            if status in ("Already Exists",):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot release a request that has been linked!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot release a request that has been linked!"),
                                           delete_after=5)
                return
        # Missing arguments
        link = utils.strip_argument(link)
        if not link:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a link for the mod!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a link for the mod!"),
                                       delete_after=5)
            return
        # Actual command
        await db.release_request(req_id, ctx.author.id, link)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@!{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    f"[Released]({link})",                                                    True],
                                                        ["Modder:",    f"<@!{ctx.author.id}>\n(`{ctx.author}`)",                                 True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["Released"],
                                                    image=image))
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()

    @commands.command(name="unrelease",
                      description="Unrelease a mod request, remove release link and status",
                      usage="{prfx}unrelease [ id ]",
                      help="id: the id of the request to unrelease (required)",
                      aliases=["takedown"])
    async def unrelease(self, ctx, req_id=None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or ()
        if ctx.channel.id not in req_channels:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{'>, <#'.join([str(chan) for chan in req_channels])}>")
            return
        # Handle arguments
        try:
            req_id = int(utils.strip_argument(req_id))
        except (TypeError, ValueError,):
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a valid request id!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a valid request id!"),
                                       delete_after=5)
            return
        # Database stuff
        try:
            requester_id, modder_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 There is no request with id `{req_id}`!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title=f"💢 There is no request with id `{req_id}`!"),
                                       delete_after=5)
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != modder_id:
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 Only the modder assigned to this request can unrelease it!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 Only the modder assigned to this request can unrelease it!"),
                                           delete_after=5)
                return
            if status in ("WIP", "Already Released",):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot unrelease a request that has not been released!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot unrelease a request that has not been released!"),
                                           delete_after=5)
                return
        # Actual command
        await db.unrelease_request(req_id, ctx.author.id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@!{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    "WIP",                                                                    True],
                                                        ["Modder:",    f"<@!{ctx.author.id}>\n(`{ctx.author}`)",                                 True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["WIP"],
                                                    image=image))
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()

    @commands.command(name="link",
                      description="Link a mod request, mark as Already Exists",
                      usage="{prfx}link [ id ] [ link ]",
                      help="id: the id of the request to link (required)\n"
                           "link: the link to the released mod (required)",
                      aliases=["exists", "alreadyexists"])
    async def link(self, ctx, req_id=None, link=None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or ()
        if ctx.channel.id not in req_channels:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{'>, <#'.join([str(chan) for chan in req_channels])}>")
            return
        # Handle arguments
        try:
            req_id = int(utils.strip_argument(req_id))
        except (TypeError, ValueError,):
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a valid request id!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a valid request id!"),
                                       delete_after=5)
            return
        # Database stuff
        try:
            requester_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 There is no request with id `{req_id}`!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title=f"💢 There is no request with id `{req_id}`!"),
                                       delete_after=5)
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if not utils.user_has_a_role(ctx.author, globals.MODDER_ROLE_IDS):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 Only users with Modder role can link requests!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 Only users with Modder role can link requests!"),
                                           delete_after=5)
                return
            if status in ("Already Exists", "Released", "WIP",):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot link a request that has already been claimed!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot link a request that has already been claimed!"),
                                           delete_after=5)
                return
        # Missing arguments
        link = utils.strip_argument(link)
        if not link:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a link for the mod!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a link for the mod!"),
                                       delete_after=5)
            return
        # Actual command
        await db.link_request(req_id, ctx.author.id, link)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@!{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    f"[Already Exists]({link})",                                              True],
                                                        ["Modder:",    "N/A",                                                                    True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["Already Exists"],
                                                    image=image))
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()

    @commands.command(name="unlink",
                      description="Unlink a mod request, remove Already Exists status and link",
                      usage="{prfx}unlink [ id ]",
                      help="id: the id of the request to unlink (required)",
                      aliases=[])
    async def unlink(self, ctx, req_id=None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        req_channels = globals.REQUESTS_CHANNEL_IDS.get(str(ctx.guild.id)) or ()
        if ctx.channel.id not in req_channels:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{'>, <#'.join([str(chan) for chan in req_channels])}>")
            return
        # Handle arguments
        try:
            req_id = int(utils.strip_argument(req_id))
        except (TypeError, ValueError,):
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title="💢 Please provide a valid request id!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title="💢 Please provide a valid request id!"),
                                       delete_after=5)
            return
        # Database stuff
        try:
            requester_id, modder_id, status, description, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "description", "image", "channel_id", "message_id")
        except FileNotFoundError:
            await ctx.message.delete()
            try:
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 There is no request with id `{req_id}`!"))
            except Exception:
                await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                       embed=utils.custom_embed(ctx.guild,
                                                                title=f"💢 There is no request with id `{req_id}`!"),
                                       delete_after=5)
            return
        # Permission checks
        if not utils.is_staff(ctx.author):
            if ctx.author.id != modder_id:
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 Only the modder assigned to this request can unlink it!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 Only the modder assigned to this request can unlink it!"),
                                           delete_after=5)
                return
            if status in ("Released", "WIP",):
                await ctx.message.delete()
                try:
                    await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                                   title="💢 You cannot unlink a request that has not been linked!"))
                except Exception:
                    await ctx.channel.send(content=f"<@!{ctx.author.id}>",
                                           embed=utils.custom_embed(ctx.guild,
                                                                    title="💢 You cannot unlink a request that has not been linked!"),
                                           delete_after=5)
                return
        # Actual command
        await db.unlink_request(req_id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@!{requester_id}>\n(`{globals.bot.get_user(requester_id) or 'N/A'}`)", True],
                                                        ["Status:",    "Waiting",                                                               True],
                                                        ["Modder:",    "TBD",                                                                   True]
                                                    ],
                                                    thumbnail=globals.REQUESTS_ICONS["Waiting"],
                                                    image=image))
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Requests(bot))


async def tick_cooldowns():
    while True:
        await asyncio.sleep(5)
        to_remove = []
        for user_id, user_cooldown in cooldowns.items():
            if user_cooldown < time.time():
                to_remove.append(user_id)
        for user_id in to_remove:
            del cooldowns[user_id]


asyncio.get_event_loop().create_task(tick_cooldowns())
