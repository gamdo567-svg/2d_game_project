==================================================================
 골렘 기절(stun) — 핵심 자세를 다른 이미지 도구로 그리기
==================================================================

[0] 이 폴더 파일
  ref_golem_south_x8.png   정면 서 있는 그림 8배 (생김새·색 기준)
  ref_golem_east_x8.png    측면(오른쪽을 봄) 서 있는 그림 8배
  ref_golem_north_x8.png   후면 서 있는 그림 8배
  (서쪽은 동쪽 그림을 뒤집어 쓰므로 필요 없습니다)

  동작: 서기 → 크게 휘청임 → 한쪽 무릎을 꿇고 고개를 푹 숙임(코어 빛이 꺼짐).
  기절 2초 동안 무릎 꿇은 자세로 살짝 흔들리고, 풀리면 일어섭니다.
  머리 위 별 이펙트는 게임이 따로 그리므로 그림에 넣지 않습니다.

[1] 하는 법 (방향마다 한 번씩, 모두 3번)
  1. ChatGPT(이미지 생성) 새 대화를 엽니다.
  2. 그 방향 ref 그림 한 장을 올립니다.
  3. 아래 [2] 공통 문구 + 그 방향 줄 하나를 붙여 넣습니다.
  4. 확인할 것:
     - 세 자세 모두 처음 방향 그대로인지 (정면이면 계속 정면, 후면이면 계속 등만 보임)
     - 골렘 생김새·색·외곽선이 원본과 같은지 (이끼·갑옷·새 무늬가 없는지)
     - 세 자세의 크기가 같은지, 서 있는 발 자리가 같은지
  5. 결과를 이 폴더에 result_south.png / result_east.png / result_north.png 로 저장하고 알려 주세요.

[3] 받은 뒤 제가 할 일
  - 세 자세를 잘라 게임 크기로 줄이고, 색을 골렘 팔레트에 맞추고, 발 위치를 맞춤 (질감이 다르면 원본 부위로 다시 맞춤)
  - PixelLab 으로 서기 → 휘청 → 무릎, 무릎 → 서기 사이 동작을 채움 (시작·끝 자세 지정)
  - 미리보기 → 확인 후 게임에 넣음

------------------------------------------------------------------
[2] 공통 문구 (영어 그대로 붙여 넣기)
------------------------------------------------------------------
Using the attached image as the exact character reference (same stone golem: same rounded boulder
shapes, same dark charcoal-grey stone colours, same thick black pixel outline, same proportions and
size, no armor, no moss, no new details), draw THREE key poses of this golem side by side in one image,
left to right, all from the SAME viewing direction as the reference:

  1. STAND: exactly like the reference.
  2. STAGGER: dazed and losing balance after being stunned: the upper body sways back and to one side,
     the head lolls to the side, one arm swings loosely out, the knees start to buckle. Feet still on
     the ground.
  3. KNEEL: collapsed down onto ONE knee (the other foot still planted), the head hangs low and bowed,
     both arms hang limp with the fists resting near the ground, the whole body slumped and heavy.
     The glowing chest core (if visible from this side) is dimmed to dull grey, the eyes are dark.

Rules: same size and scale in all three poses; the planted foot stays in the same place; legs keep the
same length and thickness. Same camera angle as the reference (top-down game view, slightly from above).
Clean pixel art, flat solid grey (#808080) background, no shadows, no stars, no effects, no motion
lines, no text.

방향 줄 (공통 문구 바로 뒤에 하나만 붙임)
  정면 (ref_golem_south): The golem faces the viewer in all three poses.
  측면 (ref_golem_east):  The golem is seen from the side facing RIGHT in all three poses.
  후면 (ref_golem_north): The golem is seen FROM BEHIND in all three poses: its back faces the viewer,
                          the face and chest core are never visible; in pose 3 the bowed head is
                          almost hidden below the shoulders.
