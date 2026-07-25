from PIL import Image, ImageDraw

def rounded_square(size, radius_ratio=0.225, bg=(255, 227, 0, 255)):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * radius_ratio)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=bg)
    return img, draw

def draw_bubble(draw, size):
    cx, cy = size * 0.5, size * 0.46
    w, h = size * 0.62, size * 0.5
    left, top = cx - w / 2, cy - h / 2
    right, bottom = cx + w / 2, cy + h / 2
    radius = h * 0.5
    draw.rounded_rectangle([left, top, right, bottom], radius=radius, fill=(60, 30, 10, 255))
    tail = [
        (cx - w * 0.12, bottom - h * 0.06),
        (cx - w * 0.30, bottom + h * 0.32),
        (cx + w * 0.06, bottom - h * 0.02),
    ]
    draw.polygon(tail, fill=(60, 30, 10, 255))
    eye_r = size * 0.028
    eye_y = cy - h * 0.02
    for ex in (cx - w * 0.15, cx + w * 0.15):
        draw.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r], fill=(255, 227, 0, 255))

def make_icon(size):
    img, draw = rounded_square(size)
    draw_bubble(draw, size)
    return img

for size, name in [(1024, "icon-1024.png"), (512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png"), (167, "icon-167.png"), (152, "icon-152.png")]:
    make_icon(size).save(f"icons/{name}")

print("done")
