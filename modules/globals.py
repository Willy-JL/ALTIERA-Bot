from asyncio import AbstractEventLoop
from discord.ext.commands import Bot
from aiohttp import ClientSession
from aiosqlite import Connection
from PIL import ImageFont, Image
from datetime import datetime


# System stuff
bot                      : Bot               = None
cur_presence             : int               = None
db                       : Connection        = None
http                     : ClientSession     = None
loop                     : AbstractEventLoop = None
restart_dt               : datetime          = None
start_dt                 : datetime          = None
ticking_cooldowns        : bool              = None
write_as_token           : str               = None

# User configurable vars, Heroku's "Config Vars" are suggested
ADMIN_ID                 : int               = None
ASSISTANCE_CATEGORY_IDS  : list              = None
BLACKLISTED_CHANNELS_IDS : list              = None
BOT_PREFIX               : str               = None
CONTRIB_AMOUNT           : int               = None
CONTRIB_CHANNELS_IDS     : list              = None
CONTRIB_COOLDOWN         : int               = None
DAILY_LEVEL_AMOUNT       : int               = None
DB_HOST_TYPE             : str               = None
DISCORD_TOKEN            : str               = None
GITHUB_GIST_FILENAME     : str               = None
GITHUB_GIST_ID           : str               = None
GITHUB_GIST_TOKEN        : str               = None
GITHUB_GIST_USER         : str               = None
HEROKU_TOKEN             : str               = None
ICON_ROLE_IDS            : dict              = None
IMGUR_CLIENT_ID          : str               = None
JOIN_LOG_CHANNEL_IDS     : dict              = None
LEVEL_NOTIF_CHANNEL_IDS  : dict              = None
MODDER_CATEGORY_IDS      : list              = None
MODDER_ROLE_IDS          : list              = None
NO_PERM_ICON             : str               = None
REP_CRED_AMOUNT          : int               = None
REP_ICON                 : str               = None
REQUESTS_CHANNEL_IDS     : dict              = None
REQUESTS_COOLDOWN        : int               = None
REQUESTS_ICONS           : dict              = None
STAFF_ROLE_IDS           : list              = None
TROPHY_ROLES             : list              = None
WRITE_AS_PASS            : str               = None
WRITE_AS_POST_ID         : str               = None
WRITE_AS_USER            : str               = None
XP_AMOUNT                : int               = None
XP_COOLDOWN              : int               = None

# Image components
font47                   : ImageFont         = None
font35                   : ImageFont         = None
font30                   : ImageFont         = None
font24                   : ImageFont         = None
font20                   : ImageFont         = None
font16                   : ImageFont         = None
default_avatar           : Image.Image       = None
overlays_default         : Image.Image       = None
overlays_staff           : Image.Image       = None
overlays_admin           : Image.Image       = None
shards_orange            : Image.Image       = None
shards_white             : Image.Image       = None
shards_teal              : Image.Image       = None
bars                     : dict              = None
levelups                 : dict              = None
