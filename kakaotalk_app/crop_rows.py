from PIL import Image, ImageDraw
import os

IMG2 = "/root/.claude/uploads/e1de0fdf-94e1-51a1-bbc2-748c8e184907/1691b11f-IMG_1998.png"
IMG3 = "/root/.claude/uploads/e1de0fdf-94e1-51a1-bbc2-748c8e184907/3c353b90-IMG_1999.png"

img2 = Image.open(IMG2).convert("RGB")
img3 = Image.open(IMG3).convert("RGB")

BG = (8, 8, 8)
PAD_TOP = 24
CYCLE_1 = 192
CYCLE_2 = 211
WIDTH = 1206
EXPORT_WIDTH = 860
JPEG_QUALITY = 88

ROWS = [
    ("row-01-oh-suhyeon", img2, 822, True, False),
    ("row-02-gulbi", img2, 1033, False, True),
    ("row-03-family", img2, 1225, False, False),
    ("row-04-survival", img2, 1417, False, False),
    ("row-05-wallet", img2, 1609, False, False),
    ("row-06-account", img2, 1801, False, False),
    ("row-07-samsungcard", img2, 1993, True, False),
    ("row-08-kakaopay", img3, 264, True, False),
    ("row-09-june-pension", img3, 475, False, False),
    ("row-10-deljoie", img3, 667, False, False),
    ("row-11-reserve", img3, 859, False, False),
    ("row-12-dreami", img3, 1051, True, False),
    ("row-13-longblack", img3, 1262, True, False),
    ("row-14-friend", img3, 1470, False, True),
    ("row-15-talkcloud", img3, 1662, False, False),
    ("row-16-dihacle", img3, 1854, False, False),
    ("row-17-wsa", img3, 2046, True, False),
    ("row-18-fastcampus", img3, 2257, False, False),
]

os.makedirs("rows", exist_ok=True)

crops = []
for i, (name, src, avatar_top, two_line, editable) in enumerate(ROWS):
    row_top = avatar_top - PAD_TOP
    cycle = CYCLE_2 if two_line else CYCLE_1
    row_bottom = row_top + cycle
    if i == len(ROWS) - 1:
        row_bottom = row_top + 170
    crops.append((name, src, row_top, row_bottom, editable, avatar_top))

def export(img, path):
    if img.width > EXPORT_WIDTH:
        ratio = EXPORT_WIDTH / img.width
        img = img.resize((EXPORT_WIDTH, round(img.height * ratio)), Image.LANCZOS)
    img.convert("RGB").save(path, quality=JPEG_QUALITY, optimize=True)

for name, src, top, bottom, editable, avatar_top in crops:
    crop = src.crop((0, top, WIDTH, bottom))
    crop.save(f"rows/{name}.png")
    print(name, top, bottom, bottom - top, "editable" if editable else "")

# masked base for the two editable rows: paint over message + time text areas
MSG_BOX = (228, 108, 950, 146)   # relative to row_top offset, from 굴비 measurement
TIME_BOX = (1015, 52, 1160, 83)

for name in ("row-02-gulbi", "row-14-friend"):
    im = Image.open(f"rows/{name}.png").convert("RGB")
    draw = ImageDraw.Draw(im)
    draw.rectangle(MSG_BOX, fill=BG)
    draw.rectangle(TIME_BOX, fill=BG)
    im.save(f"rows/{name}-masked.png")

# re-export every row (and the masked variants) as compressed, downscaled JPEG
for name, *_ in ROWS:
    export(Image.open(f"rows/{name}.png"), f"rows/{name}.jpg")
    os.remove(f"rows/{name}.png")
for name in ("row-02-gulbi", "row-14-friend"):
    export(Image.open(f"rows/{name}-masked.png"), f"rows/{name}-masked.jpg")
    os.remove(f"rows/{name}-masked.png")
    os.remove(f"rows/{name}.jpg")

# standalone friend avatar crop (for chat room header/bubbles)
friend_top = 1470
avatar = img3.crop((48, friend_top, 191, friend_top + 144))
avatar.save("assets/friend-avatar.png")

print("done")
