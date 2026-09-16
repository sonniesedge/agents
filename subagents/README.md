# subagents/

Agent definitions. Each `*.md` file declares one **named agent** you can
switch to or delegate work to: its model, its tool permissions, and its
system prompt.

Linked by the `subagents` target:

```yaml
targets:
  opencode:
    subagents: ~/.config/opencode/agent
```

Note the target path is opencode's own directory name, `agent`. This
directory is named for the target *kind* instead, and says `sub` to keep it
distinct from `AGENTS.md`, which is a rules file and nothing to do with this.

## Not to be confused with `rules/`

| | `subagents/` | `rules/` |
| --- | --- | --- |
| what | agent definitions | instructions |
| effect | creates agents to choose between | changes how every agent behaves |
| loaded | only when that agent is invoked | always |
| count | one file per agent | one file per theme |

`rules/` holds themed instruction files that apply to every agent. Despite
`subagents/` and `AGENTS.md`-style naming elsewhere, the two are unrelated.

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
$EDITOR subagents/security-reviewer.md
./agents.py sync
```

Filenames are used as-is — unlike skills, no owner prefix is applied.

See `examples/security-reviewer.md` for a worked example. Copy it up one level
to activate it: `examples/` is deliberately not linked out, so nothing in
there is ever a live agent.

`README.md` and `examples/` are both skipped when linking.
