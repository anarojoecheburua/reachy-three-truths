# 🤖 Reachy Mini: Three Truths and a Lie

A fully scripted party game for the [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) robot, made for a live audience of about 100 people at **Science Night Glasgow** on Tuesday 20 October 2026.

Reachy tells the room four statements. Three are true and one is a lie, and the audience votes for the lie by scanning a QR code before Reachy reveals the answer.

- 🤗 **Install it on your Reachy:** [anarojoecheburua/reachy-three-truths](https://huggingface.co/spaces/anarojoecheburua/reachy-three-truths) on Hugging Face
- 💻 **Code, tests and this write-up:** you're here

> **Spoiler warning:** the answers are in [`script.md`](script.md). If you're coming to the show, don't peek.

## 🎲 The game

There are three rounds, each with its own theme:

1. **About me:** facts about Reachy Mini itself
2. **About robots:** robotics history and numbers
3. **About open source:** Linux, Hugging Face and what "open source" actually means

The show is split into 8 audio clips:

| Clip | What Reachy says |
|---|---|
| `01_intro` | Says hello and explains the rules and the QR code |
| `02_round1` | Four statements about itself |
| `03_reveal1` | Reveals the lie |
| `04_round2` | Four statements about robots |
| `05_reveal2` | Reveals the lie |
| `06_round3` | Four statements about open source |
| `07_reveal3` | Reveals the lie |
| `08_goodbye` | Thanks the room, then goes to sleep |

Ana, the presenter, says her cue lines out loud and presses NEXT at the same moment. To the audience it looks like Reachy is listening and replying. It isn't, and that's the whole trick.

## 🧠 Is the robot using an LLM?

**No. On the night, Reachy doesn't run an LLM or any AI model at all.**

This is everything that happens on stage:

1. Ana says her line to the audience and presses **NEXT** on the remote.
2. The remote sends that button press to the robot over wifi. It sends nothing else, no audio and no text.
3. The robot plays the next pre-recorded WAV file **through its own speaker**.
4. While the clip plays, the robot's head moves in time with the sound (the SDK calls this "wobbling"), so it looks like Reachy is talking. Reachy has no mouth, so there's no lip sync, but it moves like a puppet speaking.
5. The robot goes quiet and waits for the next press.

So the sound really does come from the robot, and the robot really is moving. Every word, though, was written by Ana and recorded in advance. Reachy isn't listening and can't improvise.

The only AI in this project is the **voice model**, which was used **once, beforehand**, on a laptop, to turn the approved script into audio files (see [how the voice was made](#%EF%B8%8F-how-the-voice-was-made)). Once a person had listened to and approved those files, the model had done its job, and the robot never touches it.

| | Before the show (on a laptop) | On the night (on the robot) |
|---|---|---|
| Script | Written and approved by Ana | Fixed |
| AI model | Qwen3-TTS turns the text into speech | **None** |
| Audio | Generated, listened to, approved | Pre-recorded WAVs, played in order |
| Microphones | Not used | Not used |
| Internet | Used to download the model | Not needed |

## 🔒 Why it's deterministic on purpose

This is a live demo in front of the public, so the robot must **never say anything that isn't in the script**. That rules out the things that make chatbots exciting and unpredictable:

- **No LLM at runtime.** Nothing generates words on the night.
- **No live speech generation.** Every line is a WAV file that was made in advance and checked by a person.
- **No listening to the room.** The microphones stay off, so nobody can heckle the robot into saying something odd.
- **No timers.** The show only moves forward when Ana presses a button.
- **No internet needed.** Venue wifi can be unreliable, so everything runs on the robot itself.

What you get is a robot that *feels* conversational but behaves like a jukebox with a very expressive head. Whatever happens in the room, the worst it can do is play the wrong pre-approved clip.

For an audience hearing a lot about AI, that's a useful thing to see. Plenty of "robot magic" on stage comes down to careful scripting and good timing.

## 🗣️ How the voice was made

Reachy's voice comes from **[Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)**, an open text-to-speech (TTS) model from Alibaba's Qwen team:

- **Model:** `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` (1.7 billion parameters)
- **Speaker:** "Aiden", one of the model's built-in voices and the same one Reachy Mini's conversation app uses
- **Language:** English, with no extra style instructions

### Is it an LLM?

Not in the sense people usually mean. An LLM like ChatGPT or Claude generates the words themselves. This model takes the text we give it and reads it out word for word.

Under the hood it's built in a similar way. Like an LLM, it's a transformer that predicts one token after another, except that its tokens are small chunks of sound (about 12 per second of audio). A separate decoder turns those sound tokens back into a waveform. So it's a language-model-style architecture put to work as a voice, with no say over the content.

Because it samples its output, each run sounds slightly different, a bit like an actor doing another take. That's why we **generate each clip once, listen to it and freeze it as a WAV file**. On the night no model runs at all, and the robot just plays those files back.

It can't go off-script while we're using it either. It has no way to add, drop or change words, only to choose how to pronounce them, so the worst it can do is mispronounce something. That's why a person checks every clip.

### Method

1. Write and approve the script ([`script.md`](script.md)).
2. Generate each clip with [`tools/generate_voice.py`](tools/generate_voice.py), either through the hosted [Qwen3-TTS Space](https://huggingface.co/spaces/Qwen/Qwen3-TTS) or locally on a Mac with `--local`.
3. Listen to every clip. If a word comes out wrong, change its spelling *only in the text sent to the model* and regenerate, so the script itself never changes. For example, "Ana" is Spanish (AH-na) and the model might say "Anna", in which case we'd send "Ahna" instead. As it turned out, Aiden said "Ana" correctly first time.
4. Bundle the approved WAVs inside the robot app ([`three_truths/three_truths/voice/`](three_truths/three_truths/voice/)).

The voice tool has its own virtual environment, because `qwen-tts` and the Reachy Mini SDK need different versions of some shared libraries:

```bash
python3 -m venv .venv-voice
.venv-voice/bin/pip install gradio_client          # hosted Space
.venv-voice/bin/pip install qwen-tts               # optional: run locally
.venv-voice/bin/python tools/generate_voice.py all            # via the Space
.venv-voice/bin/python tools/generate_voice.py all --local    # on your own machine
```

## 🛠️ How the robot app works

The app lives in [`three_truths/`](three_truths/). It was scaffolded with Pollen's `reachy-mini-app-assistant`, and [`plan.md`](three_truths/plan.md) tracks its progress.

- **Hardware:** Reachy Mini Wireless, which runs apps on its own Raspberry Pi CM4.
- **State machine** ([`show.py`](three_truths/three_truths/show.py)): the show is a list of 8 clips and four states.

  ```
  ASLEEP --NEXT--> PLAYING --clip ends--> WAITING --NEXT--> PLAYING ... --goodbye ends--> DONE (asleep)
  ```

  - Only a button press moves the show forward, and nothing happens on a timer.
  - Presses during a clip are ignored, so a nervous double tap can't skip a line.
  - REPEAT replays the current clip, BACK plays the previous one, and SKIP TO GOODBYE jumps to the last clip.
  - STOP always works. It cuts the clip and sends Reachy to sleep, and NEXT then carries on from where it stopped.

  There's no robot code in this file, which means every button sequence can be tested on a laptop with a fake robot ([`tests/test_show.py`](three_truths/tests/test_show.py)).
- **Robot glue** ([`main.py`](three_truths/three_truths/main.py)): connects the state machine to the real robot (wake up, sleep, play a clip, stop a clip). Button presses arrive as web requests and wait in a queue, so only one part of the app ever talks to the motors.
- **Speech with movement:** clips play through the robot's own speaker while its head wobbles in time with the audio. The WAVs ship inside the app, so nothing is streamed from anywhere else.
- **Sound in a big room:** the robot's 5 W speaker won't fill a hall of 100 people, so on the night a mic near Reachy or a feed into the venue's sound system boosts it.
- **Remote** ([`static/`](three_truths/three_truths/static/)): a web page served by the robot on port 8042, with a big NEXT button plus BACK, REPEAT, SKIP TO GOODBYE and STOP / SLEEP. It shows the current clip and what NEXT will play next.
  - Buttons that won't do anything right now (NEXT while Reachy is speaking, say) are greyed out.
  - SKIP and STOP need two taps within 2 seconds, so you can't hit them by accident.
  - The page shows the robot's IP address, because some Android phones can't open `reachy-mini.local` addresses.
  - The remote only sends button presses, and every decision is made on the robot.

## 🚀 Running it on your Reachy

1. Open **Reachy Mini Control**, go to **Discover Apps** and search for **Three Truths**. (It installs from the [Hugging Face Space](https://huggingface.co/spaces/anarojoecheburua/reachy-three-truths), so the robot needs internet for this step only.)
2. Install it and start it. Reachy stays asleep until the first press.
3. On a laptop or phone on the same network as the robot, open **http://reachy-mini.local:8042**. If that address doesn't load, use the IP address shown at the bottom of the remote.
4. Press **NEXT**.

It won't appear in the Reachy Mini phone app. That app only lists JS apps, which run on the phone and need Pollen's online service, whereas this is a Python app that runs on the robot so it can work offline. The remote still works in any phone browser.

### 🎭 Rehearsing without the robot

[`tools/rehearse.py`](tools/rehearse.py) runs the real remote and the real state machine on a laptop. It plays the clips through the laptop's speakers and prints what the robot would do, which is handy for practising your cue lines:

```bash
.venv/bin/python tools/rehearse.py           # then open http://localhost:8050
.venv/bin/python tools/rehearse.py --silent  # buttons only, no sound
```

### ✅ Running the tests

You don't need a robot for these:

```bash
python3 -m venv .venv
.venv/bin/pip install pytest -e three_truths
cd three_truths && ../.venv/bin/python -m pytest tests
```

## 🔬 About Science Night Glasgow

Science Night Glasgow is a monthly science meet-up in Glasgow, with a different theme every time. Each night runs for about two hours. Doors open with food and drinks, then there's a 90-minute programme of talks, a game and a hands-on demo, and the evening ends with more time to chat.

The first night, **Beyond Human**, covers robotics, brain-computer interfaces, prosthetics and human augmentation, and the ethics of "improving" humans. Nathan Western gives the first talk, Patty O'Callaghan speaks on the ethics of improving humans, and Kirsty Carlyle runs a hands-on demo with bionic and silicone prostheses. Reachy Mini runs the game.

## 🙌 Credits

- Robot: [Reachy Mini](https://github.com/pollen-robotics/reachy_mini) by Pollen Robotics and Hugging Face
- Voice: [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice) by the Qwen team
- Game and script: Ana ([@anarojoecheburua](https://github.com/anarojoecheburua))
