"""PixelLab 으로 새로 만든 주인공 그림(remake_raw)을 게임 그림으로 내보낸다 (2026-11-17).

- 측면 공격 1·2·3타: build_remake_preview.build_layers 의 레이어(잔상+몸 / 손)를 96×64 캔버스 8프레임 시트로.
  칼 위치표(손 x, 손 y, 각도, 몸 뒤)는 config.PLAYER_ATTACK_SWORD 에 붙여 넣을 값으로 출력한다.
- 걷기: 게임은 예전 걷기 그림을 쓴다 (2026-11-17 사용자 결정). export_walk() 는 PixelLab 걷기 템플릿을 시험할 때만 쓰며
  main() 에서 부르지 않는다.
- 점프 3방향(정면·측면·후면): PixelLab 점프에서 재생 순서대로 10장을 48×56 으로 자른다. 왼쪽은 게임이 측면을 뒤집는다.
  높이는 게임 코드가 띄우므로, 그림 안에서 떠오른 만큼은 머리 높이를 기준 자세에 맞춰 줄인다.
Pillow 필요 (게임 실행에는 필요 없음).
사용: 저장소 루트에서 `python assets/concepts/pixellab/player_import/export_to_game.py`
"""
import os
import sys
from collections import Counter

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_remake_preview as b  # noqa: E402

ROOT = b.ROOT
OUT = os.path.join(ROOT, 'assets', 'images', 'player')
CELL = b.CELL
SPRITE_W, SPRITE_H = 32, 48
ATTACK_W, ATTACK_H = 96, 64
ATTACK_FOOT_ROW = ATTACK_H - 8 - 1  # config.PLAYER_ATTACK_FOOT_MARGIN = 8

# 점프: 방향별 PixelLab 원본과 쓰는 순서 (2026-11-17 사용자 결정, 여러 번 다시 그린 끝에 확정).
# 정면 = jump_v7 정면, 측면 = jump_v19 (측면 전체를 한 번에 그림), 후면 = jump_v14 후면.
# 왼쪽은 측면을 좌우 반전한다 (후드를 잡지 않아 좌우 대칭). 그림 픽셀은 고치지 않는다.
# 재생 순서 10장: 웅크림, 깊게 웅크림, 도약, 공중 ×4, 다리 폄, 착지(깊게 웅크림), 일어섬.
# 정면·후면은 착지 그림이 없어 도약 전 웅크림 그림(2 → 1)을 거꾸로 쓴다.
# 측면은 정면과 같은 순간에 뜨고 내리도록 프레임을 골랐다 (3번 = 땅 위 펴기는 건너뜀, 7번을 한 번 더).
JUMP_SOURCES = {
    'front': ('jump_v7_sheet_68.png', 0, [1, 2, 3, 4, 5, 6, 7, 8, 2, 1]),
    'side': ('jump_v19_side_full_sheet_68.png', 0, [1, 2, 4, 5, 6, 7, 7, 8, 10, 11]),
    'back': ('jump_v14_side_back_sheet_68.png', 1, [1, 2, 3, 4, 5, 6, 7, 8, 2, 1]),
}
# 높이 기준: 공중 프레임은 이 방향의 머리를 기준 자세 높이까지 내린 만큼 모든 방향을 똑같이 내린다
# (떠오르는 높이는 게임 코드가 그린다). 측면은 다리를 덜 접어 낮아 보여서, 공중에서는 몸 중심을 정면에 맞춘다.
JUMP_HEIGHT_REF = 'front'
JUMP_LEVEL_TO_REF = {'side'}
WALK_ROWS = {'front': 0, 'side': 1, 'back': 2}  # south, east, north (왼쪽은 측면을 뒤집는다)


def ref_anchor(frame):
    """기준(서 있는) 자세의 발 아래 가운데: (가운데 x, 발끝 줄 y)."""
    x0, y0, x1, y1 = frame.getchannel('A').getbbox()
    return (x0 + x1) // 2, y1 - 1, y0


