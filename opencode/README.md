# opencode/

Tool configuration, one directory per tool, named after the tool.

`opencode.jsonc` is the global opencode config: providers, models, MCP
servers, permissions, keybinds.

Linked by the `config` target:

```yaml
targets:
  opencode:
    config: ~/.config/opencode/opencode.jsonc
```

The source file is looked up as `<tool>/<the target's filename>`, so a
`claude.config` target pointing at `~/.claude/settings.json` would read
`claude/settings.json`.

## Gitignored

`opencode.jsonc` is **not** committed. A personal config tends to name
internal hosts, services, and API providers, and this repo is public. The repo
owns the symlink; the content stays on the machine.

That means a fresh clone has no config until you supply one. Keep a copy
somewhere private if you want it reproducible.

## Not the repo's own config

`config.yaml` at the repo root configures *this repo* — the owner prefix,
targets, and remote sources. This directory holds a config file that is
merely shipped somewhere else, like every other artefact directory here.

## Rules live elsewhere

`instructions` in `opencode.jsonc` is intentionally empty. Global rules come
from `rules/AGENTS.md` instead, which opencode loads automatically. Add
entries here only for extra always-on instruction files.
