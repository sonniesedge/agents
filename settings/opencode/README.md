# settings/opencode/

`opencode.jsonc` — the global opencode config: providers, models, MCP
servers, permissions, keybinds.

Linked by:

```yaml
targets:
  opencode:
    config: ~/.config/opencode/opencode.jsonc
```

## Gitignored

`opencode.jsonc` is **not** committed — see `../README.md`. This README is the
only tracked file here, which is also what keeps the directory in git.

## Rules live elsewhere

The `instructions` key is intentionally empty. Global rules come from
`rules/AGENTS.md`, which opencode loads automatically from
`~/.config/opencode/AGENTS.md`. Add entries to `instructions` only for extra
always-on instruction files.

It previously read `"instructions": [""]` — an empty string, which silently
matched nothing and meant no instruction file was ever loaded. If you add
entries, check they resolve.