# 방향별 공격 (2026-11-17): 방향 → [(타 번호, 이름, 시트, 행)]. 목록에 없는 타는 게임이 예전 그림이나 측면을 쓴다.
VIEW_ATTACKS = {
    'side': [(hit, name, path, row) for hit, (name, path, row) in enumerate(b.ATTACKS, start=1)],
    # 정면 1·2·3타 PixelLab (2타 v9, 3타 찌르기는 끝 자세 지정, attack_front_final_68.png 2·3행). 후면은 보류 (2026-11-17 사용자 결정).
    'front': [(1, 'front1', 'attack_front_final_68.png', 0), (2, 'front2', 'attack_front_final_68.png', 1),
              (3, 'front3', 'attack_front_final_68.png', 2)],
    # 후면은 ChatGPT 8자세 (2026-11-18, build_attack_back.py 가 시트를 만든다)
    # 1타는 2차: PixelLab 이 GPT 자세 사이를 다시 그림 (build_attack_back_pl.py, 2026-11-18 사용자 요청)
    # 1타 3차 (같은 날): ChatGPT 가 정면 8장을 뒤에서 본 모습으로 그림 (build_attack_back_v2.py)
    # 2·3타 2차 (같은 날): 1타와 같은 방법 (build_attack_back_v3.py)
    'back': [(1, 'backv2_1', 'attack_back_v2_68.png', 0), (2, 'backv3_2', 'attack_back_v3_68.png', 0),
             (3, 'backv3_3', 'attack_back_v3_68.png', 1)],
}


# 정면 3타 찌르기는 칼끝이 발 아래 13픽셀까지 내려와 6픽셀 올려 담는다 (2026-11-17)
RAISE = {'front3': 6}


# 패링 (2026-11-17 사용자 요청: 측면 먼저): 방향 → (이름, 시트, 행). 공격과 같은 칸(96×64)·칼 분리.
VIEW_PARRY = {'side': ('parry_side', 'parry_side_sheet_68.png', 0),
              # 정면은 측면을 기준으로 다시 그린 C안 (2026-11-18, build_parry_front.py 가 시트를 만든다)
              'front': ('parry_front', 'parry_front_sheet_68.png', 0),
              # 후면은 핵심 자세를 ChatGPT 로 그림 (2026-11-18, build_parry_back.py 가 시트를 만든다)
              'back': ('parry_back', 'parry_back_sheet_68.png', 0)}


# 검 속성 입히기 자세 (2026-11-20, build_enchant_pose.py): 두 손으로 칼을 곧게 세움.
VIEW_ENCHANT = {'side': ('enchant_side', 'enchant_side_sheet_68.png', 0),
                'front': ('enchant_front', 'enchant_front_sheet_68.png', 0),
                'back': ('enchant_back', 'enchant_back_sheet_68.png', 0)}


def export_parry(views=None, folder='parry', count=6):
    """패링 시트(player/parry/<방향>.png, _hand.png)를 내보내고 칼 위치표 {방향: [...]} 를 돌려준다.
    views·folder·count 를 바꾸면 같은 방식으로 다른 자세(검 속성 입히기 등)를 내보낸다."""
    tables = {}
    os.makedirs(os.path.join(OUT, folder), exist_ok=True)
    for view, (name, path, row) in (views or VIEW_PARRY).items():
        frames = b.cells(path, row, count=count)
        cx, foot, _ = ref_anchor(frames[0])
        dx, dy = ATTACK_W // 2 - cx, ATTACK_FOOT_ROW - foot
        layers, _, _ = b.build_layers(name, frames[1:])
        body = Image.new('RGBA', (ATTACK_W * len(layers), ATTACK_H), (0, 0, 0, 0))
        hand = Image.new('RGBA', body.size, (0, 0, 0, 0))
        table = []
        for i, layer in enumerate(layers):
            body.alpha_composite(layer['body'].crop(_src_box(dx, dy)), _dst(i, dx, dy))
            hand.alpha_composite(layer['hand'].crop(_src_box(dx, dy)), _dst(i, dx, dy))
            hx, hy, angle, behind, *rest = layer['sword']
            table.append((round(hx + dx), round(hy + dy), round(angle), behind) + tuple(rest))
        body.save(os.path.join(OUT, folder, f'{view}.png'))
        hand.save(os.path.join(OUT, folder, f'{view}_hand.png'))
        tables[view] = table
    return tables


