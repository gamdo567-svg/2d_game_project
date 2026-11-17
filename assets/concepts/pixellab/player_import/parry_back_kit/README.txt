==================================================================
 주인공 후면 패링 — 핵심 자세를 다른 이미지 도구로 그리기
==================================================================

[0] 이 폴더 파일
  ref_player_back_x12.png       게임 주인공 뒷모습 서 있는 그림 12배 (생김새·색 기준)
  ref_back_ready_guard_x8.png   후면 당김(1)·막기(3) 자세 참고 (PixelLab 이 깨끗하게 그린 것)
  motion_guide_front_side.png   완성된 측면·정면 패링 순서: 서기 / 1 당김 / 2 쳐올림 / 3 막기 / 막기 / 당김
  ※ 칼은 측면·정면처럼 "파란 단색"으로 그려야 제가 칼만 따로 떼어 게임의 칼 그림으로 바꿀 수 있습니다.

[1] 하는 법
  1. ChatGPT(이미지 생성) 새 대화를 엽니다.
  2. 세 그림(ref_player_back_x12, ref_back_ready_guard_x8, motion_guide_front_side)을 올립니다.
  3. 아래 [2] 문구를 붙여 넣습니다.
  4. 확인할 것:
     - 처음부터 끝까지 "뒷모습"인지 (고개·얼굴이 옆으로 돌아가지 않았는지)
     - 칼이 파란 단색 하나인지, 칼이 두 개가 되지 않았는지
     - 망토·후드 색과 모양이 원본과 같은지
  5. 마음에 드는 그림을 이 폴더에 result_back.png 로 저장하고 알려 주세요.

[3] 받은 뒤 제가 할 일
  - 네 자세를 잘라 게임 크기(원본 32×48 기준)로 줄이고, 몸 색을 게임 주인공 색에 맞추고, 발 위치를 맞춤
  - 정면 패링과 같은 시트(parry_back_sheet_68.png)로 만들어 export_to_game.py 로 몸 그림·칼 위치표를 뽑음
  - 미리보기 → 확인 후 게임에 넣음

------------------------------------------------------------------
[2] 문구 (영어 그대로)
------------------------------------------------------------------
Using the first image as the exact character reference (same small hooded wanderer seen FROM BEHIND:
same worn brown hood, same tattered brown cape, same dark boots, same colours, same thick dark pixel
outline, same chibi proportions), draw FOUR poses of this character side by side in one image, left to
right, ALL SEEN FROM BEHIND (back to the viewer, the face is never visible, the head does not turn):

  0. STAND: exactly like the first image.
  1. READY: pulls a sword up in front of the body with both hands, the blade standing straight up,
     so from behind only the upper part of the blade shows above the RIGHT shoulder (like the second
     image, left pose).
  2. SWING UP: a quick upward parry swing: the sword sweeps from low in front up and across to the
     upper LEFT, with one bright motion arc trail behind the blade; the shoulders twist slightly.
  3. GUARD: holds the sword raised diagonally to the upper LEFT to block, both hands on the grip,
     blade clearly visible above and to the left of the head (like the second image, right pose).

Rules: the SWORD and its motion arc are drawn in ONE flat solid bright blue colour (#1E90FF) with no
other colours, exactly one sword. Only the hands and the parts of the blade that stick out past the
body are visible; anything in front of the body is hidden by the back and cape. The feet stay planted
in the same place in all poses. Same size and scale in all four poses, feet on the same ground line.
Clean pixel art, flat solid grey (#808080) background, no shadows, no other effects, no text.
