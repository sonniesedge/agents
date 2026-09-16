# rules/

Personal instructions, injected into the context of **every** session.

`AGENTS.md` is prose telling any agent how to behave — conventions, standing
preferences, things you would otherwise repeat in each conversation. It is
always loaded, so keep it short.

Linked by the `rules` target:

```yaml
targets:
  opencode:
    rules: ~/.config/opencode/AGENTS.md
```

## Not to be confused with `agents/`

| | `rules/` | `agents/` |
| --- | --- | --- |
| what | instructions | agent definitions |
| effect | changes how every agent behaves | creates agents to choose between |
| loaded | always | only when that agent is invoked |
| count | one file | one file per agent |

The `AGENTS.md` filename is opencode's, not ours —
[opencode reads global rules](https://opencode.ai/docs/rules/) from exactly
`~/.config/opencode/AGENTS.md`. It has nothing to do with the `agents/`
directory.

## Shared across tools

This one file can land under whatever name each tool expects, so a second
tool needs no second copy:

```yaml
targets:
  opencode:
    rules: ~/.config/opencode/AGENTS.md
  claude:
    rules: ~/.claude/CLAUDE.md
```

## Keeping it short

Everything here costs context in every session. For detail you only sometimes
need, reference it lazily instead and let the agent read it on demand:

```markdown
For my git conventions: @~/.config/opencode/rules/git.md
```

## Why not the repo root?

This is deliberately not the root `AGENTS.md`. opencode checks for local rule
files before global ones, so a root copy would make your personal rules double
as this repo's project rules whenever you worked in here.
