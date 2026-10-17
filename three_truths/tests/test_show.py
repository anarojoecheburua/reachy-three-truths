"""Tests for the show's state machine, with a fake robot and a fake clock."""

import pytest

from three_truths.show import CLIPS, Command, Show, State

N, R, B, S, X = (Command.NEXT, Command.REPEAT, Command.BACK,
                 Command.SKIP_TO_GOODBYE, Command.STOP)
CLIP_S = 10.0


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class FakePlayer:
    def __init__(self):
        self.log = []

    def wake_up(self):
        self.log.append("wake")

    def goto_sleep(self):
        self.log.append("sleep")

    def play(self, clip):
        self.log.append(clip)
        return CLIP_S

    def stop_sound(self):
        self.log.append("stop_sound")


@pytest.fixture
def show():
    return Show(FakePlayer(), clock=FakeClock())


def press(show, command):
    return show.handle(command)


def finish_clip(show):
    show.clock.t += CLIP_S + 1
    show.tick()


def test_starts_asleep(show):
    assert show.status().state == State.ASLEEP
    assert show.player.log == []


def test_first_next_wakes_and_plays_intro(show):
    assert press(show, N)
    assert show.player.log == ["wake", "01_intro"]
    assert show.status().state == State.PLAYING


def test_only_next_can_start_the_show(show):
    for c in (R, B, S, X):
        assert not press(show, c)
    assert show.player.log == []


def test_full_run_plays_every_clip_in_order_then_sleeps(show):
    for _ in CLIPS:
        press(show, N)
        finish_clip(show)
    assert show.player.log == ["wake", *CLIPS, "sleep"]
    assert show.status().state == State.DONE


def test_nothing_advances_without_a_press(show):
    press(show, N)
    show.clock.t += 3600
    show.tick()
    assert show.status().state == State.WAITING
    assert show.player.log == ["wake", "01_intro"]


def test_presses_during_a_clip_are_ignored(show):
    press(show, N)
    for c in (N, N, R, B, S):
        assert not press(show, c)
    assert show.player.log == ["wake", "01_intro"]


def test_repeat_and_back(show):
    press(show, N); finish_clip(show)
    press(show, N); finish_clip(show)   # 02_round1
    press(show, R); finish_clip(show)   # 02_round1 again
    press(show, B); finish_clip(show)   # 01_intro
    press(show, B); finish_clip(show)   # still 01_intro, can't go before it
    assert show.player.log[2:] == ["02_round1", "02_round1", "01_intro", "01_intro"]


def test_skip_to_goodbye_then_sleep(show):
    press(show, N); finish_clip(show)
    press(show, S); finish_clip(show)
    assert show.player.log[-2:] == ["08_goodbye", "sleep"]
    assert show.status().state == State.DONE


def test_presses_after_the_show_are_ignored(show):
    press(show, N); finish_clip(show)
    press(show, S); finish_clip(show)
    for c in (N, R, B, S, X):
        assert not press(show, c)


def test_stop_mid_clip_cuts_sound_and_sleeps(show):
    press(show, N); finish_clip(show)
    press(show, N)                      # 02_round1 playing
    assert press(show, X)
    assert show.player.log[-2:] == ["stop_sound", "sleep"]
    assert show.status().state == State.ASLEEP


def test_after_stop_next_resumes_and_repeat_replays(show):
    press(show, N); finish_clip(show)
    press(show, N)                      # 02_round1, cut by STOP
    press(show, X)
    press(show, R)                      # wake + replay 02_round1
    assert show.player.log[-2:] == ["wake", "02_round1"]
    finish_clip(show)
    press(show, X)                      # stop while waiting: no stop_sound
    assert show.player.log[-1] == "sleep" and show.player.log[-2] != "stop_sound"
    press(show, N)                      # wake + 03_reveal1
    assert show.player.log[-2:] == ["wake", "03_reveal1"]


def test_every_clip_has_a_wav():
    from three_truths.main import VOICE_DIR, wav_duration
    for clip in CLIPS:
        assert wav_duration(VOICE_DIR / f"{clip}.wav") > 1.0
