import io
import time
import json
import atexit
import requests
from PIL import Image, ImageFont

# Local imports
from modules import globals


# Get config
def get_config():
    r = requests.post('https://write.as/api/auth/login',
                      headers={
                          'Content-Type': 'application/json'
                      },
                      data=json.dumps({
                          "alias": globals.WRITE_AS_USER,
                          "pass": globals.WRITE_AS_PASS
                      }))
    globals.WRITE_AS_TOKEN = json.loads(r.text)["data"]["access_token"]
    globals.config = json.loads(requests.get(f"https://write.as/{globals.WRITE_AS_USER}/{globals.WRITE_AS_POST_ID}.txt").text)


# Save config
@atexit.register
def save_config():
    if globals.config is not None:
        print("Saving config...")
        globals.config["time"] = time.time()
        requests.post(f'https://write.as/api/collections/{globals.WRITE_AS_USER}/posts/{globals.WRITE_AS_POST_ID}',
                      headers={
                          'Authorization': f'Token {globals.WRITE_AS_TOKEN}',
                          'Content-Type': 'application/json'
                      },
                      data=json.dumps({
                          "body": json.dumps(globals.config),
                          "font": "code"
                      }))
        print("Done!")


# Setup persistent image components
def setup_persistent_components():
    globals.font47 = ImageFont.truetype("assets/square.ttf", 47)
    globals.font35 = ImageFont.truetype("assets/square.ttf", 35)
    globals.font30 = ImageFont.truetype("assets/square.ttf", 30)
    globals.font24 = ImageFont.truetype("assets/square.ttf", 24)
    globals.font20 = ImageFont.truetype("assets/square.ttf", 20)
    globals.font16 = ImageFont.truetype("assets/square.ttf", 16)

    globals.overlay = Image.open('assets/overlay.png')
    globals.staff_overlay = Image.open('assets/staff_overlay.png')

    globals.shard_orange = Image.open("assets/shard_orange.png").resize((33, 28))
    globals.shard_white = Image.open("assets/shard_white.png").resize((33, 28))

    globals.bars = {}
    for color in ["blue", "orange", "white"]:
        globals.bars[color] = []
        for i in range(11):
            globals.bars[color].append(Image.open(f"assets/bars/{color}/{i}.png"))


# Save bytes array into a readable binary object
def bytes_to_binary_object(bytes_arr):
    binary = io.BytesIO()
    binary.write(bytes_arr)
    binary.seek(0)
    return binary


# Save link image into an image object for use with pillow
def pil_img_from_link(link):
    link = link[:link.rfind(".")] + ".png?size=256"
    r = requests.get(link)
    img = Image.open(bytes_to_binary_object(r.content))
    return img.resize((200, 200))


# Draw text at coords with max width
def draw_text(draw, font, text, color, position, max_width, alignment="lt"):
    if font.getsize(text)[0] > max_width:
        cutoff = 1
        while font.getsize(text[:-cutoff] + "...")[0] > max_width:
            cutoff += 1
        draw.text(position, text[:-cutoff] + "...", fill=color, font=font, anchor=alignment)
    else:
        draw.text(position, text, fill=color, font=font, anchor=alignment)


# Get trophy count for user to draw correct amount of shards
def get_trophy_amount(user):
    count = 0
    for role in user.roles:
        if role.id in globals.TROPHY_ROLES:
            count += 1
    return count


# Find what bar to use based on percentage to next level
def get_bar_index_from_lvl_percent(percent):
    return int(str(percent // 10**2 % 10) + str(percent // 10**1 % 10))
