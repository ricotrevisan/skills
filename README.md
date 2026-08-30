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

### [bubble-plugin-development](skills/bubble-plugin-development/SKILL.md)

Workflow for Bubble.io plugin repos that use Pled (plugin source sync) and Buildprint (dev app): the two-code-piles layout, the Pled pull/push/watch loop, runtime bundle releases, Buildprint branching, and how to verify changes against the real Bubble UI. Plugin-specific facts stay in each repo's `AGENTS.md`.

## Matt Pocock's skills

Vendored from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), promoted `engineering` and `productivity` buckets:

[ask-matt](skills/ask-matt/SKILL.md), [code-review](skills/code-review/SKILL.md), [codebase-design](skills/codebase-design/SKILL.md), [diagnosing-bugs](skills/diagnosing-bugs/SKILL.md), [domain-modeling](skills/domain-modeling/SKILL.md), [grill-me](skills/grill-me/SKILL.md), [grill-with-docs](skills/grill-with-docs/SKILL.md), [grilling](skills/grilling/SKILL.md), [handoff](skills/handoff/SKILL.md), [implement](skills/implement/SKILL.md), [improve-codebase-architecture](skills/improve-codebase-architecture/SKILL.md), [prototype](skills/prototype/SKILL.md), [research](skills/research/SKILL.md), [resolving-merge-conflicts](skills/resolving-merge-conflicts/SKILL.md), [setup-matt-pocock-skills](skills/setup-matt-pocock-skills/SKILL.md), [tdd](skills/tdd/SKILL.md), [teach](skills/teach/SKILL.md), [to-questionnaire](skills/to-questionnaire/SKILL.md), [to-spec](skills/to-spec/SKILL.md), [to-tickets](skills/to-tickets/SKILL.md), [triage](skills/triage/SKILL.md), [wait-what](skills/wait-what/SKILL.md), [wayfinder](skills/wayfinder/SKILL.md), [wizard](skills/wizard/SKILL.md), [writing-for-agents](skills/writing-for-agents/SKILL.md)

## Install

Clone the repo, then symlink every skill into the directories your agent clients load:

```bash
git clone git@github.com:ricotrevisan/skills.git
cd skills

# shared agent skill dir (opencode loads this automatically; Claude Code can too)
mkdir -p ~/.agents/skills
for d in skills/*/; do ln -sfn "$PWD/$d" ~/.agents/skills/"$(basename "$d")"; done

# Claude Code (optional if it already reads ~/.agents/skills)
mkdir -p ~/.claude/skills
for d in skills/*/; do ln -sfn "$PWD/$d" ~/.claude/skills/"$(basename "$d")"; done
```

## License

[MIT](LICENSE)
