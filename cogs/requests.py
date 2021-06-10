from discord.ext import commands

# Local imports
from modules import db, globals, utils


class Requests(commands.Cog,
               description="Mod requests / ideas management"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="create",
                      description="Create a new mod request / idea",
                      usage="{prfx}create [ description ]",
                      help="description: your request, you can add a single image (attachment) (required)",
                      aliases=["request", "suggest"])
    async def create(self, ctx, *, description: str = None):
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
                                                                  thumbnail="https://cdn.discordapp.com/emojis/777999272456486923.png",
                                                                  image=image))
        await ctx.message.delete()

        await db.add_request_message_info(req_id, req_msg)


def setup(bot):
    bot.add_cog(Requests(bot))
