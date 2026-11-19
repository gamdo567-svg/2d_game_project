"""지하 미궁 맵 바탕 그림 만들기.

2026-11-19 사용자 요청: 첫 스테이지는 지하 미궁, 낡은 돌 미궁, 벽은 비스듬히(3/4) 보이게.
같은 날 ① 푸른 회색 돌(tiles_v1)은 하수도 느낌 → 따뜻한 색(tiles_v2) + 횃불 빛.
② "분위기는 괜찮은데 퀄리티가 떨어짐" (바닥 반복·단조로움, 빛이 뿌옇고 탁함, 벽이 납작함, 장식 없음) →
   바닥은 PixelLab Wang 타일셋(큰 판석 ↔ 모래·부스러기, floor_wang)을 노이즈로 섞어 격자·반복이 안 보이게,
   빛은 (처음엔 단계로 끊었다가 같은 날 '어설프다'는 지적에) 횃불에서 부드럽게 퍼지게, 벽은 윗면 턱 하이라이트·앞면 위 그늘·모서리 그늘,
   소품은 PixelLab 그림(props): 막는 소품은 맵 글자(B 통, C 상자, I 기둥), 밟고 지나가는 해골·돌무더기·항아리는 자동으로 드문드문.

글자 맵(assets/maps/<이름>.txt)을 읽어 맵 크기의 그림 한 장으로 합친다. 게임은 이 그림을 바닥에 한 번 그린다
(게임에는 PIL 이 필요 없음). 맵 글자를 바꾸면 이 스크립트를 다시 돌린다.
그림은 충돌 칸과 정확히 겹친다: 벽은 칸 안에서만 그리고, 바닥 Wang 타일은 바닥끼리만 이어지므로 칸에 맞춰 놓는다.
출력: assets/images/maps/<이름>_bg.png (맵 칸 수 × 32 픽셀), 미리보기 preview_<이름>_x2.png
"""
import json
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
TILES = os.path.join(HERE, 'tiles_v2')
WANG = os.path.join(HERE, 'floor_wang')
PROPS_DIR = os.path.join(HERE, 'props')
TORCH = os.path.join(HERE, 'torch_v1.png')
TORCH_ANIM = os.path.join(HERE, 'torch_anim')  # PixelLab animate_image: 0 = 원본, 1~8 = 불꽃이 일렁이는 고리 (같은 날)
TORCH_FRAMES = 8
GLOW_RADIUS = 2.6 * 32  # 게임이 횃불 위에 겹쳐 그리는 빛 고리 반지름 (원본 픽셀)
GLOW_ALPHA = 78  # 게임이 겹쳐 그리는 빛 가운데 알파 (바깥으로 부드럽게 0)
GLOW_COLOR = (255, 186, 104)
T = 32
FACE_TOP = 6  # 앞에서 보이는 벽에서 윗면이 차지하는 줄 수 (나머지는 벽돌 앞면)
# 솟은 벽 윗면 (같은 날 사용자: 한 칸 두께 벽은 윗면이 안 보임): 위가 바닥인 벽 칸은 윗면이 위 칸으로 OVERHANG 줄 솟는다.
# 그 부분은 바탕 그림이 아니라 따로 '<이름>_walltop.png'(줄마다 OVERHANG 높이 띠)로 내보내, 게임이 인물과 줄 순서대로 그린다
# (벽 뒤 칸에 선 인물의 발이 벽 윗면에 가려짐). 값은 game/config.py MAP_WALL_OVERHANG 과 같아야 한다.
OVERHANG = 12
BLOCKING = {'B': 'barrel', 'C': 'crates', 'I': 'pillar'}  # game/world/tile_map.py PROPS 와 같음
DECALS = [('bones', 2), ('rubble', 3), ('pots', 2)]  # 밟고 지나가는 소품 (그림, 비중)
DECAL_CHANCE = 0.025  # 바닥 칸마다 소품이 놓일 확률 (칸 좌표로 정해져 늘 같음)
SAND_SHARE = 0.16  # 바닥에서 모래·부스러기 구역의 대략 비율
SAND_NEAR_WALL = 0.18  # 벽 가까이는 모래가 더 쌓임 (꼭짓점 노이즈에 더함)