def export_attacks(view='side'):
    """view 방향의 공격 시트를 내보내고 칼 위치표 {타 번호: [(손 x, 손 y, 각도, 몸 뒤), ...]} 를 돌려준다."""
    tables = {}
    for hit, name, path, row in VIEW_ATTACKS[view]:
        frames = b.cells(path, row)
        cx, foot, _ = ref_anchor(frames[0])
        # RAISE: 발끝 아래로 길게 내민 칼이 잘리지 않게 그림을 위로 올린다 (게임은 PLAYER_ATTACK_FRAME_SHIFTS_FRONT 로 되돌림)
        dx, dy = ATTACK_W // 2 - cx, ATTACK_FOOT_ROW - foot - RAISE.get(name, 0)
        layers, _, _ = b.build_layers(name, frames[1:])
        body = Image.new('RGBA', (ATTACK_W * len(layers), ATTACK_H), (0, 0, 0, 0))
        hand = Image.new('RGBA', body.size, (0, 0, 0, 0))
        art = Image.new('RGBA', body.size, (0, 0, 0, 0))
        art_frames = []
        table = []
        for i, layer in enumerate(layers):
            body.alpha_composite(layer['body'].crop(_src_box(dx, dy)), _dst(i, dx, dy))
            hand.alpha_composite(layer['hand'].crop(_src_box(dx, dy)), _dst(i, dx, dy))
            if layer.get('art') is not None:
                art.alpha_composite(layer['art'].crop(_src_box(dx, dy)), _dst(i, dx, dy))
                art_frames.append(i)
            hx, hy, angle, behind, *rest = layer['sword']
            table.append((round(hx + dx), round(hy + dy), round(angle), behind) + tuple(rest))
        body.save(os.path.join(OUT, 'sword_attack', f'{view}_{hit}.png'))
        if view == 'back':
            # 후면은 장마다 따로 그려 후드가 꿈틀거림 → 서기 그림 후드로 바꿔 끼움 (2026-11-19, stabilize_back.py)
            import stabilize_back
            stabilize_back.apply_sheet(os.path.join(OUT, 'sword_attack', f'{view}_{hit}.png'))
        hand.save(os.path.join(OUT, 'sword_attack', f'{view}_{hit}_hand.png'))
        if art_frames:
            # 찌르기용 칼 그림 (무기마다 하나, 공격 시트와 같은 칸): weapons/<무기>_<방향>_<타>.png
            art.save(os.path.join(OUT, 'weapons', f'old_sword_{view}_{hit}.png'))
            print(f'# 찌르기용 칼 그림 {view} {hit}타 프레임 {tuple(art_frames)}')
        tables[hit] = table
    return tables


def _src_box(dx, dy):
    """68 칸에서 96×64 캔버스 안에 들어오는 부분."""
    return (max(0, -dx), max(0, -dy), min(CELL, ATTACK_W - dx), min(CELL, ATTACK_H - dy))


def _dst(i, dx, dy):
    return (i * ATTACK_W + max(0, dx), max(0, dy))


def clean_white(img):
    """걷기 템플릿에 섞인 흰 점(작은 덩어리)을 둘레 색으로 바꾼다."""
    px = img.load()
    w, h = img.size
    white = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] and min(px[x, y][:3]) > 170]
    for comp in b.components(white):
        if len(comp) > 6:
            continue
        for x, y in comp:
            near = [px[x + ex, y + ey] for ex in (-1, 0, 1) for ey in (-1, 0, 1)
                    if (ex or ey) and 0 <= x + ex < w and 0 <= y + ey < h and px[x + ex, y + ey][3]
                    and min(px[x + ex, y + ey][:3]) <= 170]
            px[x, y] = Counter(near).most_common(1)[0][0] if near else (0, 0, 0, 0)


