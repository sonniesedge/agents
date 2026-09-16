# settings/

Tool configuration files, one subdirectory per tool.

```
settings/opencode/opencode.jsonc   -> ~/.config/opencode/opencode.jsonc
settings/claude/settings.json      -> ~/.claude/settings.json
```

Linked by a tool's `config` target:

```yaml
targets:
  opencode:
    config: ~/.config/opencode/opencode.jsonc
```

The source is looked up as `settings/<tool>/<the target's filename>`, where
`<tool>` is the key under `targets`.

## Why a subdirectory per tool

Tool config filenames are generic — `settings.json`, `config.toml`,
`config.json` — so a flat directory would collide as soon as a second tool
appeared. The subdirectory keeps them apart and makes the owner obvious.

It also gives each tool somewhere to keep related files that are not
themselves linked out.

## Contents are gitignored

Everything here except `README.md` is ignored. Tool configs tend to name
internal hosts, services, and API providers, and this repo is public. The repo
owns the symlink; the content stays on the machine.

A fresh clone therefore has no tool config until you supply one. Keep a copy
somewhere private if you want it reproducible.

## Not the repo's own config

`config.yaml` at the repo root configures *this repo* — the owner prefix,
targets, and remote sources. This directory holds config belonging to other
tools, shipped out like every other artefact here.
