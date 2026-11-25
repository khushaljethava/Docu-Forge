---
name: docu-forge
description: Makes long narrated videos (5 to 30+ minutes) — documentaries, true crime, history, Vox-style explainers, video essays, YouTube long-form — by merging two pipelines. The backbone is a code-rendered cinematic engine (Skia/Python; one camera gliding over a board of photos, documents, maps, big numbers, every hit landing on the narrator's word, synthesised SFX, burned captions). Optional AI inserts in the Vox editorial-collage style (Seedream keyframes → image-to-video via Atlas Cloud) add illustrated B-roll where no real images exist. The film is split into chapters, each rendered and checked on its own, then joined into one video with a merged SRT. Use for "make a long video about", "20 minute documentary", "YouTube documentary", "video essay", "Vox-style explainer", "true crime video", "evidence board video", or any narrated video longer than a short.
---

# Docu-Forge

Two pipelines, one film:

- **Engine (default, free, deterministic).** From cinematic-film: one camera move over one designed world, every visual hit timed to a spoken word. Covers ~90% of a long film.
- **AI inserts (optional, paid).** From vox-explainer: a style-anchored Seedream keyframe animated by an image-to-video model, in the editorial paper-collage look. Use for illustration only, where no real photo exists (rule 7).

A long film is **chapters**. Each chapter is its own engine project (2–6 min), so each fits in memory, renders in parallel, can be re-cut alone, and can change look. `scripts/join_chapters.py` stitches them.

All script paths below are relative to this skill's folder (`~/.claude/skills/docu-forge/`). All engine commands take `--project <folder>`.

## Tools

| File | What it does |
| --- | --- |
| `scripts/check_setup.py` | Checks Python, skia-python, ffmpeg, fonts, memory |
| `scripts/get_fonts.py` | Fetches open-licensed fonts (run per project on Linux) |
| `scripts/new_project.py` | New chapter from `assets/template/` (or `--example` documentary) |
| `scripts/make_beats.py` | Writes `beats.md`; lints chronology, line length, digits in spoken text |
| `scripts/tts_say.py` | Scratch voice (espeak-ng / say / any TTS command) |
| `scripts/split_takes.py` | Cuts section takes into one clip per line, flags bad cuts |
| `scripts/build_narration.py` | `audio/narration.m4a` + `audio/timing.json` — the master clock |
| `scripts/fetch_commons.py` | Wikimedia Commons search/download with licences → `credits.md` |
| `scripts/make_map.py` | Public-domain boundary maps |
| `scripts/prep_assets.py` | Grades all images into one look; board textures |
| `scripts/engine.py` | Camera, spotlight, items, maps, looks, film finish |
| `scripts/render.py` | `--probe` stills, `--strip` contact sheets, `--cues`, parallel MP4 render |
| `scripts/build_sfx.py` | Synthesises SFX from the cue list |
| `scripts/mix_soundtrack.py` | Voice + SFX + optional music, ducked, loudness-normalised |
| `scripts/burn_captions.py` | Burns captions (`highlighter`/`clean`/`paper`/`redbar`), `--srt-only` for SRT |
| `scripts/join_chapters.py` | **New.** Conforms + joins chapters and AI inserts, one loudnorm pass, merged SRT |

Engine needs Python 3.9+, `pip install skia-python numpy pillow`, ffmpeg. AI inserts also need `requests` and `ATLASCLOUD_API_KEY`.

## Layout

```
film/
├── brief.md              # topic, angle, target length, audience, platform
├── outline.md            # chapter list with target minutes + throughline
├── voice.md              # the ONE voice/TTS settings used for every chapter
├── ch01_cold-open/       # engine project (new_project.py)
├── ch02_.../
├── inserts/              # AI clips: frames/, clips/, prompts.log
│   └── style_anchor.png
└── final/                # film.mp4, film.srt, credits.md, preview.mp4
```

## Pick the look

| Kind | Engine look | Images | AI inserts? |
| --- | --- | --- | --- |
| History, true crime, investigation | `wall`, `slate` | Archive photos/docs, `bw` | Rare — recreations of places, never people/events as evidence |
| Vox-style explainer, video essay | `paper`, `studio` | Mixed archive + diagrams | Yes — collage interstitials and chapter title cards |
| Science, how it works | `blueprint`, `paper` | Diagrams | Yes — processes with no photos |
| Product, brand, founder | `studio`, `charcoal` | Your own shots, `natural` | Sometimes |
| Tech, space, trailers | `night` | Screenshots, renders | Yes |

Keep ONE look per film, or one per act at most. A long film changing board every chapter feels like a playlist.

## The rules

1. **One hero per line.** One thing on screen per narration line; the spotlight dims the rest.
2. **Hits land on the spoken word.** Time with `doc.W(line, "word")`, never the line start.
3. **Show a phrase one way.** Typed on screen or on a real document, never both.
4. **Time only moves forward after the cold open** (one bridge line allowed).
5. **Phone-readable type.** Big condensed caps, ≥3% frame height.
6. **Less is more.** Strings fade, old items dim, pull-backs stay composed.
7. **Nothing invented that looks real.** Real images get credits; code-drawn documents are labelled recreations; AI images illustrate, never evidence a real event or person. For true crime this is strict: no AI faces of victims, suspects or real people.
8. **One voice, one accent colour, one style anchor for the whole film.** Across chapters, nothing drifts.
9. **AI motion is subtle.** Slow 2D push-in, layer parallax, one living element. Forbid in every prompt: camera shake, 3D rotation, face/text morphing, style drift.

## Long-film writing

Use `references/story.md` (shapes per kind) plus `references/vox/vox-style-guide.md` (Vox arc, sentence rules). Budget at ~150 wpm:

| Length | Chapters | Words |
| --- | --- | --- |
| 5 min | 2–3 | ~750 |
| 10 min | 4–5 | ~1,500 |
| 20 min | 6–9 | ~3,000 |
| 30 min | 9–12 | ~4,500 |

- **Whole film:** cold open (hook, ≤45 s) → "to understand this, you have to go back…" → escalating chapters on one throughline → complication → resolution that reframes the hook. Last line quotable.
- **Each chapter** is a mini-arc: opens on a question, ends on a turn that pulls into the next. Retention dips at chapter seams; put the hook there, not a recap.
- **Every 60–90 s, change something:** a new map, a number, a document, an insert, a pull-back. Long films die from sameness.
- Numbers spoken as words in `spoken`; present tense for history; concrete over abstract; vary rhythm.

## Workflow

Stop at each **Gate** for the user's approval.

1. **Brief + outline.** Research, write `brief.md` and `outline.md` (chapters, minutes, the throughline, where inserts go). **Gate:** outline approved.
2. **Chapter scripts.** `new_project.py chNN_name` per chapter; write each `script.json` (takes → lines with `text`, `spoken`, `hero`, `typed`, plus `fact_notes` with sources). Run `make_beats.py` per chapter, fix every lint. **Gate:** user approves all `beats.md` including facts.
3. **Images.** Per chapter `photos.json`; `fetch_commons.py` for archives, user files in `<chapter>/assets/photos/`. `references/archive.md` for rights. List every beat with no usable image → insert candidates.
4. **Scratch voice, all chapters.** `tts_say.py` → `split_takes.py` → `build_narration.py`. Listen to every flagged line. Sum the runtimes and check against the brief; tighten scripts now, not later.
5. **AI inserts (optional).** Read `references/vox/atlas-cloud-api.md` and the Visual Grammar part of `references/vox/vox-style-guide.md`. Verify endpoints/model IDs on atlascloud.ai/docs first.
   - Quote cost first: `inserts × (~$0.10 image + ~$0.11/s video)`. **Gate:** user approves spend.
   - Make `inserts/style_anchor.png` (text-to-image), regenerate until right. **Gate:** anchor approved.
   - Remaining frames via the edit model with the anchor as reference; animate all concurrently, poll, download to `inserts/clips/`. Log every prompt + response to `inserts/prompts.log`. Budget ~15% regens.
   - An insert's narration either lives in the adjacent engine chapter (insert is silent B-roll between chapters, kept ≤ 8 s) or is its own beat: generate its VO, conform the clip to VO + 0.5 s with `references/vox/ffmpeg-assembly.md` §1, mux VO on.
   - Alternatively place a still keyframe inside the engine as a photo item in `photos.json` (`"kind": "color"` to keep its palette, `"what"` noting "AI illustration" for `credits.md`) — cheapest and keeps the camera continuous.
6. **Assets + scenes.** Per chapter: `make_map.py` if it travels, `prep_assets.py`, then `scene.py` (read `references/film.md`; patterns in `assets/template/scene.py` and `assets/wright-flyer/scene.py`).
7. **Look test.** `render.py --probe` one still per line at 1280x720 and look at every one; `--strip` every big camera move. **Gate:** stills of the cold open, one mid chapter and any insert.
8. **Draft.** Render chapter 1 fully at 1280x720 with scratch voice, plus 30 s of each other chapter. **Gate:** user watches.
9. **Final voice.** Record every chapter with the settings in `voice.md` (`references/voice.md`). Re-run split/build/probes; scenes re-time themselves.
10. **Sound per chapter.** `render.py --cues` → `build_sfx.py` → `mix_soundtrack.py` (`references/sound.md`). For a film-wide score, one bed per act; never a mid-track drop on a quiet beat.
11. **Render per chapter.** Final size (`references/performance.md`: YouTube → 2560x1440, X → 1920x1080). Chapters are independent; render them one after another with full workers, or in parallel with `--workers` split so total memory fits.
    ```bash
    python3 scripts/render.py --project ch01 --size 2560x1440 --out out/final.mp4 --audio audio/mix.m4a
    python3 scripts/burn_captions.py --project ch01 --srt-only --out out/captions.srt
    ```
12. **Join.**
    ```bash
    python3 scripts/join_chapters.py --size 2560x1440 --out film/final/film.mp4 --srt film/final/film.srt \
      film/ch01/out/final.mp4:film/ch01/out/captions.srt \
      film/inserts/clips/i01.mp4 \
      film/ch02/out/final.mp4:film/ch02/out/captions.srt
    ```
    Deliver the clean `film.mp4` + `film.srt` for YouTube; for muted-autoplay platforms burn captions per chapter (`burn_captions.py --video ... --style highlighter`) before joining. Make a phone preview: `ffmpeg -i film.mp4 -vf scale=960:-2 -crf 28 preview.mp4`. Merge every chapter's `credits.md` into `final/credits.md`. List chapter start times (printed by the join) as YouTube chapter timestamps.

## Self-review, every time

Look at stills and the joined film before claiming it works.

- Dark ink on a dark board → light type or `bar_h=0.92`.
- Camera moved, spotlight stayed → use `film.shot()`.
- Map scale too small; labels colliding; clusters straddling map edges.
- Highlights off their words → `PaperDoc.phrase_spans`, `doc.on(print, fx, fy)`.
- AI inserts: warped text, faces animating, style drift from the anchor, visible motion loops → regenerate at the insert stage.
- Join: chapter seams have no audio pop or level jump; captions stay in sync at the last chapter (drift = wrong offset); duration equals sum of parts ±0.2 s; no black frames at seams.
- Pacing over the long run: scrub the whole film at 4x. If any 90 s looks the same, add a change.

## References

- `references/story.md`, `film.md`, `voice.md`, `sound.md`, `archive.md`, `performance.md` — engine (cinematic-film).
- `references/vox/vox-style-guide.md` — Vox writing arc + collage visual grammar + prompt templates.
- `references/vox/atlas-cloud-api.md` — AI insert models, async pattern, costs.
- `references/vox/ffmpeg-assembly.md` — conform, concat, ducking, ASS subtitles.
- `LICENSES.md` — both upstream skills are MIT.
