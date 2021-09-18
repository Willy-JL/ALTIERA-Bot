from discord.errors import NotFound
from discord.ext import commands

# Local imports
from modules import db, globals, utils


class Requests(commands.Cog,
               description="Mod requests / ideas management"):
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
        if ctx.channel.id != globals.REQUESTS_CHANNEL_IDS[str(ctx.guild.id)]:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{globals.REQUESTS_CHANNEL_IDS[str(ctx.guild.id)]}>")
            return

        if not description:
            await ctx.message.delete()
            await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                           title="💢 Please provide a description of your request!"))
            return

        description = str(description)
        image = None
        for attachment in ctx.message.attachments:
            if "image" in str(attachment.content_type):
                img_bytes = await attachment.read(use_cached=True)
                image = await utils.imgur_image_upload(img_bytes)
                break

        req_id = await db.create_request(ctx, description, image)
        req_msg = await ctx.channel.send(embed=utils.custom_embed(ctx.guild,
                                                                  title=f"Request #`{req_id}`",
                                                                  description=description,
                                                                  fields=[
                                                                      ["Requester:", f"<@!{ctx.author.id}>", True],
                                                                      ["Status:",    f"Waiting",             True],
                                                                      ["Modder:",    f"TBD",                 True]
                                                                  ],
                                                                  thumbnail=globals.REQUESTS_ICONS["Waiting"],
                                                                  image=image))
        await db.add_request_message_info(req_id, req_msg)
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()

    @commands.command(name="edit",
                      description="Edit a mod request",
                      usage="{prfx}edit [ id ] [ description ]",
                      help="id: the id of the request to edit (required)\n"
                           "description: your request (required), you can optionally add a single image (attachment)\n"
                           "if you don't add a new image this will keep the old image, or you can remove it by adding `REMOVE IMAGE` anywhere in the description",
                      aliases=["modify"])
    async def edit(self, ctx: commands.Context, req_id=None, *, description: str = None):
        if str(ctx.guild.id) not in globals.REQUESTS_CHANNEL_IDS:
            return
        if ctx.channel.id != globals.REQUESTS_CHANNEL_IDS[str(ctx.guild.id)]:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{globals.REQUESTS_CHANNEL_IDS[str(ctx.guild.id)]}>")
            return

        try:
            req_id = int(req_id)
        except (TypeError, ValueError):
            await ctx.message.delete()
            await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                           title="💢 Please provide a valid request id!"))
            return

        try:
            requester_id, modder_id, status, image, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "modder_id", "status", "image", "channel_id", "message_id")
        except NotFound:
            await ctx.message.delete()
            await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                           title=f"💢 There is no request with id `{req_id}`!"))
            return

        if not utils.is_staff(ctx.author):

            if ctx.author.id not in (requester_id, modder_id):
                await ctx.message.delete()
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 You cannot edit someone else's request!"))
                return

            if status in ("Released", "WIP") and ctx.author.id == requester_id:
                await ctx.message.delete()
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 You cannot edit a request that has been claimed!"))
                return

        if not description:
            await ctx.message.delete()
            await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                           title="💢 Please provide a new description for the request!"))
            return

        # Actual command

        description = str(description)
        new_image = None
        for attachment in ctx.message.attachments:
            if "image" in str(attachment.content_type):
                img_bytes = await attachment.read(use_cached=True)
                new_image = await utils.imgur_image_upload(img_bytes)
                break
        if "REMOVE IMAGE" in description:
            description = description.replace("REMOVE IMAGE", "")
        else:
            new_image = new_image or image

        await db.edit_request(req_id, description, new_image)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.edit(embed=utils.custom_embed(ctx.guild,
                                                    title=f"Request #`{req_id}`",
                                                    description=description,
                                                    fields=[
                                                        ["Requester:", f"<@!{requester_id}>",                                True],
                                                        ["Status:",    status,                                               True],
                                                        ["Modder:",    "TBD" if status == "Waiting" else f"<@!{modder_id}>", True]
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
        if ctx.channel.id != globals.REQUESTS_CHANNEL_IDS[str(ctx.guild.id)]:
            await utils.embed_reply(ctx,
                                    title="💢 No requests here!",
                                    description=f"You can use request related commands in <#{globals.REQUESTS_CHANNEL_IDS[str(ctx.guild.id)]}>")
            return

        try:
            req_id = int(req_id)
        except (TypeError, ValueError):
            await ctx.message.delete()
            await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                           title="💢 Please provide a valid request id!"))
            return

        try:
            requester_id, status, channel_id, message_id = await db.get_request_info(req_id, "requester_id", "status", "channel_id", "message_id")
        except NotFound:
            await ctx.message.delete()
            await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                           title=f"💢 There is no request with id `{req_id}`!"))
            return

        if not utils.is_staff(ctx.author):

            if ctx.author.id != requester_id:
                await ctx.message.delete()
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 You cannot delete someone else's request!"))
                return

            if status in ("Released", "WIP"):
                await ctx.message.delete()
                await ctx.author.send(embed=utils.custom_embed(ctx.guild,
                                                               title=f"💢 You cannot delete a request that has been claimed!"))
                return

        # Actual command

        await db.delete_request(req_id)
        req_msg = await globals.bot.get_channel(channel_id).fetch_message(message_id)
        await req_msg.delete()
        await ctx.message.add_reaction('👌')
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Requests(bot))
