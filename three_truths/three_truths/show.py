"""The show's state machine: which clip plays when Ana presses a button.

This module has no robot code in it. It talks to the robot through a small
`Player` interface, so the whole game can be tested on a laptop with a fake
player (see tests/test_show.py).

Rules:
- The show starts ASLEEP. The first NEXT wakes Reachy up and plays the intro.
- Each NEXT plays the next clip. Nothing ever advances on a timer.
- While a clip is playing, NEXT / REPEAT / BACK / SKIP are ignored, so a
  double tap can't skip a line. STOP always works.
- After the goodbye clip finishes, Reachy goes to sleep and the show is DONE.
- STOP cuts the current clip, sends Reachy to sleep and remembers where we
  were. NEXT then wakes it and carries on with the following clip; REPEAT
  wakes it and replays the clip that was cut.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol

CLIPS = [
    "01_intro",
    "02_round1",
    "03_reveal1",
    "04_round2",
    "05_reveal2",
    "06_round3",
    "07_reveal3",
    "08_goodbye",
]
GOODBYE = len(CLIPS) - 1


class Player(Protocol):
    """Everything the show needs from the robot."""

    def wake_up(self) -> None: ...
    def goto_sleep(self) -> None: ...
    def play(self, clip: str) -> float:
        """Start playing a clip without blocking; return its length in seconds."""
        ...
    def stop_sound(self) -> None: ...


class State(str, Enum):
    ASLEEP = "asleep"
    PLAYING = "playing"
    WAITING = "waiting"  # awake, silent, waiting for Ana's next press
    DONE = "done"


class Command(str, Enum):
    NEXT = "next"
    REPEAT = "repeat"
    BACK = "back"
    SKIP_TO_GOODBYE = "skip_to_goodbye"
    STOP = "stop"


@dataclass
class Status:
    state: State
    step: int  # index into CLIPS of the current clip, -1 before the intro
    clip: str | None
    total: int = len(CLIPS)


class Show:
    # Small safety margin after each clip so the head wobble settles.
    END_MARGIN_S = 0.3

    def __init__(self, player: Player, clock: Callable[[], float] = time.monotonic):
        self.player = player
        self.clock = clock
        self.state = State.ASLEEP
        self.step = -1
        self._busy_until = 0.0

    # --- Public API -------------------------------------------------------

    def handle(self, command: Command) -> bool:
        """Apply one button press. Returns True if it did something."""
        self.tick()

        if command == Command.STOP:
            return self._stop()
        if self.state in (State.PLAYING, State.DONE):
            return False  # ignore presses mid-clip and after the show
        if self.step == -1 and command != Command.NEXT:
            return False  # only NEXT can start the show

        if command == Command.NEXT:
            return self._play(self.step + 1)
        if command == Command.REPEAT:
            return self._play(max(self.step, 0))
        if command == Command.BACK:
            return self._play(max(self.step - 1, 0))
        if command == Command.SKIP_TO_GOODBYE:
            return self._play(GOODBYE)
        return False

    def tick(self) -> None:
        """Call regularly: notices when a clip has finished."""
        if self.state != State.PLAYING or self.clock() < self._busy_until:
            return
        if self.step == GOODBYE:
            self.player.goto_sleep()
            self.state = State.DONE
        else:
            self.state = State.WAITING

    def status(self) -> Status:
        self.tick()
        clip = CLIPS[self.step] if self.step >= 0 else None
        return Status(self.state, self.step, clip)

    # --- Internals --------------------------------------------------------

    def _play(self, step: int) -> bool:
        if step >= len(CLIPS):
            return False
        if self.state == State.ASLEEP:
            self.player.wake_up()
        duration = self.player.play(CLIPS[step])
        self.step = step
        self.state = State.PLAYING
        self._busy_until = self.clock() + duration + self.END_MARGIN_S
        return True

    def _stop(self) -> bool:
        if self.state in (State.ASLEEP, State.DONE):
            return False
        if self.state == State.PLAYING:
            self.player.stop_sound()
        self.player.goto_sleep()
        self.state = State.ASLEEP
        return True
