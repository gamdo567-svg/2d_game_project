==================================================================
 골렘 ② 올려차기 — 핵심 자세를 다른 이미지 도구로 그리기
==================================================================

[0] 이 폴더 파일
  ref_golem_<방향>_x8.png   게임에 들어간 골렘 서 있는 그림을 8배 확대 (생김새·색 기준)
  pose_guide_<방향>.png     자세 안내: 1 서기 / 2 준비 / 3 차기
                             (어느 다리로 차는지·몸 방향은 이걸 따르고, 차는 높이는 더 크게)
  방향: south = 정면(보는 사람 쪽), north = 뒷모습, east = 오른쪽을 봄, west = 왼쪽을 봄

[1] 하는 법 (방향마다 한 번씩, 4번)
  1. ChatGPT(이미지 생성) 새 대화를 엽니다. 방향마다 새 대화가 좋습니다.
  2. 그 방향의 ref_golem_<방향>_x8.png 와 pose_guide_<방향>.png 두 장을 올립니다.
  3. 아래 [2] 공통 문구 + [3] 그 방향 문구를 붙여 넣습니다.
  4. 결과가 마음에 들 때까지 다시 생성합니다. 특히 확인할 것:
     - 준비에서 뒤로 당긴 다리와 차기에서 올라간 다리가 "같은 다리"인지
     - 다리 길이가 서 있을 때와 같은지 (갑자기 길어지지 않았는지)
     - 골렘 생김새·색이 원본과 같은지 (갑옷·이끼·새 무늬가 생기지 않았는지)
  5. 마음에 드는 그림을 이 폴더에 저장해 주세요:
       result_south.png, result_east.png, result_north.png, result_west.png
     (west 가 어려우면 east 만 있어도 됩니다. 제가 좌우 반전으로 만들 수 있습니다)
  6. 저에게 "받았어" 라고 알려 주세요.

[4] 받은 뒤 제가 할 일
  - 세 자세를 잘라 게임 크기(원본 96px 기준)로 줄이고, 색을 골렘 팔레트에 맞추고, 발 위치를 맞춤
  - PixelLab 으로 서기 → 준비 → 차기 → 착지 → 서기 사이 동작을 채움 (시작·끝 자세 지정)
  - 미리보기 → 확인 후 게임에 넣음

------------------------------------------------------------------
[2] 공통 문구 (영어 그대로 붙여 넣기)
------------------------------------------------------------------
Using the first image as the exact character reference (same stone golem: same rounded boulder
shapes, same dark charcoal-grey stone colours, same tiny white eye dots, same small glowing white
chest core, same thick black pixel outline, no armor, no moss, no new details), draw THREE key poses
of this golem side by side in one image, left to right, following the second image as the pose guide:

  1. STAND: exactly like the reference.
  2. WIND-UP: standing on the LEFT leg, the RIGHT leg pulled far back behind the body with the knee
     bent, upper body leaning forward, both fists held forward for balance.
  3. KICK: a powerful rising front kick with the SAME RIGHT leg: the right leg swung forward and up,
     almost straight, the right foot at chest height in front of the body; standing on the left leg;
     upper body leaning back; both arms swung back for balance.

Rules: the kicking leg is the same right leg in poses 2 and 3. Both legs keep exactly the same
length and thickness as in the reference (do not stretch the leg). Same camera angle as the
reference (top-down game view, slightly from above). Same size and scale in all three poses, feet on
the same ground line. Clean pixel art, flat solid grey (#808080) background, no shadows, no effects,
no motion lines, no text.

------------------------------------------------------------------
[3] 방향별 문구 (공통 문구 다음 줄에 붙여 넣기)
------------------------------------------------------------------
[south / 정면]
View: the golem faces the viewer. Its RIGHT leg is on the LEFT side of the image. In WIND-UP the
right leg goes back and up behind the body (only the foot and lower leg peek out behind, raised).
In KICK the right foot comes up toward the viewer at chest height in front of the body, the sole
facing the viewer.

[east / 오른쪽]
View: the golem faces RIGHT (profile). Its RIGHT leg is the leg nearer to the viewer. In WIND-UP
that near leg is pulled back to the LEFT side of the image, behind the body. In KICK the same near
leg swings to the RIGHT and up, foot at chest height in front of the body.

[west / 왼쪽]
View: the golem faces LEFT (profile). Its RIGHT leg is the leg farther from the viewer (partly behind
the body). In WIND-UP that far leg is pulled back to the RIGHT side of the image. In KICK the same far
leg swings to the LEFT and up, foot at chest height in front of the body.

[north / 뒷모습]
View: we see the golem from BEHIND (its back faces the viewer). Its RIGHT leg is on the RIGHT side of
the image. In WIND-UP the right leg is pulled back toward the viewer, the foot raised and clearly
visible below the body. In KICK the right leg swings forward away from the viewer, so it is HIDDEN
behind the golem's body; we only see the left leg standing, the back leaning backward toward the
viewer, and both arms swung back toward the viewer.
