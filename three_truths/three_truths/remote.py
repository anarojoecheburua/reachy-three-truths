"""Phone remote routes and the show loop.

No Reachy Mini SDK imports here, so this also runs on a laptop for tests and
rehearsals (see tools/rehearse.py).
"""

import logging
import queue
import socket
import threading
import wave
from dataclasses import asdict
from pathlib import Path

from three_truths.show import Command, Show

VOICE_DIR = Path(__file__).parent / "voice"

logger = logging.getLogger(__name__)


def wav_duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def local_ip() -> str | None:
    """The robot's LAN address, for phones that can't resolve reachy-mini.local."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # No packet is sent; this just asks the OS which interface it would use.
            s.connect(("10.254.254.254", 1))
            return s.getsockname()[0]
    except OSError:
        return None


def add_routes(app, show: Show, port: int | None) -> "queue.Queue[Command]":
    """Web routes for the phone remote. Returns the queue of button presses.

    The routes only queue commands; the robot is driven from the show thread
    alone, so two presses can never talk to it at the same time.
    """
    commands: queue.Queue[Command] = queue.Queue()

    @app.post("/command/{name}")
    def send_command(name: Command):
        commands.put(name)
        return {"queued": name}

    @app.get("/state")
    def get_state():
        return asdict(show.status())

    @app.get("/info")
    def get_info():
        return {"ip": local_ip(), "port": port}

    return commands


def run_show(show: Show, commands: "queue.Queue[Command]", stop_event: threading.Event) -> None:
    """Apply button presses one at a time until the app is stopped."""
    while not stop_event.is_set():
        try:
            command = commands.get(timeout=0.05)
            done = show.handle(command)
            logger.info("%s -> %s (%s)", command.value, show.status(), "ok" if done else "ignored")
        except queue.Empty:
            show.tick()
