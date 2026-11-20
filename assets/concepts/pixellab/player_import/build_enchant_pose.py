"""검 속성 입히기 자세 시트 (측면) 만들기 (2026-11-20 사용자: 자세 그림 작업 시작 → 핵심 자세 이미지 좋음).

PixelLab: 주인공 캐릭터에 `Enchant Hold` 상태(두 손으로 칼을 곧게 세워 얼굴 앞에, 칼은 파란 단색, 4방향)를 만들고,
서 있는 측면 → 그 자세 사이를 pixminimax 4장으로 그렸다 (concepts/pixellab/enchant_pose/side_raise_v1/f0~f4, f0 = 시작 그림).
장 순서 (6장): 손을 꺼냄(f1) → 칼을 허리 앞에 잡음(f2) → 비스듬히 들어 올림(f3) → 곧게 세움(Enchant Hold, 이펙트가 차오르는 동안)
→ 내리며 비스듬히(f3) → 허리 앞(f2).
PixelLab 이 몸을 조금 다른 색으로 칠해 파란 칼을 뺀 몸 픽셀을 게임 주인공 색 중 가장 가까운 색으로 바꾼다 (패링 정면과 같음).
출력: remake_raw/enchant_side_sheet_68.png (칸 0 = 서 있는 측면, 1~6 = 위 순서). export_to_game.py 가 읽는다.
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
ORDER = ['side_raise_v1/f1.png', 'side_raise_v1/f2.png', 'side_raise_v1/f3.png', 'hold_east_64.png',
         'side_raise_v1/f3.png', 'side_raise_v1/f2.png']


def main():
    palette = pf.game_palette()
    frames = [Image.open(os.path.join(POSE, 'idle_east_64.png')).convert('RGBA')]
    frames += [pf.snap(Image.open(os.path.join(POSE, p)).convert('RGBA'), palette) for p in ORDER]
    sheet = Image.new('RGBA', (68 * len(frames), 68), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        sheet.alpha_composite(f, (k * 68 + OFFSET[0], OFFSET[1]))
    sheet.save(os.path.join(RAW, 'enchant_side_sheet_68.png'))
    print('enchant side', len(frames) - 1)


if __name__ == '__main__':
    main()
