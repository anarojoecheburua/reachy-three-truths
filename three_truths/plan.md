# Plan: three_truths

## What Ana wants
A fully scripted Three Truths and a Lie game for a live audience of ~100 at Science Night Glasgow (20 Oct 2026). Reachy plays 8 pre-recorded, human-approved clips, one per button press. It must never go off-script: no LLM, no live speech, no microphones, no timers, no internet at runtime.

## Technical approach
- **Python app** (on-robot, offline) scaffolded with `reachy-mini-app-assistant`, default template. Not yet published to Hugging Face; GitHub first.
- **Game logic** in `show.py`: a small state machine (ASLEEP → PLAYING ⇄ WAITING → DONE) with no robot code, unit-tested with a fake robot in `tests/test_show.py`.
- **Robot glue** in `main.py`: `wake_up()`, `goto_sleep()`, `media.play_sound()` with `enable_wobbling()`. Clip lengths are read from the WAV headers; STOP uses the daemon's `/api/media/stop_sound`.
- **Commands** arrive on FastAPI routes (`POST /command/{next,repeat,back,skip_to_goodbye,stop}`, `GET /state`) and are queued, so only the app thread ever drives the robot.
- **Voice**: 8 WAVs in `three_truths/voice/`, generated with Qwen3-TTS (speaker Aiden) and approved by Ana.

## Status
- [x] Scaffold, bundle WAVs, state machine, tests
- [x] Phone remote page in `static/` and laptop rehearsal mode (`tools/rehearse.py`)
- ~~Antenna tap as a backup NEXT~~ (decided against it: the laptop remote is enough)
- [ ] Optional idle and emotion moves (pre-cached for offline)
- [ ] Install on the robot and full dry run with the phone

## Decisions made
- Before the intro, only NEXT does anything.
- Presses during a clip are ignored; STOP always works.
- After STOP, NEXT carries on with the following clip, and REPEAT replays the one that was cut.
- After the goodbye, Reachy sleeps and further presses are ignored. To run the show again, restart the app from Reachy Mini Control.
