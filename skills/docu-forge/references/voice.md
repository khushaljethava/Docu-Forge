# Voice

The film is timed to the voice, so the voice comes before the picture. Use a free scratch voice to build against, then swap in the final one. The scene asks for line starts and spoken words, never fixed seconds, so it re-times itself.

## Scratch voice

```bash
python3 scripts/tts_say.py --project my-film                         # macOS say, or espeak-ng on Linux
python3 scripts/tts_say.py --project my-film --voice Daniel --rate 165
```

It reads each take in one go, with a clear pause between lines, and writes `audio/takes/<take>.wav`.

## Final voice: any provider

Record **one take per section**, not one call per line. One call keeps the delivery even. Per-line calls change pace and pitch from line to line, which sounds stitched together.

- **A command-line TTS** (Piper, a provider's CLI, your own script): `tts_say.py --cmd 'tool --in {txt} --out {out}'`. `{txt}` is a file with the take's lines, one paragraph each.
- **An API or app** (ElevenLabs, OpenAI, Higgsfield, PlayHT): send each take's `spoken` lines joined with a paragraph break (or the provider's pause tag), and save the result as `audio/takes/<take>.wav`. Any format ffmpeg reads is fine.
- **A person**: one file per take, a beat of silence between lines.

Then:

```bash
python3 scripts/split_takes.py --project my-film
python3 scripts/build_narration.py --project my-film                 # natural read
python3 scripts/build_narration.py --project my-film --target 88     # fit to 88 s (0.90 to 1.15x only)
```

## Hindi final voice: Deepgram Flux (default)

`scripts/tts_deepgram.py` uses Deepgram Flux TTS (`POST /v2/speak`). The default is **`flux-rajesh-hi`** (Rajesh, male Hindi) at **expressivity 1**.

```bash
export DEEPGRAM_API_KEY=...            # never commit it; or pass --key
python3 scripts/tts_deepgram.py --project ch01                    # Rajesh, expressivity 1
python3 scripts/tts_deepgram.py --project ch01 --only T02_case    # re-record one take
python3 scripts/split_takes.py --project ch01 && python3 scripts/build_narration.py --project ch01
```

- Write `spoken` in Devanagari. Deepgram normalises numbers and dates in Hindi, but words are safer for names and years.
- **Expressivity** ranges from `-2` (calm) to `2` (animated), whole numbers only. Keep `1` for the film. Override it on a take or a line with `"expressivity": 2` only for a real peak.
- **Speed** ranges from 0.5 to 1.5 (`--speed`, or `"speed"` on a take or line). Prefer `build_narration.py --target` for fitting the length.
- It makes one call per line with the same voice and settings. The script writes exact cut points to `audio/overrides.json`, so `split_takes.py` doesn't guess.
- Other Hindi voices: `ajay arjun nikhil rahul vikram` (male), `anjali divya jyoti pallavi prachi ritu shreya sunita` (female), as `flux-<name>-hi`. Use one voice for the whole film.

## Checking the split

`split_takes.py` measures every line's speaking rate in letters per second of actual speech, and flags lines more than 35% off the median. A flag nearly always means one of three things:

- **Two lines run together.** The voice did not pause, so the cut landed a sentence late. Force the boundary in `audio/overrides.json`: `{"cut_before": {"53": 26.80}}`, the line id and the seconds into its take where that line starts. Find the spot by listening, or with `ffmpeg -i take.wav -af silencedetect=noise=-40dB:d=0.1 -f null -`.
- **A dramatic pause inside a line** ("He was... thirty-two") got taken for a boundary. Force the real one the same way.
- **A dropped or doubled word.** Re-record that take.

Listen to every flagged line. A cut in the wrong place shifts every visual hit after it.

## Re-recording

Re-record a whole take, never a single line: one line patched in from another call stands out. After any change, run `split_takes.py` and `build_narration.py` again, then `render.py --probe` on the affected lines. If a line got noticeably longer, check its camera keys still have time.

## Delivery notes

- Ask for a measured documentary read. A pace of 150 to 170 words a minute suits these films.
- Numbers and names go in `spoken` exactly as they should be said.
- A tempo fit beyond 0.90 to 1.15x sounds wrong. `build_narration.py` refuses it: cut or add lines instead.
- The narration lands at -16 LUFS. `mix_soundtrack.py` sets the final loudness.
