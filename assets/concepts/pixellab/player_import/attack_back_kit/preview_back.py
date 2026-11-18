"""후면 공격 미리보기: 위 줄 = ChatGPT 원본(게임 크기), 아래 줄 = 게임처럼 칼을 겹친 그림. 타마다 두 줄."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image  # noqa: E402

import build_remake_preview as b  # noqa: E402

BG = (128, 128, 128, 255)
rows = []
for r in range(3):
    frames = b.cells('attack_back_gpt_68.png', r)
    layers, _, _ = b.build_layers(f'backgpt{r + 1}', frames[1:])
    raw = [f for f in frames[1:]]
    comp = [b.compose(l, pad=0) for l in layers]
    for line in (raw, comp):
        row = Image.new('RGBA', (68 * 8, 68), BG)
        for i, f in enumerate(line):
            row.alpha_composite(f.crop((0, 0, 68, 68)), (i * 68, 0))
        rows.append(row)
out = Image.new('RGBA', (68 * 8, 68 * len(rows)), BG)
for i, row in enumerate(rows):
    out.alpha_composite(row, (0, i * 68))
out.resize((out.width * 3, out.height * 3), Image.NEAREST).save(os.path.join(HERE, 'attack_back_compare_x3.png'))
print('ok')
