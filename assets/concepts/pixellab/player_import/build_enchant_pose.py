"""검 속성 입히기 자세 시트 (측면·정면·후면) 만들기 (2026-11-20 사용자: 자세 그림 작업 시작 → 핵심 자세 이미지 좋음).

PixelLab: 주인공 캐릭터에 `Enchant Hold` 상태(두 손으로 칼을 곧게 세워 얼굴 앞에, 칼은 파란 단색, 4방향)를 만들고,
방향마다 서 있는 그림 → 그 자세 사이를 pixminimax 4장으로 그렸다 (concepts/pixellab/enchant_pose/<방향>_raise_v1/f0~f4,
f0 = 시작 그림). 장 순서 (7장): f1 → f2 → f3 → 곧게 세움(Enchant Hold, 이펙트가 차오르는 동안) → 털어내기 3장 (아래 VIEWS 설명).
측면: 손을 꺼냄 → 칼을 허리 앞에 → 비스듬히 → 곧게. 정면: 칼을 꺼내 비스듬히 → 더 세움 → 얼굴 앞에 곧게.
후면: 칼이 몸에 가려 칼끝만 후드 위로 솟음.
PixelLab 이 몸을 조금 다른 색으로 칠해 파란 칼을 뺀 몸 픽셀을 게임 주인공 색 중 가장 가까운 색으로 바꾼다 (패링 정면과 같음).
출력: remake_raw/enchant_<방향>_sheet_68.png (칸 0 = 서 있는 그림, 1~7 = 위 순서). export_to_game.py 가 읽는다.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_parry_front as pf  # noqa: E402

POSE = os.path.normpath(os.path.join(HERE, '..', 'enchant_pose'))
RAW = os.path.join(HERE, 'remake_raw')
OFFSET = (1, 3)  # 64 그림을 68 칸에 놓는 자리 (발이 패링 시트와 같은 줄 58 에)
VIEWS = {'side': ('east', 'side_raise_v1'), 'front': ('south', 'south_raise_v1'), 'back': ('north', 'north_raise_v1')}
# 마지막 털어내기 (같은 날 사용자: 1타 재탕은 베는 느낌, 원한 건 검을 한번 털어내는 느낌): PixelLab `Enchant Flick End`
# (칼을 몸 옆 아래로 비스듬히, 4방향) 상태를 만들고, 곧게 세운 자세 → 그 자세를 pixminimax 4장으로 (<방향>_flick_v2).
# 1차(flick_v1)는 "피를 털어내듯" 이라고 써서 PixelLab 이 빨간 피를 그려 버림 → 그 말을 빼고 다시.
# 장 순서 (7장): 들어 올림 f1~f3 → 곧게 세움 → 확 털어 내림(크게 휘두른 잔상) → 내려온 장 → 털어낸 끝 자세


def order(direction, folder):
    return [f'{folder}/f1.png', f'{folder}/f2.png', f'{folder}/f3.png', f'hold_{direction}_64.png',
            f'{direction}_flick_v2/f1.png', f'{direction}_flick_v2/f2.png', f'flick_{direction}_64.png']


def main():
    palette = pf.game_palette()
    for view, (direction, folder) in VIEWS.items():
        frames = [Image.open(os.path.join(POSE, f'idle_{direction}_64.png')).convert('RGBA')]
        frames += [pf.snap(Image.open(os.path.join(POSE, p)).convert('RGBA'), palette) for p in order(direction, folder)]
        sheet = Image.new('RGBA', (68 * len(frames), 68), (0, 0, 0, 0))
        for k, f in enumerate(frames):
            sheet.alpha_composite(f, (k * 68 + OFFSET[0], OFFSET[1]))
        sheet.save(os.path.join(RAW, f'enchant_{view}_sheet_68.png'))
        print('enchant', view, len(frames) - 1)


if __name__ == '__main__':
    main()
