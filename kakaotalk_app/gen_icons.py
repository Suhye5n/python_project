from PIL import Image, ImageDraw

RADIUS_RATIO = 0.225
SOURCE = "icons/source/talk-icon.jpg"

def rounded_mask(size, radius_ratio=RADIUS_RATIO):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    radius = int(size * radius_ratio)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask

def make_icon(source, size):
    square = source.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size))
    out.paste(square, (0, 0), rounded_mask(size))
    return out

source = Image.open(SOURCE).convert("RGB")
side = min(source.size)
left = (source.width - side) // 2
top = (source.height - side) // 2
source = source.crop((left, top, left + side, top + side))

for size, name in [(1024, "icon-1024.png"), (512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png"), (167, "icon-167.png"), (152, "icon-152.png")]:
    make_icon(source, size).save(f"icons/{name}")

print("done")
