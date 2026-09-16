# agents/

Agent definitions. Each `*.md` file declares one **named agent** you can
switch to or delegate work to: its model, its tool permissions, and its
system prompt.

Linked by the `agents` target:

```yaml
targets:
  opencode:
    agents: ~/.config/opencode/agent
```

Note the target path is opencode's own directory name, which is singular.
This directory is plural to match the target *kind*.

## Not to be confused with `rules/`

| | `agents/` | `rules/` |
| --- | --- | --- |
| what | agent definitions | instructions |
| effect | creates agents to choose between | changes how every agent behaves |
| loaded | only when that agent is invoked | always |
| count | one file per agent | one file |

`rules/AGENTS.md` is named for the file opencode expects at
`~/.config/opencode/AGENTS.md`. Despite the name, it belongs to `rules/` and
has nothing to do with this directory.

## Shape of a definition

One agent per file, named by its filename:

```markdown
---
description: Reviews changes for security issues
mode: subagent
model: github-copilot/claude-opus-5
temperature: 0.1
tools:
  write: false
  edit: false
---

You are a security reviewer. Focus on injection, authentication, and
data exposure. Report findings by severity.
```

`mode: subagent` makes it delegable rather than directly selectable. See
[the agents docs](https://opencode.ai/docs/agents/) for the full frontmatter.

## Adding one

```sh
$EDITOR agents/security-reviewer.md
./scripts/agents.py sync
```

Filenames are used as-is — unlike skills, no owner prefix is applied.

`README.md` is skipped when linking, so this file is not mistaken for an
agent definition.
