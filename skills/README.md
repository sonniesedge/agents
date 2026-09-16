# skills/

Skills you author yourself, following the
[Agent Skills standard](https://agentskills.io): a folder containing a
`SKILL.md` with `name` and `description` frontmatter, plus any scripts,
references, or assets it needs.

Skills from other people are not kept here. They are declared as `sources` in
`config.yaml`, cloned into `.vendor/`, and never edited in place. Their `path`
selects which subdirectories to take, and `not <path>` excludes parts of a
tree.

Linked by the `skills` target:

```yaml
targets:
  opencode:
    skills: ~/.config/opencode/skill
```

## Names are unprefixed here

Write the frontmatter `name` unprefixed, matching the directory:

```
skills/chezmoi/SKILL.md     ->  name: chezmoi
```

Sync applies your `owner` prefix and installs it as `sonniesedge-chezmoi`. The
prefix is added at build time, so changing `owner` in `config.yaml` renames
every skill you author at once.

## How sync handles them

The spec wants a skill's `name` to match its directory name, so sync renders
each skill into `.build/skills/<owner>-<name>/` with a rewritten `SKILL.md`,
and symlinks that. Every *other* file in the skill is symlinked back here, so
scripts and references stay live — only `SKILL.md` edits need a re-sync.

## Adding one

```sh
mkdir -p skills/my-skill
$EDITOR skills/my-skill/SKILL.md
./scripts/agents.py sync
```

Any directory containing a `SKILL.md` is found, including nested ones, so
skills may be grouped into subdirectories.

## Not to be confused with `agents/`

A skill is procedural knowledge any agent can load when a task matches its
description. An agent definition creates a whole named agent. Skills are
discovered by description; agents are chosen by name.
