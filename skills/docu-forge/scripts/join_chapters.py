#!/usr/bin/env python3
"""Join chapter films into one long video, with one loudness pass and a merged SRT.

  python3 join_chapters.py --out final/film.mp4 ch01/out/final.mp4 ch02/out/final.mp4 ...
  python3 join_chapters.py --out final/film.mp4 --srt final/film.srt ch01/out/final.mp4:ch01/out/captions.srt ...

Every input is conformed to one spec (size/fps/48k stereo AAC) so code-rendered
chapters and AI clips (which may be silent) concat cleanly.
"""
import argparse, json, os, re, subprocess, sys, tempfile


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    return float(j["format"]["duration"]), any(s["codec_type"] == "audio" for s in j["streams"])


def ts(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def parse_ts(s):
    h, m, rest = s.strip().split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def merge_srt(parts):
    """parts: [(srt_text or None, offset_seconds)] -> one renumbered SRT."""
    rows, rx = [], re.compile(r"(\S+) --> (\S+)\n(.*)", re.S)
    for text, off in parts:
        for block in (text or "").strip().split("\n\n"):
            lines = block.strip().split("\n", 1)
            if len(lines) < 2 or not (m := rx.match(lines[1])):
                continue
            a, b, body = m.groups()
            rows.append(f"{ts(parse_ts(a) + off)} --> {ts(parse_ts(b) + off)}\n{body.strip()}")
    return "\n\n".join(f"{i}\n{r}" for i, r in enumerate(rows, 1)) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="video[:captions.srt] in order")
    ap.add_argument("--out", required=True)
    ap.add_argument("--srt", default="")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--lufs", type=float, default=-14.0, help="YouTube normalises to -14")
    a = ap.parse_args()
    w, h = a.size.split("x")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="join_")
    parts, srts, offset = [], [], 0.0
    for i, spec in enumerate(a.inputs):
        video, _, srt = spec.partition(":")
        dur, has_audio = probe(video)
        part = os.path.join(tmp, f"p{i:03}.mp4")
        # ponytail: always re-encode each part; skip-if-matching is an optimisation, add if join time hurts.
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", video]
        if not has_audio:
            cmd += ["-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=48000:cl=stereo"]
        cmd += ["-map", "0:v:0", "-map", "0:a:0" if has_audio else "1:a:0",
                "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={a.fps},setsar=1,format=yuv420p",
                "-c:v", "libx264", "-crf", str(a.crf), "-preset", "medium",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{dur}", part]
        subprocess.run(cmd, check=True)
        parts.append(part)
        srts.append((open(srt).read() if srt else None, offset))
        print(f"[{i + 1}/{len(a.inputs)}] {video}  {dur:.1f}s  @ {ts(offset)}")
        offset += probe(part)[0]
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    joined = os.path.join(tmp, "joined.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", joined, "-c:v", "copy",
                    "-af", f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", a.out], check=True)
    if a.srt:
        with open(a.srt, "w") as f:
            f.write(merge_srt(srts))
        print(f"srt: {a.srt}")
    print(f"done: {a.out}  {ts(probe(a.out)[0])}")


def _selfcheck():
    s = "1\n00:00:01,000 --> 00:00:02,500\nhello\n\n2\n00:00:03,000 --> 00:00:04,000\nworld\n"
    m = merge_srt([(s, 0), (None, 5), (s, 65.25)])
    assert m.count("-->") == 4, m
    assert "00:01:06,250 --> 00:01:07,750\nhello" in m and m.startswith("1\n") and "\n4\n" in m, m
    assert parse_ts(ts(3723.456)) == 3723.456


if __name__ == "__main__":
    if sys.argv[1:] == ["--selfcheck"]:
        _selfcheck(); print("ok")
    else:
        main()
