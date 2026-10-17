"""Three Truths and a Lie: a fully scripted Reachy Mini game.

The robot only ever plays the 8 pre-recorded clips in voice/, one per button
press. No LLM, no live speech generation, no microphones, no internet.
The game logic lives in show.py, the phone remote in remote.py; this file
connects them to the robot.
"""

import logging
import threading
import urllib.request
from urllib.parse import urlparse

from reachy_mini import ReachyMini, ReachyMiniApp

from three_truths.remote import VOICE_DIR, add_routes, run_show, wav_duration
from three_truths.show import Command, Show

DAEMON_URL = "http://localhost:8000/api"

logger = logging.getLogger(__name__)


class RobotPlayer:
    """The real robot, as seen by the Show."""

    def __init__(self, mini: ReachyMini):
        self.mini = mini
        # Read every clip's length up front; fail early if a file is missing.
        self.durations = {p.stem: wav_duration(p) for p in sorted(VOICE_DIR.glob("*.wav"))}

    def wake_up(self) -> None:
        self.mini.wake_up()

    def goto_sleep(self) -> None:
        self.mini.goto_sleep()

    def play(self, clip: str) -> float:
        logger.info("Playing %s", clip)
        self.mini.media.play_sound(str(VOICE_DIR / f"{clip}.wav"))
        return self.durations[clip]

    def stop_sound(self) -> None:
        # The SDK has no stop call for play_sound, but the robot's daemon does.
        try:
            req = urllib.request.Request(f"{DAEMON_URL}/media/stop_sound", method="POST")
            urllib.request.urlopen(req, timeout=1.0)
        except OSError as e:
            logger.warning("Could not stop sound: %s", e)


class ThreeTruths(ReachyMiniApp):
    # The phone remote is served by the robot on this port.
    custom_app_url: str | None = "http://0.0.0.0:8042"
    # No camera needed; saves CPU on the Wireless.
    request_media_backend: str | None = "gstreamer_no_video"

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        show = Show(RobotPlayer(reachy_mini))
        commands = add_routes(self.settings_app, show, urlparse(self.custom_app_url).port)

        # Head moves in time with every clip played through play_sound().
        reachy_mini.enable_wobbling()

        run_show(show, commands, stop_event)

        # App stopped from Reachy Mini Control: cut any clip and go to sleep.
        show.handle(Command.STOP)


if __name__ == "__main__":
    app = ThreeTruths()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
