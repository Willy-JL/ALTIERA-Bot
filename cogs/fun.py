from discord.ext import commands
import discord

# Local imports
from modules import globals, utils


class Fun(commands.Cog,
          description="Commands for them squad lols"):
    def __init__(self, bot):
        self.bot = bot

    @utils.hybcommand(globals.bot,
                      name="cookie",
                      description="Treat someone to a CyberCookie (cosmetic, no rewards)",
                      usage="{prfx}cookie [ user ]",
                      help="user: the user to give a cookie to (ping, name, id) (optional)",
                      aliases=["cybercookie"])
    async def cookie(self, ctx, user: discord.Member = None):
        if user and user.id != ctx.author.id:
            await utils.embed_reply(ctx,
                                    content=user.mention,
                                    title="🍪 CyberCookie!",
                                    description=f"{ctx.author.mention} just gave you a delicious Cyber🤖Cookie🍪!\n"
                                                "Eat it before it vaporizes you!",
                                    thumbnail="https://cdn.discordapp.com/emojis/766054797673496596.png",
                                    ephemeral=False)
        else:
            await utils.embed_reply(ctx,
                                    title="🍪 CyberCookie!",
                                    description=f"{ctx.author.mention} doesn't have any friends yet so they treated themselves to a delicious Cyber🤖Cookie🍪!\n"
                                                "Time to eagerly eat it in complete silence!",
                                    thumbnail="https://cdn.discordapp.com/emojis/766054797673496596.png",
                                    ephemeral=False)

    @utils.hybcommand(globals.bot,
                      name="burrito",
                      description="Deliver someone a SpaceBurrito (cosmetic, no rewards)",
                      usage="{prfx}burrito [ user ]",
                      help="user: the user to give a burrito to (ping, name, id) (optional)",
                      aliases=["spaceburrito"])
    async def burrito(self, ctx, user: discord.Member = None):
        if user and user.id != ctx.author.id:
            await utils.embed_reply(ctx,
                                    content=user.mention,
                                    title="🌯 SpaceBurrito!",
                                    description=f"{ctx.author.mention} just delivered you a delicious Space🌌Burrito🌯!\n"
                                                "Eat it before it gets cold!",
                                    thumbnail="https://cdn.discordapp.com/emojis/779465397903949825.png",
                                    ephemeral=False)
        else:
            await utils.embed_reply(ctx,
                                    title="🌯 SpaceBurrito!",
                                    description=f"{ctx.author.mention} doesn't have any friends yet so they bought themselves a delicious Space🌌Burrito🌯!\n"
                                                "Time to eagerly enjoy it in complete silence!",
                                    thumbnail="https://cdn.discordapp.com/emojis/779465397903949825.png",
                                    ephemeral=False)

    @utils.hybcommand(globals.bot,
                      name="pat",
                      description="Pat someone (cosmetic, no rewards)",
                      usage="{prfx}pat [ user ]",
                      help="user: the user to pat (ping, name, id) (optional)",
                      aliases=["pet", "patpat"])
    async def pat(self, ctx, user: discord.Member = None):
        if user and user.id != ctx.author.id:
            await utils.embed_reply(ctx,
                                    content=user.mention,
                                    title="<a:PatPatPat:836341685952184388> \\*PatPat\\*",
                                    description=f"{ctx.author.mention} just delivered you a truckload of heartfelt pats!\n"
                                                "Cheer up pal, you're a wonderful person!",
                                    thumbnail="https://cdn.discordapp.com/emojis/889187488915128421.gif",
                                    ephemeral=False)
        else:
            await utils.embed_reply(ctx,
                                    title="<a:PatPatPat:836341685952184388> \\*PatPat\\*",
                                    description=f"{ctx.author.mention} doesn't have any friends yet so they tried consoling themselves with a few pats!\n"
                                                "Cheer up pal, life gets better!",
                                    thumbnail="https://cdn.discordapp.com/emojis/889190978001465476.gif",
                                    ephemeral=False)


async def setup(bot):
    await bot.add_cog(Fun(bot))