# tiles_v2 번호 (0 부터): 벽 윗면 8·9, 벽돌 앞면 10~13·15
WALL_TOP = [(8, 3), (9, 1)]
WALL_FACE = [(10, 10), (11, 3), (13, 3), (12, 1), (15, 1)]  # 15 = 빈 벽감, 12 = 쇠창살 환기구 (드물게)
GREY_TO_BROWN = {(0x3a, 0x3a, 0x40): (0x35, 0x25, 0x1b), (0x55, 0x55, 0x5c): (0x5a, 0x41, 0x30),
                 (0x76, 0x76, 0x7c): (0x6e, 0x52, 0x3c)}  # 팔레트의 회색 → 갈색 (하수도 느낌 빼기)
RIM = (10, 7, 6, 255)
LEDGE = (0x83, 0x65, 0x4a, 255)  # 벽 윗면 앞 턱 하이라이트
WALL_FACE_DARK = 0.8  # 벽 앞면은 바닥보다 어둡게
TORCH_EVERY = 6  # 앞에서 보이는 벽 줄에서 몇 칸마다 횃불
TORCH_SCALE = 0.62
TORCH_RADIUS = 4.5 * T  # 빛이 닿는 거리 (픽셀)
LIGHT_MIN, LIGHT_MAX = 0.36, 1.25  # 빛이 닿지 않는 곳 / 횃불 바로 앞 밝기 (사이는 부드럽게)
WARM = (1.08, 0.92, 0.72)  # 횃불 빛 색 (빨강·초록·파랑 배율), 밝은 단계일수록 강하게


def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def lum_mean(im):
    px = [p for p in im.get_flattened_data() if p[3]]
    return sum(lum(p) for p in px) / len(px)


def scale(img, box, factor):
    """box 안 픽셀 밝기를 factor 배로."""
    px = img.load()
    x0, y0, x1, y1 = box
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            r, g, b, a = px[x, y]
            px[x, y] = (min(255, round(r * factor)), min(255, round(g * factor)), min(255, round(b * factor)), a)


def recolor(tile):
    out = tile.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = px[x, y]
            if c[:3] in GREY_TO_BROWN:
                px[x, y] = GREY_TO_BROWN[c[:3]] + (c[3],)
    return out


def hash01(a, b, salt):
    h = (a * 73856093) ^ (b * 19349663) ^ (salt * 83492791)
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return (h & 0xFFFF) / 0xFFFF


def pick(choices, col, row, salt):
    """칸 좌표로 정해지는 고르기 (무작위처럼 보이지만 늘 같음)."""
    total = sum(w for _, w in choices)
    r = hash01(col, row, salt) * total
    for idx, w in choices:
        if r < w:
            return idx
        r -= w
    return choices[-1][0]


def value_noise(x, y, cell, salt):
    """부드러운 값 노이즈 0~1 (cell 칸마다 무작위 값, 사이는 부드럽게 이음)."""
    gx, gy = x / cell, y / cell
    x0, y0 = math.floor(gx), math.floor(gy)
    fx, fy = gx - x0, gy - y0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    v = [[hash01(x0 + i, y0 + j, salt) for i in (0, 1)] for j in (0, 1)]
    top = v[0][0] + (v[0][1] - v[0][0]) * sx
    bot = v[1][0] + (v[1][1] - v[1][0]) * sx
    return top + (bot - top) * sy


def load_wang():
    sheet = Image.open(os.path.join(WANG, 'sheet.png')).convert('RGBA')
    meta = json.load(open(os.path.join(WANG, 'metadata.json'), encoding='utf-8'))
    tiles = meta['tileset_data']['tiles']
    out = {}
    for t in tiles:
        c, bb = t['corners'], t['bounding_box']
        key = tuple(c[k] == 'upper' for k in ('NW', 'NE', 'SW', 'SE'))
        out.setdefault(key, sheet.crop((bb['x'], bb['y'], bb['x'] + bb['width'], bb['y'] + bb['height'])))
    return out


