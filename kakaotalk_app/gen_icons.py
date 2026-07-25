from PIL import Image, ImageDraw, ImageFont

BUBBLE = (61, 36, 30, 255)
YELLOW = (255, 224, 0, 255)
FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

def rounded_square(size, radius_ratio=0.225, bg=YELLOW):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * radius_ratio)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=bg)
    return img, draw

def draw_bubble(img, draw, size):
    cx, cy = size * 0.5, size * 0.44
    w, h = size * 0.7, size * 0.52
    left, top = cx - w / 2, cy - h / 2
    right, bottom = cx + w / 2, cy + h / 2
    radius = h * 0.46
    draw.rounded_rectangle([left, top, right, bottom], radius=radius, fill=BUBBLE)
    tail = [
        (cx - w * 0.16, bottom - h * 0.08),
        (cx - w * 0.34, bottom + h * 0.30),
        (cx + w * 0.02, bottom - h * 0.02),
    ]
    draw.polygon(tail, fill=BUBBLE)

    text = "TALK"
    font = ImageFont.truetype(FONT_PATH, int(h * 0.34))
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = cx - tw / 2 - bbox[0]
    ty = cy - th / 2 - bbox[1] - h * 0.02
    draw.text((tx, ty), text, font=font, fill=YELLOW)

def make_icon(size):
    img, draw = rounded_square(size)
    draw_bubble(img, draw, size)
    return img

for size, name in [(1024, "icon-1024.png"), (512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png"), (167, "icon-167.png"), (152, "icon-152.png")]:
    make_icon(size).save(f"icons/{name}")

print("done")
