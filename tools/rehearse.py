"""Rehearse the show on a laptop, no robot needed.

Serves the real phone remote and runs the real state machine (show.py), but
plays the clips through this computer's speakers and prints what the robot
would do. Open the printed address on your phone (same wifi) or in a browser.

    .venv/bin/python tools/rehearse.py           # with sound
    .venv/bin/python tools/rehearse.py --silent  # just the buttons
"""

import subprocess
import sys
import threading
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import the app straight from the repo, no install needed.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "three_truths"))

from three_truths.remote import VOICE_DIR, add_routes, local_ip, run_show, wav_duration
from three_truths.show import Show

# Not 8042: the Reachy Mini Control desktop app already uses that port.
PORT = 8050
STATIC = VOICE_DIR.parent / "static"


class LaptopPlayer:
    """Stands in for the robot: plays audio locally and prints the moves."""

    def __init__(self, silent=False):
        self.silent = silent
        self.proc = None

    def wake_up(self):
        print("🤖 wake up")

    def goto_sleep(self):
        print("😴 go to sleep")

    def play(self, clip):
        print(f"🔊 {clip}")
        path = VOICE_DIR / f"{clip}.wav"
        if not self.silent:
            self.proc = subprocess.Popen(["afplay", str(path)])  # macOS player
        return wav_duration(path)

    def stop_sound(self):
        print("⏹  stop sound")
        if self.proc:
            self.proc.terminate()


def main():
    sys.stdout.reconfigure(line_buffering=True)  # show each action straight away
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    app.get("/")(lambda: FileResponse(STATIC / "index.html"))

    show = Show(LaptopPlayer(silent="--silent" in sys.argv))
    commands = add_routes(app, show, PORT)
    threading.Thread(target=run_show, args=(show, commands, threading.Event()), daemon=True).start()

    print(f"Remote: http://localhost:{PORT}  (phone: http://{local_ip()}:{PORT})")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
