"""원본 짤의 불덩이가 실제로 끓어오르며 터지는 것처럼 보이도록 루프 애니메이션을 만듭니다.

핵심은 새 폭발을 덧그리는 게 아니라, 이미 밝게 타고 있는 영역을
움직이는 난류(turbulence) 로 일렁이게 만들고 그 위에 불티를 얹는 것입니다.
모든 시간 항의 주기를 프레임 수의 정수배로 잡아 루프가 끊기지 않게 했습니다.
"""
import math, os, sys
import numpy as np
from PIL import Image

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_cat.jpg")
N = 16
SIZE = 512

CAT_C = (0.585, 0.74)
CAT_R = (0.215, 0.315)

rng = np.random.default_rng(11)
base_src = Image.open(SRC).convert("RGB")
base_full = np.asarray(base_src.resize((SIZE, SIZE), Image.LANCZOS), np.float32)

yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32) / SIZE

# 고양이는 불꽃에 덮이지 않게. 가장자리에만 살짝 빛이 걸치도록 합니다.
d_cat = np.sqrt(((xx - CAT_C[0]) / CAT_R[0]) ** 2 + ((yy - CAT_C[1]) / CAT_R[1]) ** 2)
cat_mask = np.clip((d_cat - 0.85) / 0.30, 0.0, 1.0) ** 1.3

# 이미 불이 붙어 있는 영역(=원본이 밝고 화면 위쪽)만 일렁이게 합니다.
lum = base_full.mean(-1) / 255.0
warm = np.clip((base_full[..., 0] - base_full[..., 2]) / 85.0, 0, 1)
fire_region = np.clip((lum - 0.40) / 0.35, 0, 1) ** 1.2
fire_region *= (0.30 + 0.70 * warm)
fire_region *= np.clip(1.45 - 1.5 * yy, 0, 1) * cat_mask

# 시간축이 순환하는 값 노이즈. 사인 격자와 달리 줄무늬가 생기지 않습니다.
NOISE_T = 4
NOISE_SIZES = (10, 22, 46)
NOISE_AMP = (0.5, 0.32, 0.18)
noise_grids = [rng.random((NOISE_T, s, s)).astype(np.float32) * 2 - 1 for s in NOISE_SIZES]

# 불티
K = 60
e_x = rng.uniform(0.04, 0.96, K)
e_y = rng.uniform(0.02, 0.44, K)
e_off = rng.uniform(0, 1, K)
e_rise = rng.uniform(0.10, 0.30, K)
e_sway = rng.uniform(0.006, 0.03, K)
e_size = rng.uniform(0.0030, 0.0080, K)

# 불덩이 가장자리에서 혀처럼 솟는 불꽃
L = 24
l_x = rng.uniform(0.06, 0.94, L)
l_y = rng.uniform(0.14, 0.42, L)
l_off = rng.uniform(0, 1, L)
l_size = rng.uniform(0.035, 0.085, L)
l_rise = rng.uniform(0.05, 0.14, L)


def sample_grid(grid, t):
    """t 를 따라 순환 보간한 뒤 화면 크기로 확대합니다."""
    T = grid.shape[0]
    ft = t * T
    i0 = int(math.floor(ft)) % T
    f = ft - math.floor(ft)
    f = f * f * (3 - 2 * f)
    slab = grid[i0] * (1 - f) + grid[(i0 + 1) % T] * f
    img = Image.fromarray(((slab + 1) * 127.5).astype(np.uint8))
    return np.asarray(img.resize((SIZE, SIZE), Image.BICUBIC), np.float32) / 127.5 - 1.0


def turbulence(t):
    v = np.zeros((SIZE, SIZE), np.float32)
    for grid, amp in zip(noise_grids, NOISE_AMP):
        v += amp * sample_grid(grid, t)
    return v


def colorize(heat):
    h = np.clip(heat, 0, 1.6)
    r = np.clip(h * 2.4, 0, 1)
    g = np.clip((h - 0.20) * 1.7, 0, 1)
    b = np.clip((h - 0.80) * 2.2, 0, 1)
    return np.stack([r, g, b], -1) * 255.0


def frame(i):
    t = i / N

    # 1) 이미 타고 있는 영역을 난류로 일렁이게 — 불덩이가 끓어 보이는 핵심
    turb = turbulence(t)
    boil = 1.0 + 0.55 * turb * fire_region

    # 2) 한 번씩 부풀었다 꺼지는 전체 맥동
    pulse = 0.5 - 0.5 * math.cos(2 * math.pi * t)
    inset = int(round(2 + 5 * pulse))
    w, hgt = base_src.size
    b = base_src.crop((inset, inset, w - inset, hgt - inset)).resize((SIZE, SIZE), Image.LANCZOS)
    base = np.asarray(b, np.float32)

    out = base * boil[..., None] * (1.0 + 0.07 * pulse)

    # 3) 불티와 불꽃 혀를 더합니다
    heat = np.zeros((SIZE, SIZE), np.float32)
    for k in range(K):
        f = (t + e_off[k]) % 1.0
        life = math.sin(math.pi * f) ** 1.5          # 떠오르며 나타났다 사라짐
        ey = e_y[k] - e_rise[k] * f
        ex = e_x[k] + e_sway[k] * math.sin(2 * math.pi * (t + e_off[k]) * 2)
        heat += 1.7 * life * np.exp(-(((xx - ex) ** 2 + (yy - ey) ** 2) / (e_size[k] ** 2)))
    for k in range(L):
        f = (t + l_off[k]) % 1.0
        life = math.sin(math.pi * f)
        ly = l_y[k] - l_rise[k] * f
        sz = l_size[k] * (0.6 + 0.7 * f)
        heat += 0.85 * life * np.exp(-(((xx - l_x[k]) ** 2 + ((yy - ly) * 1.5) ** 2) / (sz * sz)))

    out = out + colorize(heat) * cat_mask[..., None] * 0.9
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    frames = [frame(i) for i in range(N)]
    for i, f in enumerate(frames):
        f.save(os.path.join(out_dir, "explosion_%02d.jpg" % i), quality=80, optimize=True)
    sheet = Image.new("RGB", (SIZE // 4 * 8, SIZE // 4 * 2))
    for i, f in enumerate(frames):
        sheet.paste(f.resize((SIZE // 4, SIZE // 4)), (SIZE // 4 * (i % 8), SIZE // 4 * (i // 8)))
    sheet.save(os.path.join(out_dir, "_contact_sheet.png"))
    total = sum(os.path.getsize(os.path.join(out_dir, "explosion_%02d.jpg" % i)) for i in range(N))
    print("frames:", len(frames), "total:", total // 1024, "KB")
