# rules/

Personal instructions, loaded into **every** session. One file per theme —
`git.md`, `testing.md`, `token-budget.md` — rather than one long file.

Linked as a directory:

```yaml
targets:
  opencode:
    rules: ~/.config/opencode/rules
  claude:
    rules: ~/.claude/rules
```

Both tools read a rules directory, so the same files serve both.

## opencode needs wiring, Claude Code does not

|                    | Claude Code                | opencode                          |
| ------------------ | -------------------------- | --------------------------------- |
| wiring             | none, reads it natively    | must be globbed from its config   |
| discovery          | recursive, subdirs work    | basename glob only — **flat**     |
| `paths:` frontmatter | scopes a rule to matching files | ignored, rule always loads   |

For opencode, `settings/opencode/opencode.jsonc` needs:

```jsonc
"instructions": ["~/.config/opencode/rules/*.md"]
```

Use `~` or an absolute path. A **relative** entry globs upward from whatever
project you are in, not from the config directory — a quiet way to load the
wrong files.

Because that config is gitignored, a fresh clone can have rules linked but
nothing loading them. `sync` checks for this and warns:

```
warning: opencode: rules are linked to ~/.config/opencode/rules but
opencode.jsonc does not glob them, so they will not load.
```

## Keep it flat

opencode globs the basename only, so `rules/**/*.md` will not work there even
though Claude Code would find it. Subdirectories silently load for one tool
and not the other, so keep every rule at the top level.

## Keep it short

Everything here costs context in every session, in every tool. Claude Code
suggests staying under 200 lines per file and notes that adherence drops as
files grow. For anything procedural or occasional, write a skill instead —
skills load only when the task matches.

Claude Code can scope a rule to matching files with `paths:` frontmatter:

```markdown
---
paths:
  - "src/**/*.ts"
---
```

opencode ignores that frontmatter and loads the rule regardless, so a
path-scoped rule behaves differently in each tool. Use it only for rules that
are harmless when always loaded.

## Not to be confused with `agents/`

| | `rules/` | `agents/` |
| --- | --- | --- |
| what | instructions | agent definitions |
| effect | changes how every agent behaves | creates agents to choose between |
| loaded | always | only when that agent is invoked |
| count | one file per theme | one file per agent |

## Why not the repo root?

These are deliberately not a root `AGENTS.md`. Both tools check for local rule
files before global ones, so a root copy would make your personal rules double
as this repo's project rules whenever you worked in here.

`README.md` is skipped when linking, so this file is not loaded as a rule.
