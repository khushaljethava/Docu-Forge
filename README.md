# Docu-Forge

A Claude Code skill for **long narrated videos** (5 to 30+ minutes): documentaries, true crime, history, Vox-style explainers and YouTube video essays.

- **Code-rendered engine** (Skia + Python): one camera moves across a board of photos, documents, maps and big numbers, and every highlight lands on the narrator's word. Sound effects are synthesised and captions are burned in. Free, and the same output every run.
- **Optional AI inserts**: editorial paper-collage B-roll (Seedream keyframes, then image-to-video via Atlas Cloud), used only where no real image exists.
- **Chapters**: each chapter renders and gets checked on its own, then `join_chapters.py` stitches them into one film with normalised loudness and a merged SRT.

## Install

In Claude Code:

```
/plugin marketplace add khushaljethava/Docu-Forge
/plugin install docu-forge@docu-forge
```

Or copy it by hand:

```bash
git clone https://github.com/khushaljethava/Docu-Forge
cp -r Docu-Forge/skills/docu-forge ~/.claude/skills/
```

Then install the dependencies:

```bash
pip install -r requirements.txt   # plus ffmpeg on PATH
```

AI inserts also need `ATLASCLOUD_API_KEY`.

## Use

Ask Claude something like:

> Make a 20 minute documentary about the Great Molasses Flood of 1919, evidence-board style.

The skill writes an outline and chapter scripts, and stops for your approval at each gate (outline, facts, look, draft, AI spend) before rendering.

## Credits

Built by merging two MIT-licensed skills:

- [cinematic-skill](https://github.com/Moh4696/cinematic-skill) by exploraX: the film engine, scripts and references
- [vox-explainer-skill](https://github.com/CK42BB/vox-explainer-skill) by Kingsley: the Vox writing and visual style guide, the Atlas Cloud pipeline and the ffmpeg recipes

Docu-Forge adds the chapter workflow for long films, `join_chapters.py`, and the merged guidance.
