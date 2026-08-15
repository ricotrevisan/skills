---
name: video-analysis
description: Analyze videos and screen recordings. Load whenever the user asks to watch, review, explain, or diagnose a video file; prefer Gemini full-duration video input, distinguish it from client-side frame extraction, and troubleshoot the Gemini path before falling back.
compatibility: Native analysis requires Gemini access. The bundled compact-video fallback requires bash, ffmpeg, python3, and GEMINI_API_KEY.
---

# Video analysis

Treat **full-duration video input** and **client-side frame extraction** as different methods. Gemini samples video internally, so full-duration input does not imply uninterrupted visual fidelity; it means Gemini receives the complete timeline and audio. A contact sheet or `fetch_content` call with `frames` is client-side frame extraction.

## Workflow

1. Resolve the actual video path. A CleanShot path supplied alongside a screenshot may point to the screenshot rather than the recording; inspect the named media directory when necessary.
2. When `fetch_content` is available, send the complete video to Gemini:
   - Use a local `file://` URL or a service the tool supports, such as YouTube. Download a direct remote `.mp4`/`.mov` URL locally first.
   - Set `model` to `gemini-3.6-flash`.
   - Give a prompt asking for chronological observations, timestamps, audio, and the question to answer.
   - Omit `frames` and `timestamp`; either option selects client-side frame extraction.
3. Confirm the result is a model analysis rather than a list of extracted frames. The step is complete when Gemini returns a temporal account that answers the user's question.
4. If `fetch_content` is unavailable or reports that Gemini access is missing, check whether `GEMINI_API_KEY` is present without printing its value. Tool auth can fail even while the direct API works.
5. When the environment key exists, resolve [`scripts/gemini-video`](scripts/gemini-video) relative to this `SKILL.md` and run it with the source video and analysis prompt. It submits a compact, full-duration copy—including audio—to Gemini; larger copies use Gemini's Files API:

   ```bash
   "/path/to/video-analysis/scripts/gemini-video" "/path/to/video.mp4" \
     "Describe the bug chronologically with timestamps and root-cause clues."
   ```

6. Use extracted frames only when both Gemini routes fail. Sample densely enough for the task and explicitly label the result as frame-based.

## Reporting

Always name the method used:

- **Gemini full-duration video analysis** — the full timeline was submitted to Gemini.
- **Gemini compact full-duration analysis** — the full timeline was transcoded before submission; disclose the fallback frame rate/resolution when motion fidelity matters.
- **Frame sampling** — only selected stills were inspected.

Keep observations separate from inference. Never claim Gemini watched a recording when the tool only returned extracted frames.

## Credential safety

Read `GEMINI_API_KEY` from the environment. Never print it, write it into the skill, include it in a URL, or commit it. If the key is absent, ask the user to inject it through their existing secret-management setup or authenticate the supported browser-cookie route.
