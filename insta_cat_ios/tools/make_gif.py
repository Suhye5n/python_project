"""공유용 애니메이션 짤(GIF). 대사를 이미지에 직접 얹습니다."""
import os, sys
from PIL import Image, ImageDraw, ImageFont

SRC_DIR, OUT = sys.argv[1], sys.argv[2]
SIZE = 320
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
LINES = ["니 미래에 방해가 되는 인스타는", "내가 날려버렸다먀"]


def fit_font(draw, lines, max_w):
    for size in range(30, 9, -1):
        f = ImageFont.truetype(FONT, size)
        if all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f
    return ImageFont.truetype(FONT, 10)


frames = []
paths = sorted(p for p in os.listdir(SRC_DIR) if p.startswith("explosion_") and p.endswith(".jpg"))
for p in paths:
    im = Image.open(os.path.join(SRC_DIR, p)).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    font = fit_font(d, LINES, SIZE * 0.92)
    lh = font.size + 6
    y = SIZE - 14 - lh * len(LINES)
    for line in LINES:
        w = d.textlength(line, font=font)
        d.text(((SIZE - w) / 2, y), line, font=font, fill=(255, 255, 255),
               stroke_width=max(2, font.size // 9), stroke_fill=(0, 0, 0))
        y += lh
    frames.append(im.convert("P", palette=Image.ADAPTIVE, colors=200))

frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
print(OUT, os.path.getsize(OUT) // 1024, "KB")

# 확인용 정지 컷
Image.open(OUT).convert("RGB").save(OUT.replace(".gif", "_still.png"))
