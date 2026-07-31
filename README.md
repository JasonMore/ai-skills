# AI Skills

Personal AI agent skills. This repository is the source of truth for skills installed in `~/.copilot/skills/`.

## Install

```bash
./install
```

The installer symlinks each directory under `skills/` into `~/.copilot/skills/`. It preserves skills from other sources unless they use the same name.

## Add or update a skill

1. Create or edit the skill under `skills/`.
2. Run its tests and validation.
3. Run `./install` to refresh local links.
4. Commit and push the change to GitHub.