def export_walk():
    sheet = Image.open(os.path.join(b.RAW, 'walk_sheet_32x48.png')).convert('RGBA')
    for view, row in WALK_ROWS.items():
        frames = [sheet.crop((c * SPRITE_W, row * SPRITE_H, (c + 1) * SPRITE_W, (row + 1) * SPRITE_H))
                  for c in range(8)]
        lowest = max(f.getchannel('A').getbbox()[3] for f in frames)
        shift = SPRITE_H - lowest  # 발끝을 맨 아래 줄로 (서 있는 그림과 같게)
        out = Image.new('RGBA', (SPRITE_W * 8, SPRITE_H), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            clean_white(f)
            out.alpha_composite(f.crop((0, 0, SPRITE_W, SPRITE_H - shift)), (i * SPRITE_W, shift))
        out.save(os.path.join(OUT, 'walk', f'{view}.png'))


JUMP_W = 48  # 점프 그림은 펄럭이는 망토가 잘리지 않게 가로 48 (config.PLAYER_JUMP_SPRITE_WIDTH)
JUMP_H = 56  # 공중에서 머리가 잘리지 않게 세로 56 (config.PLAYER_JUMP_SPRITE_HEIGHT)


def feet_center(frame):
    """발(맨 아래 8줄의 어두운 픽셀)의 가로 가운데. 망토 끝(밝은 갈색)은 빼고 다리·부츠만 본다."""
    x0, y0, x1, y1 = frame.getchannel('A').getbbox()
    xs = [x for y in range(max(y0, y1 - 8), y1) for x in range(x0, x1)
          if frame.getpixel((x, y))[3] and max(frame.getpixel((x, y))[:3]) < 80]
    return round(sum(xs) / len(xs)) if xs else (x0 + x1) // 2


GLOVE = (0x5c, 0x37, 0x36, 255)  # 서 있는 그림의 장갑(어두운 가죽) 색
GLOVE_LIGHT = (0x62, 0x3d, 0x3b, 255)


def is_skin(c):
    return c[3] and c[0] >= 140 and c[0] > c[1] > c[2]


def glove_hands(frame):
    """맨손(피부색)을 장갑 색으로. 얼굴(가장 위에 있는 피부 덩어리)은 그대로 둔다.

    PixelLab 점프가 장갑 낀 손을 맨손으로 그려서 (2026-11-17 사용자 지적).
    """
    frame = frame.copy()
    px = frame.load()
    skin = [(x, y) for y in range(frame.height) for x in range(frame.width) if is_skin(px[x, y])]
    comps = b.components(skin)
    if not comps:
        return frame
    face = min(comps, key=lambda comp: min(y for _, y in comp))
    for comp in comps:
        if comp is face:
            continue
        for p in comp:
            px[p] = GLOVE_LIGHT if px[p][0] >= 180 else GLOVE
    return frame


def _cells(sheet_name, row):
    sheet = Image.open(os.path.join(b.RAW, sheet_name)).convert('RGBA')
    return [sheet.crop((c * CELL, row * CELL, (c + 1) * CELL, (row + 1) * CELL)) for c in range(sheet.width // CELL)]


def _bbox(frame):
    return frame.getchannel('A').getbbox()


def jump_frames():
    """방향별 점프 그림 (48×56). {view: [Image, ...]}

    서 있는 기준 그림(0번)의 발 아래 가운데에 맞춰 모든 프레임을 같은 자리에서 자른다 (그림 속 위치 그대로).
    공중 프레임의 위아래 위치는 JUMP_HEIGHT_REF 방향 기준으로 모든 방향을 똑같이 옮기고,
    JUMP_LEVEL_TO_REF 방향은 몸 중심 높이를 기준 방향에 맞춘다.
    """
    ref_sheet, ref_row, ref_picks = JUMP_SOURCES[JUMP_HEIGHT_REF]
    ref_cells = _cells(ref_sheet, ref_row)
    _, ref_top, _, _ = _bbox(ref_cells[0])
    ref_foot = _bbox(ref_cells[0])[3] - 1
    lifts, centers = [], []
    for c in ref_picks:
        _, y0, _, y1 = _bbox(ref_cells[c])
        airborne = y1 - 1 < ref_foot
        lifts.append(max(0, ref_top - y0) if airborne else 0)
        centers.append(((y0 + y1) / 2, airborne))
    result = {}
    for view, (sheet_name, row, picks) in JUMP_SOURCES.items():
        cells = _cells(sheet_name, row)
        cx, foot, _ = ref_anchor(cells[0])
        left, bottom = cx - JUMP_W // 2, foot + 1
        result[view] = []
        for i, c in enumerate(picks):
            f = cells[c]
            _, y0, _, y1 = _bbox(f)
            shift = lifts[i]  # 아래로 (+)
            ref_center, ref_air = centers[i]
            if view in JUMP_LEVEL_TO_REF and (ref_air or y1 - 1 < foot):
                shift -= round((y0 + y1) / 2 - ref_center)  # 몸 중심을 기준 방향에 맞춤 (위로 -)
            top_row = bottom - JUMP_H - shift
            result[view].append(f.crop((left, top_row, left + JUMP_W, top_row + JUMP_H)))
    return result


def export_jump():
    for view, frames in jump_frames().items():
        out = Image.new('RGBA', (JUMP_W * len(frames), JUMP_H), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            out.alpha_composite(f, (i * JUMP_W, 0))
        out.save(os.path.join(OUT, 'jump', f'{view}.png'))


def main():
    for view, const in (('side', 'PLAYER_ATTACK_SWORD'), ('front', 'PLAYER_ATTACK_SWORD_FRONT'),
                        ('back', 'PLAYER_ATTACK_SWORD_BACK')):
        tables = export_attacks(view)
        print(f'{const} = (')
        for hit in range(1, 4):
            t = tables.get(hit)
            if t is None:
                print('    None,')
                continue
            rows = ['(' + ', '.join(str(v) for v in e) + ')' for e in t]
            print('    (' + ', '.join(rows[:4]) + ',' + chr(10) + '     ' + ', '.join(rows[4:]) + '),')
        print(')')
    for view, t in export_parry().items():
        print(f'PLAYER_PARRY_SWORD[{view!r}] = (' + ', '.join('(' + ', '.join(str(v) for v in e) + ')' for e in t) + ')')
    for view, t in export_parry(VIEW_ENCHANT, 'enchant', 12).items():
        print(f'PLAYER_ENCHANT_SWORD[{view!r}] = (' + ', '.join('(' + ', '.join(str(v) for v in e) + ')' for e in t) + ')')
    export_jump()

if __name__ == '__main__':
    main()
