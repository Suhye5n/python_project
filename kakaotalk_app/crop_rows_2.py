from PIL import Image
import os

IMG8 = "sources/IMG_2008.PNG"
IMG9 = "sources/IMG_2009.PNG"

img8 = Image.open(IMG8).convert("RGB")
img9 = Image.open(IMG9).convert("RGB")

PAD_TOP = 24
CYCLE_1 = 192
CYCLE_2 = 211
WIDTH = 1206
EXPORT_WIDTH = 860
JPEG_QUALITY = 88

ROWS = [
    ("row-19-cj-deljoie", img8, 807, False),
    ("row-20-loccitane", img8, 999, True),
    ("row-21-ably", img8, 1210, True),
    ("row-22-jinryang", img8, 1421, False),
    ("row-23-sibotaku", img8, 1613, False),
    ("row-24-twosome", img8, 1805, True),
    ("row-25-juvis-ad", img8, 2016, False),
    ("row-26-bithumb", img8, 2208, True),
    ("row-27-banksalad", img9, 244, True),
    ("row-28-klairs", img9, 455, True),
    ("row-29-taling", img9, 666, True),
    ("row-30-zigzag", img9, 877, True),
    ("row-31-lguplus", img9, 1088, True),
    ("row-32-kakaogift", img9, 1299, True),
    ("row-33-delipang", img9, 1510, False),
    ("row-34-starbucks", img9, 1702, True),
    ("row-35-paybook", img9, 1913, True),
    ("row-36-studyalert", img9, 2124, True),
]

os.makedirs("rows", exist_ok=True)


def export(img, path):
    if img.width > EXPORT_WIDTH:
        ratio = EXPORT_WIDTH / img.width
        img = img.resize((EXPORT_WIDTH, round(img.height * ratio)), Image.LANCZOS)
    img.convert("RGB").save(path, quality=JPEG_QUALITY, optimize=True)


for name, src, avatar_top, two_line in ROWS:
    row_top = avatar_top - PAD_TOP
    cycle = CYCLE_2 if two_line else CYCLE_1
    row_bottom = row_top + cycle
    crop = src.crop((0, row_top, WIDTH, row_bottom))
    export(crop, f"rows/{name}.jpg")
    print(name, row_top, row_bottom, row_bottom - row_top)

print("done")
