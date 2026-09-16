# agents

User-scoped agent skills, agent files, and plugins — version controlled in one
place and symlinked into the tools that consume them.

Skills follow the [Agent Skills](https://agentskills.io) standard: a folder
containing a `SKILL.md` with `name` and `description` frontmatter, plus any
scripts, references, or assets it needs.

## Layout

```
agents.yaml        owner prefix + symlink targets
skills.yaml        manifest of remote skill sources
skills.local.yaml  private sources, merged in       (gitignored)
skills/            skills authored here (unprefixed on disk)
rules/AGENTS.md    personal, always-on agent rules
agent/             agent definition files (*.md)
plugin/            plugin files
scripts/agents.py  the CLI
.vendor/           cloned remote repos              (gitignored)
.build/            rendered, prefixed skills        (gitignored)
```

## Naming

Every installed skill is prefixed by whoever authored it:

- skills in `skills/` get the `owner` from `agents.yaml` → `sonniesedge-chezmoi`
- skills from a remote get that source's `owner` → `mattpocock-tdd`

`owner: auto` derives the prefix from this repo's own git remote, so a repo
published at `github.com/sonniesedge/agents` yields `sonniesedge`. Set a
literal string instead to pin it regardless of remote, and `owner_remote` to
read something other than `origin`. If `auto` can't resolve, sync stops and
tells you rather than guessing — a wrong prefix would rename every skill you
author. `./agents status` always reports which route was taken.

The spec wants a skill's `name` to match its directory name, so `sync` renders
each skill into `.build/skills/<owner>-<name>/` with a rewritten `SKILL.md`,
then symlinks that. Every other file in the skill is symlinked back to its
source, so scripts and references stay live — only `SKILL.md` edits need a
re-run of `./agents sync`.

Changing the prefix is safe to do: the next sync removes the old symlinks and
creates the new ones.

## Usage

```sh
./agents sync             # fetch remotes, rebuild, refresh symlinks
./agents sync --no-fetch  # rebuild and relink without touching the network
./agents status           # what is linked, and where it came from
./agents list             # every resolvable skill
./agents fetch            # update remote sources only
./agents unlink           # remove every symlink this repo owns
```

`sync` is the everyday command and is safe to re-run. It only ever touches
symlinks that point back into this repo — anything else in the target
directories is left alone and reported as a warning.

## Adding a skill of your own

```sh
mkdir -p skills/my-skill
$EDITOR skills/my-skill/SKILL.md   # name: my-skill  (unprefixed)
./agents sync
```

Write the frontmatter `name` unprefixed. The prefix is applied at build time,
so changing `owner` in `agents.yaml` renames every one of your skills at once.

## Adding a remote source

Add an entry to `skills.yaml` and run `./agents sync`:

```yaml
sources:
  - owner: someone          # prefix for every skill from this repo
    repo: someone/skills    # or a full git/SSH URL
    ref: main               # branch, tag, or commit (optional)
    path: skills            # subdirectory to scan (optional)
    include: ["tdd", "*-review"]   # optional allowlist
    exclude: ["*.archived"]        # optional denylist
```

`fetch` clones into `.vendor/<host>/<org>/<repo>` and checks out `ref`,
detached. Re-running `sync` pulls the latest and relinks, so remote skills stay
current. Removing a source from the manifest removes its symlinks on the next
sync.

### Private sources

`skills.local.yaml` uses the same format, is gitignored, and is merged with
`skills.yaml` at sync time. Put work-internal or private sources there so this
repo can stay public without advertising them.

## Targets

`agents.yaml` decides where things land. By default:

| what    | target                        |
| ------- | ----------------------------- |
| skills  | `~/.config/opencode/skill`    |
| agents  | `~/.config/opencode/agent`    |
| plugins | `~/.config/opencode/plugin`   |
| rules   | `~/.config/opencode/AGENTS.md`|

The first three are directories of entries. `rules` is a single file, because
[opencode reads global rules](https://opencode.ai/docs/rules/) from exactly
`~/.config/opencode/AGENTS.md`. It is optional — drop the line to stop
managing it.

Note that `rules/AGENTS.md` deliberately is *not* this repo's root
`AGENTS.md`. opencode checks for local rule files before global ones, so a
root `AGENTS.md` would make your personal rules double as this repo's project
rules whenever you worked in here. The two stay separate.

For rules too big to keep always-on, reference them lazily from within
`rules/AGENTS.md` rather than loading everything every session:

```markdown
For my git conventions: @~/.config/opencode/rules/git.md
```

## Requirements

`python3` with PyYAML, and `git`.
