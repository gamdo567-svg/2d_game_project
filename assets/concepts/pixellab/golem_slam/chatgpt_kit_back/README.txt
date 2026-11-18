==================================================================
 골렘 ① 두 손 내려찍기 (후면) — 핵심 자세를 다른 이미지 도구로 그리기
==================================================================

[0] 이 폴더 파일
  ref_golem_north_x8.png   게임 골렘 뒷모습 서 있는 그림 8배 (생김새·색 기준)
  motion_guide.png         윗줄 = 정면 내려찍기 (잘 된 것: 1 서기 / 2 들기 / 3 내려찍기 / 4 일어서기)
                           아랫줄 = 지금 후면. 1·2 는 괜찮고, 3·4 에서 몸은 안 숙이고 팔만 옆으로 돌아온 것이 문제

[1] 하는 법
  1. ChatGPT(이미지 생성) 새 대화를 엽니다.
  2. ref_golem_north_x8.png 와 motion_guide.png 두 장을 올립니다.
  3. 아래 [2] 문구를 붙여 넣습니다.
  4. 확인할 것:
     - 네 자세 모두 "뒷모습"인지 (얼굴·가슴 코어가 보이지 않는지)
     - 3 내려찍기에서 등을 크게 숙여 머리가 거의 안 보이고, 두 손은 몸 앞 바닥 쪽이라 등에 가려졌는지
     - 4 일어서기에서 몸과 팔이 "함께" 올라오는지 (팔만 먼저 옆으로 돌아오지 않았는지)
     - 골렘 생김새·색이 원본과 같은지 (갑옷·이끼·새 무늬가 생기지 않았는지), 발 위치가 같은지
  5. 마음에 드는 그림을 이 폴더에 result_north.png 로 저장하고 알려 주세요.

[3] 받은 뒤 제가 할 일
  - 네 자세를 잘라 게임 크기로 줄이고, 색을 골렘 팔레트에 맞추고, 발 위치를 맞춤
  - PixelLab 으로 서기 → 들기, 내려찍기 → 일어서기 → 서기 사이 동작을 채움 (시작·끝 자세 지정)
  - 지금 후면 내려찍기(slam_north.png)를 바꿈. 정면·측면·충격 이펙트는 그대로
  - 미리보기 → 확인 후 게임에 넣음

------------------------------------------------------------------
[2] 문구 (영어 그대로 붙여 넣기)
------------------------------------------------------------------
Using the first image as the exact character reference (same stone golem seen FROM BEHIND: same
rounded boulder shapes, same dark charcoal-grey stone colours, same thick black pixel outline, same
proportions, no armor, no moss, no new details), draw FOUR key poses of this golem side by side in one
image, left to right, ALL SEEN FROM BEHIND (its back faces the viewer; the face and the glowing chest
core are never visible). The second image shows the same attack from the FRONT (top row) as a guide
for timing and body posture; copy those postures but seen from behind.

  1. STAND: exactly like the reference.
  2. RAISE: both arms raised high above the head, fists joined together, ready to smash down; the
     fists are clearly visible above the head.
  3. SLAM: both joined fists smashed down to the ground IN FRONT of the golem (away from the viewer).
     The upper body is bent far forward, so we see the big rounded back and shoulders from behind and
     the head is almost hidden below the shoulders. The arms and fists are in front of the body, so
     they are HIDDEN behind the back; at most the upper arms show at the shoulders. Knees slightly bent.
  4. RISING: halfway back up from the slam. The back straightens up and the arms come up TOGETHER with
     the body, still in front of it (elbows bent, fists low in front at hip height, mostly hidden behind
     the body; only the elbows and the edges of the forearms show at the sides). The head is visible
     again above the shoulders.

Rules: the feet stay planted in exactly the same place in all four poses (same ground line, same
distance between the feet); legs keep the same length and thickness. Same camera angle as the
reference (top-down game view, slightly from above). Same size and scale in all four poses. Clean
pixel art, flat solid grey (#808080) background, no shadows, no dust, no effects, no motion lines,
no text.
