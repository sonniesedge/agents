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

## Rules are wired from here

opencode does not read a rules directory on its own, so `instructions` has to
glob it:

```jsonc
"instructions": ["~/.config/opencode/rules/*.md"]
```

Use `~` or an absolute path — a relative entry globs upward from whatever
project you are in, not from this config. Sync warns if this line is missing
or stops matching the linked rules directory.

This previously read `"instructions": [""]`, an empty string that silently
matched nothing, so no instruction file was ever loaded. If you add entries,
check they resolve.
