#!/usr/bin/env python3
"""Voice every take with Deepgram Flux TTS: realistic Hindi (default voice Rajesh, expressivity 1).

  export DEEPGRAM_API_KEY=...                       # or pass --key
  python3 tts_deepgram.py --project ch01                           # flux-rajesh-hi, expressivity 1
  python3 tts_deepgram.py --project ch01 --only T02_case           # re-record one take
  python3 tts_deepgram.py --project ch01 --voice flux-anjali-hi --expressivity 0 --speed 0.95

Hindi voices: male ajay arjun nikhil rahul rajesh vikram; female anjali divya jyoti pallavi prachi
ritu shreya sunita (as flux-<name>-hi). Expressivity -2 (calm) .. 2 (animated), whole numbers.
Speed 0.5-1.5. A take or line can override both: {"id": 8, "spoken": "...", "expressivity": 2}.

One call per LINE (same voice, same settings), joined into audio/takes/<take>.wav with a fixed
pause. The joins are known exactly, so cut points go to audio/overrides.json and split_takes.py
cuts on them instead of guessing. Then run split_takes.py and build_narration.py as usual.
"""
import argparse
import io
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import wave

URL = "https://api.deepgram.com/v2/speak"
SR = 48000


def cut_points(durations, pause):
    """Seconds into the take where each line after the first starts: middle of the pause before it."""
    out, t = [], 0.0
    for d in durations[:-1]:
        t += d
        out.append(round(t + pause / 2, 3))
        t += pause
    return out


def speak(text, key, voice, expressivity, speed):
    """Return raw 16-bit mono PCM at SR for one line."""
    q = {"model": voice, "encoding": "linear16", "container": "wav", "sample_rate": SR,
         "expressivity": int(expressivity)}
    if speed != 1.0:
        q["speed"] = speed
    req = urllib.request.Request(f"{URL}?{urllib.parse.urlencode(q)}", data=json.dumps({"text": text}).encode(),
                                 headers={"Authorization": f"Token {key}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt * 2); continue
            sys.exit(f"Deepgram HTTP {e.code}: {body}")
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(2 ** attempt * 2); continue
            sys.exit(f"Deepgram unreachable: {e}")
    with wave.open(io.BytesIO(data)) as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, SR):
            sys.exit(f"unexpected audio format {w.getparams()}")
        return w.readframes(w.getnframes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--key", default=os.environ.get("DEEPGRAM_API_KEY"), help="default: $DEEPGRAM_API_KEY")
    ap.add_argument("--voice", default="flux-rajesh-hi")
    ap.add_argument("--expressivity", type=int, default=1, choices=[-2, -1, 0, 1, 2])
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--pause", type=float, default=0.65, help="silence between lines in a take (s)")
    ap.add_argument("--only", default="", help="comma-separated take names to (re)record")
    a = ap.parse_args()
    if not a.key:
        sys.exit("no API key: export DEEPGRAM_API_KEY=... or pass --key")

    proj = pathlib.Path(a.project)
    script = json.loads((proj / "script.json").read_text())
    tdir = proj / "audio" / "takes"; tdir.mkdir(parents=True, exist_ok=True)
    ov_path = proj / "audio" / "overrides.json"
    ov = json.loads(ov_path.read_text()) if ov_path.exists() else {}
    cut_before = ov.setdefault("cut_before", {})
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    gap = b"\0\0" * int(a.pause * SR)

    for take in script["takes"]:
        name = take["take"]
        if only and name not in only:
            continue
        parts, durs = [], []
        for line in take["lines"]:
            ex = line.get("expressivity", take.get("expressivity", a.expressivity))
            sp = line.get("speed", take.get("speed", a.speed))
            pcm = speak(line["spoken"].strip(), a.key, a.voice, ex, sp)
            d = len(pcm) / 2 / SR
            print(f"  {line['id']:>3} ex={ex:+d} {d:5.1f}s  {line['spoken'][:50]}", flush=True)
            parts += [pcm, gap]; durs.append(d)
        out = tdir / f"{name}.wav"
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(b"".join(parts[:-1]))
        for line, t in zip(take["lines"][1:], cut_points(durs, a.pause)):
            cut_before[str(line["id"])] = t
        print(f"{name:<20} {len(durs)} lines  {sum(durs) + a.pause * (len(durs) - 1):5.1f}s  -> {out}")
    ov_path.write_text(json.dumps(ov, indent=1))
    print(f"cut points -> {ov_path}\nnext: split_takes.py, then build_narration.py")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selfcheck"]:
        assert cut_points([2.0, 3.0, 1.0], 0.5) == [2.25, 5.75], cut_points([2.0, 3.0, 1.0], 0.5)
        print("ok")
    else:
        main()
