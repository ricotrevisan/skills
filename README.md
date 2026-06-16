# skills

A collection of [Claude Code](https://claude.com/claude-code) / agent skills I use and want to share.

Each skill lives in its own directory under [`skills/`](skills/) and contains a `SKILL.md` following the [Agent Skills specification](https://agentskills.io/specification).

## Skills

### [offer-to-cold-email](skills/offer-to-cold-email/SKILL.md)

Turn a service — coaching, agency, consulting, or productized — into punchy front-end offers and short cold emails that actually start conversations.

Adapted from Aaron Shepherd's ([GrowthFlare](https://www.youtube.com/@AaronxShepherd)) video ["Give me 24 min and I'll make your cold emails impossible to ignore"](https://www.youtube.com/watch?v=N5ORVjBPlcg). All credit for the underlying ideas goes to him; this skill simply packages them for reuse.

## Install

To use a skill locally with Claude Code, clone the repo and symlink the skill into your personal skills directory:

```bash
git clone git@github.com:ricotrevisan/skills.git
ln -s "$PWD/skills/skills/offer-to-cold-email" ~/.claude/skills/offer-to-cold-email
```

## License

[MIT](LICENSE)
