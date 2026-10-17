"""Generate Reachy's voice clips from script.md with Qwen3-TTS (Hugging Face Space).

Usage:
    .venv/bin/python tools/generate_voice.py 01_intro          # one clip
    .venv/bin/python tools/generate_voice.py 02_round1 03_reveal1  # several clips
    .venv/bin/python tools/generate_voice.py all               # every clip
    .venv/bin/python tools/generate_voice.py 01_intro --speaker Ryan --out voice/samples
    .venv/bin/python tools/generate_voice.py 03_reveal1 --ana Ahna --suffix _ahna --out voice/samples
"""

import argparse
import re
import shutil
import time
from pathlib import Path

from gradio_client import Client
from huggingface_hub import get_token

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "script.md"

# Respellings applied to the TTS text only; script.md stays unchanged.
# "Ana" is Spanish (AH-na), not "Anna". Aiden already says it correctly, so no
# respelling by default; use --ana Ahna if a future take says "Anna".
RESPELL = {
    r"\bAna\b": "Ana",
}

INSTRUCT = ""


def load_clips():
    clips, current = {}, None
    for line in SCRIPT.read_text().splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            clips[current] = []
        elif current and line.strip() and not line.strip().startswith("("):
            clips[current].append(line.strip())
    return {k: " ".join(v) for k, v in clips.items()}


def tts_text(text):
    for pattern, repl in RESPELL.items():
        text = re.sub(pattern, repl, text)
    # "A." alone can be read as a sentence end; make the option letters clear.
    return re.sub(r"(?<!\w)([A-D])\. ", r"\1: ", text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("clip", nargs="+", help="clip ids (e.g. 01_intro 02_round1) or 'all'")
    p.add_argument("--speaker", default="Aiden")
    p.add_argument("--out", default="voice")
    p.add_argument("--ana", default="Ana", help="TTS spelling of 'Ana' (Ahna = AH-na)")
    p.add_argument("--suffix", default="", help="extra filename suffix, e.g. _ahna")
    p.add_argument("--local", action="store_true", help="run the model on this Mac instead of the Space")
    args = p.parse_args()
    RESPELL[r"\bAna\b"] = args.ana

    clips = load_clips()
    ids = list(clips) if args.clip == ["all"] else args.clip
    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    synth = local_synth() if args.local else space_synth()
    for clip_id in ids:
        text = tts_text(clips[clip_id])
        print(f"{clip_id}: {text}", flush=True)
        suffix = ("" if args.speaker == "Aiden" else f"_{args.speaker}") + args.suffix
        dest = out_dir / f"{clip_id}{suffix}.wav"
        start = time.time()
        synth(text, args.speaker, dest)
        print(f"  -> {dest.relative_to(ROOT)} ({time.time() - start:.0f} s)", flush=True)


def space_synth():
    # Use the local Hugging Face login (if any) for a bigger ZeroGPU quota.
    client = Client("Qwen/Qwen3-TTS", token=get_token())

    def synth(text, speaker, dest):
        audio, _ = client.predict(
            text, "English", speaker, INSTRUCT, "1.7B",
            api_name="/generate_custom_voice",
        )
        shutil.copy(audio, dest)

    return synth


def local_synth():
    # Same model as the Space, run on this Mac (Apple GPU if available).
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", device_map=device, dtype=torch.float32,
    )

    def synth(text, speaker, dest):
        wavs, sr = model.generate_custom_voice(
            text=text, speaker=speaker, language="English", instruct=INSTRUCT or None,
        )
        sf.write(dest, wavs[0], sr, subtype="PCM_16")

    return synth


if __name__ == "__main__":
    main()
