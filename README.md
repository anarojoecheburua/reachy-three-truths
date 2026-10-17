# Reachy Mini: Three Truths and a Lie

A fully scripted party game for the [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) robot, built for a live audience of about 100 people at **Science Night Glasgow** ("Beyond Human" night, Tuesday 20 October 2026).

Reachy tells the room four statements. Three are true, one is a lie, and the audience votes for the lie by scanning a QR code. Then Reachy reveals the answer.

> **Spoiler warning:** the answers are in [`script.md`](script.md). If you're coming to the show, don't peek.

## The game

There are three rounds, each on a different theme:

1. **About me:** facts about Reachy Mini itself
2. **About robots:** robotics history and numbers
3. **About open source:** Linux, Hugging Face and what "open source" actually means

The show is split into 8 audio clips:

| Clip | What Reachy says |
|---|---|
| `01_intro` | Hello, explains the rules and the QR code |
| `02_round1` | Four statements about itself |
| `03_reveal1` | Reveals the lie |
| `04_round2` | Four statements about robots |
| `05_reveal2` | Reveals the lie |
| `06_round3` | Four statements about open source |
| `07_reveal3` | Reveals the lie |
| `08_goodbye` | Thanks the room, then goes to sleep |

Ana, the presenter, says her cue lines out loud and presses a button on her phone at the same moment. To the audience it looks like Reachy is listening and replying. It isn't. That's the trick, and it's also the point of this project.

## Is the robot using an LLM?

**No. On the night, Reachy doesn't run an LLM or any AI model at all.**

Here's everything that happens on stage:

1. Ana says her line to the audience and presses **NEXT** on her phone.
2. The phone sends that button press to the robot over wifi. That's all it sends: no audio, no text.
3. The robot plays the next pre-recorded WAV file **through its own speaker**.
4. While the clip plays, the robot's head moves in time with the sound (the SDK calls this "wobbling"), so it looks like Reachy is talking. Reachy has no mouth, so it isn't lip sync, but it moves like a puppet speaking.
5. The robot goes quiet and waits for the next press.

So the sound really does come from the robot, and the robot really is moving. But every word was written by Ana and recorded in advance. Reachy isn't thinking, isn't listening and can't improvise.

The only AI in this project is the **voice model**, and it was used **once, beforehand**, on a laptop, to turn the approved script into audio files (see [How the voice was made](#how-the-voice-was-made)). Once a person had listened to and approved those files, the model's job was done. The robot never sees it.

| | Before the show (on a laptop) | On the night (on the robot) |
|---|---|---|
| Script | Written and approved by Ana | Fixed |
| AI model | Qwen3-TTS turns the text into speech | **None** |
| Audio | Generated, listened to, approved | Pre-recorded WAVs, played in order |
| Microphones | Not used | Not used |
| Internet | Used to download the model | Not needed |

## Why it's deliberately deterministic

This is a live demo in front of the public, so the robot must **never say anything that isn't in the script**. That rules out the things that make chatbots exciting and unpredictable:

- **No LLM at runtime.** Nothing generates words on the night.
- **No live speech generation.** Every line is a pre-recorded WAV file, made in advance and checked by a human.
- **No listening to the room.** The microphones aren't used, so nobody can heckle the robot into saying something odd.
- **No timers.** The show only moves forward when Ana presses a button.
- **No internet needed.** The venue wifi might be unreliable, so everything runs on the robot itself.

The result is a robot that *feels* conversational but behaves like a jukebox with a very expressive head. Whatever happens in the room, the worst it can do is play the wrong pre-approved clip.

This is a useful contrast for an audience hearing a lot about AI: a lot of "robot magic" on stage is careful scripting and timing, not intelligence.

## How the voice was made

Reachy's voice comes from **[Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)**, an open text-to-speech (TTS) model from Alibaba's Qwen team. We used:

- **Model:** `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` (1.7 billion parameters)
- **Speaker:** "Aiden", one of the model's built-in voices, and the same voice Reachy Mini's conversation app uses
- **Language:** English, with no extra style instructions

### Is it an LLM?

Not in the sense people usually mean. An LLM like ChatGPT or Claude *decides what to say*. This model only decides *how to say* text we give it, word for word.

Under the hood it is built in a similar way: like an LLM, it's a transformer that predicts the next token, one after another. The difference is that its tokens are small chunks of sound (about 12 per second of audio), not words. A separate decoder turns those sound tokens back into a waveform. So it's a language-model-style architecture, put to work as a voice, with no say over the content.

Because it samples its output, each run sounds slightly different, a bit like an actor doing another take. That's exactly why we **generate each clip once, listen to it and freeze it as a WAV file**. On the night, no model runs at all: the robot only plays those files back.

It also can't go off-script even while we're using it. It has no way to add, drop or change words, only to choose how to pronounce them. The worst it can do is mispronounce something, and that's why every clip is checked by a person.

### Methodology

1. Write and approve the script ([`script.md`](script.md)).
2. Generate each clip with [`tools/generate_voice.py`](tools/generate_voice.py), either through the hosted [Qwen3-TTS Space](https://huggingface.co/spaces/Qwen/Qwen3-TTS) or locally on a Mac with `--local`.
3. Listen to every clip. If a word comes out wrong, change its spelling *only in the text sent to the model*, then regenerate. For example, "Ana" is Spanish (AH-na), and the model may say "Anna", so we can send "Ahna" instead. The script itself never changes. (In the end Aiden said "Ana" correctly first time, so no respelling was needed.)
4. Bundle the approved WAVs inside the robot app.

```bash
python3 -m venv .venv
.venv/bin/pip install gradio_client          # hosted Space
.venv/bin/pip install qwen-tts               # optional: run locally
.venv/bin/python tools/generate_voice.py all            # via the Space
.venv/bin/python tools/generate_voice.py all --local    # on your own machine
```

## How the robot app works

*In progress. This section will be updated as the app is built.*

- **Hardware:** Reachy Mini Wireless, which runs apps on its own Raspberry Pi CM4.
- **State machine:** an ordered list of steps. The robot starts asleep, wakes up on the first press, plays one clip per press, and goes back to sleep after the goodbye.
- **Speech with movement:** clips play through the robot's own speaker while its head "wobbles" in time with the audio, so it looks like it's talking. The WAVs are bundled inside the app, so nothing is streamed from elsewhere.
- **Sound in a big room:** the robot's 5 W speaker won't fill a hall of 100 people, so on the night a mic near Reachy or a feed into the venue's sound system boosts it.
- **Phone remote:** a web page served by the robot, with a big NEXT button plus REPEAT, BACK, SKIP TO GOODBYE and STOP.
- **Backup trigger:** tapping one of Reachy's antennas also counts as NEXT, in case the phone loses connection.

## About Science Night Glasgow

<!-- TODO (Ana): a sentence or two about the event and the "Beyond Human" night, plus a link. -->

## Credits

- Robot: [Reachy Mini](https://github.com/pollen-robotics/reachy_mini) by Pollen Robotics and Hugging Face
- Voice: [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice) by the Qwen team
- Game and script: Ana ([@anarojoecheburua](https://github.com/anarojoecheburua))
