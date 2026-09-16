# rules/

Personal instructions, loaded into **every** session. One file per theme —
`git.md`, `testing.md`, `token-budget.md` — rather than one long file.

An `AGENTS.md` here is treated as the primary file rather than a theme: when
merging it leads, and the themed files follow.

## Linking them

The default is a directory, one symlink per themed file:

```yaml
targets:
  opencode:
    rules: ~/.config/opencode/rules
  claude:
    rules: ~/.claude/rules
```

Any target can be written longhand to pass options. For `rules` the option is
`merge`, which concatenates the themed files into a single generated
`AGENTS.md` instead:

```yaml
targets:
  opencode:
    rules:
      path: ~/.config/opencode/rules
      merge: true
```

A bare string is shorthand for `path`, so the two forms above differ only in
`merge`. With `merge: true` the generated file is written *inside* `path` as
`AGENTS.md`; point `path` directly at a `.md` file to place it exactly.

| | `merge: false` (default) | `merge: true` |
| --- | --- | --- |
| installs | one symlink per file | one generated `AGENTS.md` |
| edits | live | need a `sync` |
| per-file `paths:` scoping | works in Claude Code | lost, all one file |
| context cost | identical | identical |

Prefer the default. Merge when a tool reads only a single rules file, or when
you want one artefact rather than many.

Switching between the two is safe in either direction — sync clears whatever
it previously installed, whether that is the per-file symlinks in the same
directory or a file at an old path.

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

`merge: true` does not avoid this. opencode reads `AGENTS.md` natively only at
the top of its config directory, so a merged file *inside* a subdirectory
still needs the glob. Point `path` at `~/.config/opencode/AGENTS.md` if you
want it read with no config at all.

Merge order is `AGENTS.md` first, then the rest alphabetically, so numeric
prefixes (`10-git.md`, `20-testing.md`) reorder the themed files. Each section
is labelled with its source in an HTML comment; Claude Code strips those
before loading, so they cost nothing there.

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
