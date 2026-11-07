---
name: video-analysis
description: Watch, review, explain, or diagnose a video or screen recording, including YouTube links.
compatibility: Scripts need bash, ffmpeg, python3, and op or the keys below. YouTube fetches run over `ssh office` (uv, deno, ffmpeg there).
---

# Video analysis

Read before you watch. Words are cheap and exact; watching costs time and money and models misread screens. Watch only the spans the question needs.

Scripts live in [`scripts/`](scripts/) next to this file; each has `--help`.

## YouTube and other online videos

1. **Captions.** `scripts/yt-fetch captions URL DIR` writes `DIR/meta.txt` (title, channel, length) and `DIR/transcript.txt` (`[mm:ss] text`). Done when the transcript exists. If the video has no captions, go to step 3 for the whole video.
2. **Decide what to watch.** Answer from the transcript alone when the question is about what is said (the argument, the advice, "is this worth my time"). Mark spans to watch when either holds:
   - the question is visual: UI, layout, design, code on screen, a demo, a bug;
   - near the relevant part the speaker points at the screen. Find those spans with
     `grep -n -i -E "you can see|look at|right here|over here|this one|let me show|I'll show|watch this" DIR/transcript.txt`.
   Done when every part of the question is either answered from the transcript or tied to a time range.
3. **Watch.** Whole video: `scripts/gemini-video URL "PROMPT"` (Gemini fetches YouTube itself). Spans: `scripts/yt-fetch video URL DIR`, then cut each one with `ffmpeg -v error -ss 10:35 -to 11:15 -i DIR/video.mp4 -c copy DIR/clip-1.mp4` and pass the clip to `scripts/gemini-video`. Pad spans by ~10 s on each side.
4. If `gemini-video` exits 3 (every Gemini model overloaded), send the same clips to `scripts/opencode-video`.

`yt-fetch` runs yt-dlp on `office` because YouTube asks datacenter IPs (lab, hetzner) to sign in. Set `VIDEO_FETCH_HOST=openclaw` if office is down. Both share the home IP, so fetch one video at a time and only what you need.

## Local recordings

Screen recordings usually have no speech, so watch them directly: `scripts/gemini-video PATH "PROMPT"`, then `scripts/opencode-video PATH "PROMPT"` on exit 3. A CleanShot path given with a screenshot may point at the screenshot; check the media folder for the recording.

## Prompts

Ask for chronological observations with `mm:ss` timestamps, what is said, and the user's question. Ask the model to separate what it sees from what it infers. For a clip, say where it starts in the full video so its timestamps can be mapped back.

## Fallbacks and keys

| Route | Script | Key |
|---|---|---|
| Gemini 3.6 → 3.8 → 3.7 Flash, one retry each on 429/5xx | `gemini-video` | `GEMINI_API_KEY`, else 1Password `op://Dev/tuisdffrgbcrrxzpnhyxjlm6oa/API keys/Gemini` |
| Qwen 3.8 Flash on OpenCode Go (~$0.03 for 24 min) | `opencode-video` | `OPENCODE_API_KEY`, else `op://Dev/Opencode/api_keys/video-analysis` |
| Frame sampling | ffmpeg stills you inspect | none |

Use frame sampling only when both models fail, and sample densely enough for the task. Never print or commit a key.

## Reporting

Name the method: **Captions only**, **Gemini (YouTube URL)**, **Gemini compact video** (say which clips), **Qwen via OpenCode Go** (say which clips), or **Frame sampling**. Keep observations separate from inference, and give timestamps in the full video's time.
