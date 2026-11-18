==================================================================
 주인공 후면 공격(1·2·3타) — 핵심 자세를 ChatGPT 로 그리기 (2026-11-18)
==================================================================

후면 = 위를 보고 공격 (보는 사람 반대쪽으로 벰). 지금은 그림이 없어 측면 그림을 임시로 씀.
측면과 같은 동작·박자: 1타 사선 내려베기, 2타 올려베기, 3타 찌르기.
칼은 측면·정면처럼 "파란 단색"으로 그려야 제가 칼만 떼어 게임의 칼 그림(바꿔 끼우기)으로 바꿀 수 있습니다.

[0] 이 폴더 파일
  ref_player_back_x12.png      게임 주인공 뒷모습 12배 (생김새·색 기준)
  ref_back_parry_x6.png        완성된 후면 패링 (뒷모습에서 칼이 몸에 가려지는 모습 참고)
  motion_guide_side_combo.png  완성된 측면 1·2·3타 (줄마다 한 타, 동작 순서 참고)

[1] 하는 법 (타마다 새 대화 하나, 모두 세 번)
  1. ChatGPT(이미지 생성) 새 대화를 엽니다.
  2. 세 그림(ref_player_back_x12, ref_back_parry_x6, motion_guide_side_combo)을 올립니다.
  3. 아래 [2] 공통 문구 + [3] 그 타의 문구를 붙여 넣습니다.
  4. 확인할 것:
     - 처음부터 끝까지 "뒷모습"인지 (고개·얼굴이 옆으로 돌아가지 않았는지)
     - 칼이 파란 단색 하나인지 (두 개가 되지 않았는지), 몸 앞(보는 사람 반대쪽)에 있는 부분은 가려졌는지
     - 후드·망토 색과 모양이 원본과 같은지
  5. 마음에 드는 그림을 이 폴더에 result_hit1.png / result_hit2.png / result_hit3.png 로 저장하고 알려 주세요.

[받은 뒤 제가 할 일]
  - 자세를 잘라 게임 크기로 줄이고(픽셀 덩어리 가운데 색, 뭉개지지 않게), 몸 색을 게임 주인공 색에 맞추고, 발 위치를 맞춤
  - 자세 사이를 PixelLab(시작·끝 지정)으로 채워 타마다 8장, 측면과 같은 박자(판정 프레임)로 맞춤
  - 파란 칼을 떼어 내 칼 위치·각도 표를 만들고, 게임 칼 그림을 겹쳐 그림 (몸에 가려지는 프레임은 몸 뒤로)
  - 미리보기 → 확인 후 게임에 넣음

------------------------------------------------------------------
[2] 공통 문구 (영어 그대로, 맨 앞에)
------------------------------------------------------------------
Using the first image as the exact character reference (same small hooded wanderer seen FROM BEHIND:
same worn brown hood, same tattered brown cape, same dark boots, same colours, same thick dark pixel
outline, same chibi proportions), draw the poses below of this character side by side in one image,
left to right, ALL SEEN FROM BEHIND (back to the viewer; the face is never visible and the head never
turns to the side). The character attacks AWAY from the viewer (toward the top of the image) with a
sword held in BOTH hands. The second image shows how a sword looks from behind: only the parts of the
blade that stick out past the body are visible, anything in front of the body is hidden by the back
and cape. The third image shows the same attack seen from the side, for the motion and timing.

Rules: the SWORD and its motion arc are drawn in ONE flat solid bright blue colour (#1E90FF) with no
other colours, exactly one sword. Same size and scale in every pose, feet on the same ground line.
Clean pixel art, flat solid grey (#808080) background, no shadows, no dust, no other effects, no text.

------------------------------------------------------------------
[3] 타별 문구 (공통 문구 뒤에 하나만)
------------------------------------------------------------------
(1타 result_hit1 : 사선 내려베기 — 측면 그림 첫째 줄)
Draw FOUR poses (HIT 1, a diagonal downward slash):
  0. STAND: exactly like the first image, no sword visible.
  1. RAISE: steps forward and lifts the sword high over the RIGHT shoulder with both hands; the blade
     points up and slightly back, clearly visible above and to the right of the hood.
  2. SLASH: swings the sword down hard diagonally from upper right to lower left; the blade is mostly
     hidden in front of the body, with ONE blue motion arc sweeping from above the right shoulder down
     past the LEFT side of the body.
  3. FOLLOW-THROUGH: body leaning forward low, the sword ends low on the LEFT side; only the tip of the
     blade sticks out past the left hip.

(2타 result_hit2 : 올려베기 — 측면 그림 둘째 줄)
Draw FOUR poses (HIT 2, a rising upward slash that continues from HIT 1):
  0. STAND: exactly like the first image, no sword visible.
  1. LOW: crouched a little, the sword held low on the LEFT side, the tip pointing down-left, visible
     past the left hip.
  2. RISING SLASH: swings the sword up from low left to high right in one motion; ONE blue motion arc
     sweeps from the lower left up and over to above the right shoulder.
  3. HIGH: standing taller, the sword raised high with both hands; the blade points straight up and is
     clearly visible above the hood.

(3타 result_hit3 : 찌르기 — 측면 그림 셋째 줄)
Draw FOUR poses (HIT 3, a straight two-handed thrust away from the viewer):
  0. STAND: exactly like the first image, no sword visible.
  1. PULL BACK: feet apart, both hands pull the sword back to the RIGHT hip, the blade pointing away
     from the viewer (mostly hidden by the body; only the pommel shows at the right hip).
  2. THRUST: lunges forward into a long stance, both arms extended forward away from the viewer; the
     blade points straight forward, so it shows straight up the image above the hood (foreshortened,
     narrow, clearly one straight blade).
  3. HOLD: the same thrust held, the body leaning a little further forward, the cape swinging back
     toward the viewer.
