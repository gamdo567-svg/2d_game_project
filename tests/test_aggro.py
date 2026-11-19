"""몬스터 어그로 테스트 (2026-11-20 사용자 결정, pico2d 없이)."""
import unittest

from game import config
from game.enemies.aggro import AggroTracker
from game.enemies.golem import DEAD, DORMANT, WAKING, Golem, aggro_mark_pose


def open_room(c, r):
    return not (0 <= c < 40 and 0 <= r < 20)


def place_ok(c, r):
    return True


class GolemDormantTest(unittest.TestCase):
    def test_dormant_golem_stays_still_and_does_not_attack(self):
        golem = Golem(10, 5, open_room, dormant=True)
        self.assertEqual(golem.state, DORMANT)
        for _ in range(300):  # 주인공이 바로 옆에 있어도 (어그로가 끌리지 않았으면) 가만히
            golem.update(1 / 60, (9, 5), place_ok)
            self.assertEqual(golem.attacks, [])
        self.assertEqual(golem.state, DORMANT)
        self.assertEqual((golem.col, golem.row), (10, 5))

    def test_wake_shows_mark_then_starts_acting(self):
        golem = Golem(10, 5, open_room, dormant=True)
        golem.wake()
        self.assertEqual(golem.state, WAKING)
        self.assertEqual(golem.aggro_mark_age, 0.0)  # 붉은 ! 가 뜸
        golem.update(config.GOLEM_WAKE_TIME / 2, (9, 5), place_ok)
        self.assertEqual(golem.state, WAKING)  # 코어가 켜지는 중엔 공격하지 않음
        golem.update(config.GOLEM_WAKE_TIME, (9, 5), place_ok)
        self.assertNotIn(golem.state, (DORMANT, WAKING))
        golem.update(config.AGGRO_MARK_TIME, (9, 5), place_ok)
        self.assertLess(golem.aggro_mark_age, 0)  # ! 는 잠깐 뒤 사라짐

    def test_respawns_dormant(self):
        golem = Golem(10, 5, open_room, dormant=True)
        golem.wake()
        golem.take_hit(config.GOLEM_MAX_HP, (1, 0))
        self.assertEqual(golem.state, DEAD)
        golem.update(config.GOLEM_RESPAWN_TIME + 0.1, (0, 0), place_ok)
        self.assertEqual(golem.state, DORMANT)

    def test_default_golem_is_awake(self):
        self.assertNotEqual(Golem(10, 5, open_room).state, DORMANT)

    def test_mark_springs_out_squashes_wobbles_and_fades(self):
        rising = aggro_mark_pose(0.08)
        landed = aggro_mark_pose(0.22)
        later = [aggro_mark_pose(0.22 + k / 60) for k in range(30)]
        steady = aggro_mark_pose(0.8)
        fading = aggro_mark_pose(config.AGGRO_MARK_TIME - 0.05)
        self.assertGreater(rising["sy"], rising["sx"])  # 위로 쭉 늘어나며
        self.assertGreater(rising["lift"], 0)  # 솟구침
        self.assertGreater(landed["sx"], 1.2)  # 내려앉으며 납작
        self.assertLess(landed["sy"], 0.8)
        self.assertGreater(max(abs(p["angle"]) for p in later), 3)  # 좌우로 흔들림
        self.assertAlmostEqual(steady["sx"], 1.0, places=1)  # 제 크기로 멈춤
        self.assertLess(abs(steady["angle"]), 0.5)  # 흔들림이 거의 멈춤
        self.assertGreater(aggro_mark_pose(0.02)["flash"], 0.5)  # 처음엔 하얗게 번쩍
        self.assertIsNotNone(aggro_mark_pose(0.2)["burst"])  # 강조선
        self.assertIsNone(steady["burst"])
        self.assertLess(fading["opacity"], 0.5)  # 끝에서 옅어지며
        self.assertGreater(fading["lift"], 0)  # 떠오름

class AggroTrackerTest(unittest.TestCase):
    def setUp(self):
        self.aggro = AggroTracker()
        self.near = Golem(10, 5, open_room, dormant=True)
        self.far = Golem(20, 5, open_room, dormant=True)
        self.golems = [self.near, self.far]

    def test_wakes_only_within_distance(self):
        self.aggro.update((10 - config.AGGRO_WAKE_DISTANCE - 1, 5), self.golems)
        self.assertIsNone(self.aggro.target)
        self.assertTrue(self.near.dormant)
        self.aggro.update((10 - config.AGGRO_WAKE_DISTANCE, 5), self.golems)
        self.assertIs(self.aggro.target, self.near)
        self.assertEqual(self.near.state, WAKING)

    def test_only_one_monster_at_a_time(self):
        self.aggro.update((15, 5), self.golems)  # 둘 다 6칸 안: 더 가까운 하나만
        self.assertIs(self.aggro.target, self.near)
        self.assertTrue(self.far.dormant)
        self.aggro.update((19, 5), self.golems)  # 다른 골렘 바로 옆에 가도 끌리지 않음
        self.assertIs(self.aggro.target, self.near)
        self.assertTrue(self.far.dormant)

    def test_hitting_another_dormant_monster_does_not_pull_it(self):
        self.aggro.update((9, 5), self.golems)
        self.far.take_hit(10, (1, 0))
        self.aggro.on_hit(self.far)
        self.assertTrue(self.far.dormant)  # 피해만 받고 휴면 그대로
        self.assertEqual(self.far.hp, config.GOLEM_MAX_HP - 10)

    def test_hit_wakes_from_any_distance_when_free(self):
        self.aggro.on_hit(self.far)
        self.assertIs(self.aggro.target, self.far)
        self.assertEqual(self.far.state, WAKING)

    def test_keeps_target_when_far_and_releases_when_dead(self):
        self.aggro.update((9, 5), self.golems)
        self.aggro.update((39, 19), self.golems)  # 멀리 도망쳐도 유지
        self.assertIs(self.aggro.target, self.near)
        self.near.take_hit(config.GOLEM_MAX_HP, (1, 0))  # 죽이면 놓고, 거리 안의 다른 몬스터가 끌림
        self.aggro.update((17, 5), self.golems)
        self.assertIs(self.aggro.target, self.far)
        self.assertEqual(self.far.state, WAKING)


if __name__ == "__main__":
    unittest.main()