def build(name):
    lines = [l.rstrip('\r\n') for l in open(os.path.join(ROOT, 'assets', 'maps', f'{name}.txt'), encoding='utf-8')
             if l.strip()]
    rows, cols = len(lines), len(lines[0])
    tiles = [recolor(Image.open(os.path.join(TILES, f'tile_{i}.png')).convert('RGBA')) for i in range(16)]
    face_base = lum_mean(tiles[WALL_FACE[0][0]])
    for i, _ in WALL_FACE:  # 벽 앞면 변형 밝기를 기본 벽돌에 맞춤 (벽감 타일이 밝은 베이지라 튀었음)
        scale(tiles[i], (0, 0, T, T), WALL_FACE_DARK * face_base / lum_mean(tiles[i]))
    wang = load_wang()
    props = {n: Image.open(os.path.join(PROPS_DIR, f'{n}.png')).convert('RGBA')
             for n in list(BLOCKING.values()) + [d for d, _ in DECALS]}
    props = {n: p.crop(p.getbbox()) for n, p in props.items()}

    def wall(c, r):  # r = 그림의 줄 (0 = 맨 위). 맵 밖은 벽으로 본다. 소품 칸은 바닥으로 그린다
        return not (0 <= c < cols and 0 <= r < rows) or lines[r][c] == '#'

    def front(c, r):
        return wall(c, r) and not wall(c, r + 1)

    # 바닥 꼭짓점 (cols+1 × rows+1): 노이즈 + 벽 가까이 가산 → 모래·부스러기 여부
    def near_wall(vx, vy):
        return any(wall(vx + dx, vy + dy) for dx in (-1, 0) for dy in (-1, 0))

    vals = {}
    for vy in range(rows + 1):
        for vx in range(cols + 1):
            n = 0.55 * value_noise(vx, vy, 3.0, 7) + 0.45 * value_noise(vx, vy, 1.3, 8)  # 잘게 섞어 네모난 덩어리를 깸
            vals[(vx, vy)] = n + (SAND_NEAR_WALL if near_wall(vx, vy) else 0)
    cut = sorted(vals.values())[int(len(vals) * (1 - SAND_SHARE))]
    sand = {k: v >= cut for k, v in vals.items()}

    img = Image.new('RGBA', (cols * T, rows * T), (0, 0, 0, 255))
    for r in range(rows):
        for c in range(cols):
            x, y = c * T, r * T
            if not wall(c, r):
                key = (sand[(c, r)], sand[(c + 1, r)], sand[(c, r + 1)], sand[(c + 1, r + 1)])
                img.alpha_composite(wang[key], (x, y))
            elif front(c, r):  # 아래가 바닥: 윗면 + 벽돌 앞면
                img.alpha_composite(tiles[pick(WALL_TOP, c, r, 2)].crop((0, 0, T, FACE_TOP)), (x, y))
                face = tiles[pick(WALL_FACE, c, r, 3)]
                img.alpha_composite(face.crop((0, 0, T, T - FACE_TOP)), (x, y + FACE_TOP))
                for k, f in enumerate((0.5, 0.65, 0.8)):  # 턱 아래 그늘
                    scale(img, (x, y + FACE_TOP + k, x + T, y + FACE_TOP + k + 1), f)
                scale(img, (x, y + T - 3, x + T, y + T), 0.7)  # 벽 밑동
            else:
                img.alpha_composite(tiles[pick(WALL_TOP, c, r, 2)], (x, y))
    px = img.load()
    for r in range(rows):  # 벽 윗면 테두리·턱 하이라이트, 앞면 양 끝 그늘
        for c in range(cols):
            if not wall(c, r):
                continue
            x, y = c * T, r * T
            if not wall(c, r - 1):
                for i in range(T):
                    px[x + i, y] = RIM
            for dc, xx, inner in ((-1, x, x + 1), (1, x + T - 1, x + T - 2)):
                if not wall(c + dc, r):
                    for j in range(T):
                        px[xx, y + j] = RIM
                    if front(c, r):  # 앞면 양 끝은 모서리라 어둡게
                        scale(img, (min(inner, xx), y + FACE_TOP, max(inner, xx) + 1, y + T), 0.7)
            if front(c, r):
                for i in range(T):
                    px[x + i, y + FACE_TOP - 2] = LEDGE  # 턱 위 하이라이트
                    px[x + i, y + FACE_TOP - 1] = RIM
    for r in range(rows):  # 바닥 그늘: 위가 벽이면 위쪽 6줄, 왼쪽·오른쪽이 벽이면 그쪽 3줄
        for c in range(cols):
            if wall(c, r):
                continue
            x, y = c * T, r * T
            if wall(c, r - 1):
                for k, f in enumerate((0.45, 0.55, 0.65, 0.75, 0.85, 0.92)):
                    scale(img, (x, y + k, x + T, y + k + 1), f)
            if wall(c - 1, r):
                for k, f in enumerate((0.6, 0.75, 0.88)):
                    scale(img, (x + k, y, x + k + 1, y + T), f)
            if wall(c + 1, r):
                for k, f in enumerate((0.6, 0.75, 0.88)):
                    scale(img, (x + T - 1 - k, y, x + T - k, y + T), f)

    # 소품: 막는 소품(맵 글자) + 밟고 지나가는 소품(드문드문). 아래 가운데를 칸 아래쪽에 맞춤, 바닥에 작은 그림자
    def place(prop, c, r, foot_pad):
        x = c * T + (T - prop.width) // 2
        y = r * T + T - foot_pad - prop.height
        shadow_w = max(6, prop.width - 6)
        sx = c * T + (T - shadow_w) // 2
        scale(img, (sx, r * T + T - foot_pad - 2, sx + shadow_w, r * T + T - foot_pad + 1), 0.6)
        img.alpha_composite(prop, (x, y))

    special = set()
    for r in range(rows):
        for c in range(cols):
            ch = lines[r][c]
            if ch in 'PDG':
                special |= {(c + dx, r + dy) for dx in (-1, 0, 1) for dy in (-2, -1, 0, 1)}
    for r in range(rows):
        for c in range(cols):
            ch = lines[r][c]
            if ch in BLOCKING:
                place(props[BLOCKING[ch]], c, r, 2)
            elif not wall(c, r) and ch == '.' and (c, r) not in special and hash01(c, r, 9) < DECAL_CHANCE:
                place(props[pick(DECALS, c, r, 10)], c, r, 6)

    # 횃불: 앞에서 보이는 벽 줄을 왼쪽부터 세어 TORCH_EVERY 칸마다 (짧은 줄은 가운데 하나)
    torches = []
    for r in range(rows):
        c = 0
        while c < cols:
            if not front(c, r):
                c += 1
                continue
            start = c
            while c < cols and front(c, r):
                c += 1
            run = list(range(start, c))
            if len(run) < TORCH_EVERY:
                if len(run) >= 2:
                    torches.append((run[len(run) // 2], r))
            else:
                torches += [(cc, r) for cc in run[TORCH_EVERY // 2::TORCH_EVERY]]
    # 횃불 그림은 바탕에 박지 않고 게임이 불꽃을 움직여 그린다 (같은 날 사용자: 다음 작업 = 횃불 일렁임).
    # 바탕의 빛 계산에 쓸 불꽃 자리만 구하고, 자리는 <이름>_torches.json 으로 내보낸다.
    frames = [Image.open(os.path.join(TORCH_ANIM, f'f{k}.png')).convert('RGBA') for k in range(1, TORCH_FRAMES + 1)]
    box = frames[0].getbbox()
    for f in frames[1:]:
        b = f.getbbox()
        box = (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    frames = [f.crop(box) for f in frames]
    tw, th = max(1, round(frames[0].width * TORCH_SCALE)), max(1, round(frames[0].height * TORCH_SCALE))
    frames = [f.resize((tw, th), Image.NEAREST) for f in frames]
    flames, torch_spots = [], []
    for c, r in torches:
        x = c * T + (T - tw) // 2
        y = r * T + T - 4 - th  # 밑동이 벽 밑에서 조금 위
        flames.append((x + tw / 2, y + th * 0.2))
        torch_spots.append({'x': x + tw / 2, 'bottom': y + th, 'flame_y': y + th * 0.2})

    # 솟은 벽 윗면 띠: 줄 i 의 띠 = 줄 i 벽 가운데 위가 바닥인 칸 위로 솟는 OVERHANG 줄 (바탕 그림 좌표로 i*T - OVERHANG ~ i*T)
    walltop = Image.new('RGBA', (cols * T, rows * OVERHANG), (0, 0, 0, 0))
    wpx = walltop.load()
    for r in range(rows):
        for c in range(cols):
            if not (wall(c, r) and not wall(c, r - 1)) or r == 0:
                continue
            x, by = c * T, r * OVERHANG
            src = tiles[pick(WALL_TOP, c, r - 1, 4)]
            walltop.alpha_composite(src.crop((0, T - OVERHANG, T, T)), (x, by))
            for i in range(T):
                wpx[x + i, by] = RIM
            for dc, xx in ((-1, x), (1, x + T - 1)):
                if not (wall(c + dc, r) and not wall(c + dc, r - 1)):  # 옆 칸은 솟지 않음 → 끝 테두리
                    for j in range(OVERHANG):
                        wpx[xx, by + j] = RIM
            # 바탕 그림의 윗면 맨 위 테두리를 지운 자리와 이어지게, 띠 맨 아래 한 줄은 윗면 색 그대로 둔다
        # (바탕 그림 쪽 맨 위 테두리는 아래에서 지움)
    for r in range(1, rows):
        for c in range(cols):
            if wall(c, r) and not wall(c, r - 1):
                src = tiles[pick(WALL_TOP, c, r - 1, 4)]
                img.alpha_composite(src.crop((0, 0, T, 1)), (c * T, r * T))  # 솟은 띠와 이어지게 칸 맨 위 테두리 지움
                for dc, xx in ((-1, c * T), (1, c * T + T - 1)):
                    if not wall(c + dc, r):
                        img.putpixel((xx, r * T), RIM)

    # 빛: 횃불에서 멀어질수록 부드럽게 어두워짐 (같은 날 사용자: 단계로 나뉜 빛이 어설픔 → 부드러운 빛).
    # 예전 '뿌옇다'는 지적을 피하려고 바깥은 충분히 어둡게(LIGHT_MIN), 밝을수록 따뜻한 색을 강하게 해 탁해 보이지 않게.
    lo, hi = LIGHT_MIN, LIGHT_MAX

    def lit(pix, x, y, mx, my):
        """(mx, my) = 바탕 그림 좌표에서의 자리 (빛 계산용), (x, y) = 이 그림에서의 자리."""
        glow = 0.0
        for fx, fy in flames:
            d = math.hypot(mx - fx, (my - fy) * 1.15)
            if d < TORCH_RADIUS:
                t = 1 - d / TORCH_RADIUS
                glow += t * t * (3 - 2 * t)  # 부드러운 끝 (smoothstep)
        glow = min(1.0, glow)
        lv = lo + (hi - lo) * glow
        tint = [1 + (w - 1) * glow for w in WARM]
        r_, g_, b_, a_ = pix[x, y]
        pix[x, y] = (min(255, round(r_ * lv * tint[0])), min(255, round(g_ * lv * tint[1])),
                     min(255, round(b_ * lv * tint[2])), a_)

    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            lit(px, x, y, x, y)
    for y in range(walltop.height):
        r, j = divmod(y, OVERHANG)
        for x in range(walltop.width):
            if wpx[x, y][3]:
                lit(wpx, x, y, x, r * T - OVERHANG + j)
    out_dir = os.path.join(ROOT, 'assets', 'images', 'maps')
    os.makedirs(out_dir, exist_ok=True)
    img.save(os.path.join(out_dir, f'{name}_bg.png'))
    walltop.save(os.path.join(out_dir, f'{name}_walltop.png'))
    # 횃불 그림 (가로 TORCH_FRAMES 장)·빛 고리·자리 (원본 픽셀, y 는 맵 그림 위에서부터)
    sheet = Image.new('RGBA', (tw * TORCH_FRAMES, th), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        sheet.alpha_composite(f, (k * tw, 0))
    sheet.save(os.path.join(out_dir, 'torch.png'))
    g = round(GLOW_RADIUS)
    glow = Image.new('RGBA', (2 * g, 2 * g), (0, 0, 0, 0))
    gpx = glow.load()
    for y in range(2 * g):
        for x in range(2 * g):
            d = math.hypot(x + 0.5 - g, (y + 0.5 - g) * 1.15) / g
            a = round(GLOW_ALPHA * max(0.0, 1 - d) ** 2) if d < 1 else 0
            if a:
                gpx[x, y] = GLOW_COLOR + (min(255, a),)
    glow.save(os.path.join(out_dir, 'torch_glow.png'))
    with open(os.path.join(out_dir, f'{name}_torches.json'), 'w', encoding='utf-8') as fp:
        json.dump({'frame_width': tw, 'frame_height': th, 'frames': TORCH_FRAMES, 'torches': torch_spots}, fp, indent=1)
    # 미리보기: 솟은 띠까지 얹은 모습
    for r in range(rows):
        band = walltop.crop((0, r * OVERHANG, cols * T, (r + 1) * OVERHANG))
        if r > 0:
            img.alpha_composite(band, (0, r * T - OVERHANG))
    for spot in torch_spots:  # 미리보기에만 횃불 첫 장
        img.alpha_composite(frames[0], (round(spot['x'] - tw / 2), round(spot['bottom'] - th)))
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(os.path.join(HERE, f'preview_{name}_x2.png'))
    return img, torches


if __name__ == '__main__':
    for n in sys.argv[1:] or ['test_room']:
        _, t = build(n)
        print('ok', n, 'torches', len(t))
