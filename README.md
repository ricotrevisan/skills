# skills

A collection of [Claude Code](https://claude.com/claude-code) / agent skills I use and want to share.

Each skill lives in its own directory under [`skills/`](skills/) and contains a `SKILL.md` following the [Agent Skills specification](https://agentskills.io/specification).

## Skills

### [video-analysis](skills/video-analysis/SKILL.md)

Watch, review, or diagnose videos with Gemini full-duration video input. Distinguishes model video input from client-side frame extraction and includes a compact full-video fallback when the normal Gemini tool path fails.

### [tidewave](skills/tidewave/SKILL.md)

Use the [Tidewave](https://tidewave.ai) MCP tools (v0.8+) against a running Phoenix dev server without the trial-and-error: help-first `browser_eval`, no guessed tool names, and a triage table for the common failure states. Distilled from real agent sessions where every one of these mistakes was made at least once.

### [offer-to-cold-email](skills/offer-to-cold-email/SKILL.md)

Turn a service — coaching, agency, consulting, or productized — into punchy front-end offers and short cold emails that actually start conversations.

Adapted from Aaron Shepherd's ([GrowthFlare](https://www.youtube.com/@AaronxShepherd)) video ["Give me 24 min and I'll make your cold emails impossible to ignore"](https://www.youtube.com/watch?v=N5ORVjBPlcg). All credit for the underlying ideas goes to him; this skill simply packages them for reuse.

## Install

Clone the repo, then symlink a skill into the directory your agent client loads:

```bash
git clone git@github.com:ricotrevisan/skills.git
cd skills

# pi and shared agent clients
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/video-analysis" ~/.agents/skills/video-analysis

# Claude Code
mkdir -p ~/.claude/skills
ln -s "$PWD/skills/offer-to-cold-email" ~/.claude/skills/offer-to-cold-email
```

## License

[MIT](LICENSE)
