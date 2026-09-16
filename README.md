# agents

User-scoped agent skills, agent files, and plugins — version controlled in one
place and symlinked into the tools that consume them.

Skills follow the [Agent Skills](https://agentskills.io) standard: a folder
containing a `SKILL.md` with `name` and `description` frontmatter, plus any
scripts, references, or assets it needs.

## Layout

```
config.yaml        owner, symlink targets, remote sources
config.local.yaml  private settings, layered on top  (gitignored)
skills/            skills authored here (unprefixed on disk)
rules/AGENTS.md    personal, always-on agent rules
opencode/          opencode.jsonc                    (gitignored)
agent/             agent definition files (*.md)
plugin/            plugin files
scripts/agents.py  the CLI
.vendor/           cloned remote repos               (gitignored)
.build/            rendered, prefixed skills         (gitignored)
```

The two `config*.yaml` files at the root configure this repo. Every directory
is named for the artefact it holds and is symlinked out as-is.

## Naming

Every installed skill is prefixed by whoever authored it:

- skills in `skills/` get the `owner` from `config.yaml` → `sonniesedge-chezmoi`
- skills from a remote get that source's `owner` → `mattpocock-tdd`

`owner: auto` derives the prefix from this repo's own git remote, so a repo
published at `github.com/sonniesedge/agents` yields `sonniesedge`. Set a
literal string instead to pin it regardless of remote, and `owner_remote` to
read something other than `origin`. If `auto` can't resolve, sync stops and
tells you rather than guessing — a wrong prefix would rename every skill you
author. `./scripts/agents.py status` always reports which route was taken.

The spec wants a skill's `name` to match its directory name, so `sync` renders
each skill into `.build/skills/<owner>-<name>/` with a rewritten `SKILL.md`,
then symlinks that. Every other file in the skill is symlinked back to its
source, so scripts and references stay live — only `SKILL.md` edits need a
re-run of `./scripts/agents.py sync`.

Changing the prefix is safe to do: the next sync removes the old symlinks and
creates the new ones.

## Usage

```sh
./scripts/agents.py sync             # fetch remotes, rebuild, refresh symlinks
./scripts/agents.py sync --no-fetch  # rebuild and relink without touching the network
./scripts/agents.py status           # what is linked, and where it came from
./scripts/agents.py list             # every resolvable skill
./scripts/agents.py fetch            # update remote sources only
./scripts/agents.py unlink           # remove every symlink this repo owns
```

`sync` is the everyday command and is safe to re-run. It only ever touches
symlinks that point back into this repo — anything else in the target
directories is left alone and reported as a warning.

## Adding a skill of your own

```sh
mkdir -p skills/my-skill
$EDITOR skills/my-skill/SKILL.md   # name: my-skill  (unprefixed)
./scripts/agents.py sync
```

Write the frontmatter `name` unprefixed. The prefix is applied at build time,
so changing `owner` in `config.yaml` renames every one of your skills at once.

## Adding a remote source

Add an entry to `sources` in `config.yaml` and run `./scripts/agents.py sync`:

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

`config.local.yaml` is gitignored and layered on top of `config.yaml`: its
`sources` are appended, and any other key it sets overrides. Put work-internal
or private settings there so this repo can stay public without advertising
them.

## Targets

`config.yaml` decides where things land. By default:

| what    | target                            |
| ------- | --------------------------------- |
| skills  | `~/.config/opencode/skill`        |
| agents  | `~/.config/opencode/agent`        |
| plugins | `~/.config/opencode/plugin`       |
| rules   | `~/.config/opencode/AGENTS.md`    |
| config  | `~/.config/opencode/opencode.jsonc` |

The first three are directories of entries. `rules` and `config` are single
files, and both are optional — drop the line to stop managing one.

`rules` is a single file because [opencode reads global
rules](https://opencode.ai/docs/rules/) from exactly
`~/.config/opencode/AGENTS.md`.

`opencode/opencode.jsonc` is gitignored: a personal opencode config tends to
name internal hosts, services, and providers. The repo owns the symlink; the
content stays local.

None of these targets will overwrite a file the repo did not create. If
something is already there and is not a symlink pointing back here, sync warns
and leaves it untouched.

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
