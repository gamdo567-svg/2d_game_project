"""장면(scene).

장면은 다음 두 메서드를 가진다.
    update(dt, input_state) : 게임 로직 갱신 (pico2d 를 직접 호출하지 않는다)
    draw(renderer)          : Renderer 를 통해 그리기

장면 전환 관리자는 장면이 2개 이상 필요해질 때 추가한다.
"""
