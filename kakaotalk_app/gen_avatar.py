from PIL import Image, ImageDraw

size = 200
img = Image.new("RGB", (size, size))
draw = ImageDraw.Draw(img)

top = (255, 183, 130)
bottom = (255, 120, 110)
for y in range(size):
    t = y / size
    r = int(top[0] + (bottom[0] - top[0]) * t)
    g = int(top[1] + (bottom[1] - top[1]) * t)
    b = int(top[2] + (bottom[2] - top[2]) * t)
    draw.line([(0, y), (size, y)], fill=(r, g, b))

draw.ellipse([size * 0.55, size * 0.12, size * 0.85, size * 0.42], fill=(255, 235, 205))
draw.rectangle([0, size * 0.62, size, size], fill=(30, 20, 35))

draw.ellipse([size * 0.44, size * 0.30, size * 0.56, size * 0.44], fill=(20, 15, 25))
draw.polygon(
    [
        (size * 0.42, size * 0.66),
        (size * 0.47, size * 0.42),
        (size * 0.53, size * 0.42),
        (size * 0.58, size * 0.66),
    ],
    fill=(20, 15, 25),
)

mask = Image.new("L", (size, size), 0)
mdraw = ImageDraw.Draw(mask)
mdraw.ellipse([0, 0, size, size], fill=255)
out = Image.new("RGBA", (size, size))
out.paste(img, (0, 0), mask)
out.save("assets/friend-avatar.png")
print("done")
