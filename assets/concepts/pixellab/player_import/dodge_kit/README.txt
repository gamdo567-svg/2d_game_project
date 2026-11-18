==================================================================
 주인공 회피(dodge) — 핵심 자세를 ChatGPT 로 그리기 (2026-11-18)
==================================================================

회피 규칙: Q, 바라보는(누른) 방향으로 2칸을 0.25초에 미끄러지듯 이동, 내내 무적. 칼은 그리지 않음.
방향은 정면(아래로 = 보는 사람 쪽으로), 측면(오른쪽으로), 후면(위로 = 보는 사람 반대쪽으로) 세 가지.
왼쪽은 측면을 뒤집어 씀.

[0] 이 폴더 파일
  ref_player_front_x12.png  정면 서 있는 그림 12배
  ref_player_side_x12.png   측면(오른쪽을 봄) 12배
  ref_player_back_x12.png   후면 12배
  ref_player_all_x8.png     세 방향 나란히

[1] 하는 법 (방향마다 새 대화 하나)
  1. ChatGPT(이미지 생성) 새 대화를 엽니다.
  2. 그 방향의 ref_player_<방향>_x12.png 를 올립니다.
  3. 아래 [2] 공통 문구 + [3] 그 방향 문구를 붙여 넣습니다.
  4. 확인할 것:
     - 네 자세 모두 같은 방향인지 (후면은 끝까지 뒷모습, 고개·얼굴이 옆으로 돌지 않음)
     - 후드·망토 색과 모양이 원본과 같은지, 칼이 없는지
     - 다리가 바뀌거나 늘어나지 않았는지
  5. 마음에 드는 그림을 이 폴더에 result_front.png / result_side.png / result_back.png 로 저장하고 알려 주세요.

[받은 뒤 제가 할 일]
  - 네 자세를 잘라 게임 크기(32×48)로 줄이고, 색을 게임 주인공 색에 맞추고, 발 위치를 맞춤
  - 자세 사이(웅크림→돌진, 돌진→미끄러짐, 미끄러짐→서기)를 PixelLab(시작·끝 자세 지정)으로 채움
  - 미리보기 → 확인 후 게임에 넣음

------------------------------------------------------------------
[2] 공통 문구 (영어 그대로, 맨 앞에)
------------------------------------------------------------------
Using the uploaded image as the exact character reference (same small hooded wanderer: same worn
brown hood pulled low so the eyes are hidden in shadow, same tattered brown shoulder cape, same dark
clothes and boots, same colours, same thick dark pixel outline, same chibi proportions, NO weapon in
the hands), draw FOUR poses of this character side by side in one image, left to right, as a quick
evasive DASH (a fast low dodge that slides two steps along the ground). Keep the SAME viewing angle in
all four poses. Same size and scale in all four, clean pixel art, flat solid grey (#808080)
background, no shadows on the ground, no motion lines, no dust, no text.

  0. STAND: exactly like the reference image.
  1. CROUCH: knees bent, body lowered and leaning into the dash direction, ready to push off.
  2. DASH: very low and stretched, the body leaning hard into the dash direction, one leg pushing
     behind, the cape and the hood's tip blown back by the speed.
  3. SLIDE STOP: still low, feet planted and sliding to a stop, the body pulled back upright a little,
     the cape swinging forward past the body as it stops.

------------------------------------------------------------------
[3] 방향별 문구 (공통 문구 뒤에 하나만)
------------------------------------------------------------------
(정면 result_front)
View: seen from the FRONT in every pose; the character dashes straight TOWARD the viewer, so leaning
into the dash means leaning toward the viewer (the head and shoulders come lower and closer, the hood
tips forward); the cape flies up behind the shoulders. Never turn sideways.

(측면 result_side)
View: seen from the SIDE facing RIGHT in every pose (like the reference); the character dashes to the
RIGHT, leaning right, the cape streaming out to the LEFT behind it. Never turn toward the viewer.

(후면 result_back)
View: seen from BEHIND in every pose (back to the viewer, like the reference); the character dashes
straight AWAY from the viewer. The face is NEVER visible and the head NEVER turns to the side. Leaning
into the dash means the hood and shoulders go forward and lower (away from the viewer), so the back
and the cape show more; the cape lifts and flutters toward the viewer. Both legs stay behind the cape,
one boot sole may show pushing off.
