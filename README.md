# Agents

User-scoped agent skills, agent files, and plugins for your agent harness. All
version controlled in one place and symlinked into the tools that consume
them.

Focussed on [opencode](https://opencode.ai/) for now, but flexible enough to
be expanded to other agent harnesses.

Skills follow the [Agent Skills](https://agentskills.io) standard: a folder
containing a `SKILL.md` with `name` and `description` frontmatter, plus any
scripts, references, or assets it needs.

## Quick start

You need [`uv`](https://docs.astral.sh/uv/) and `git` on your system. Nothing
else: `agents.py` declares its own Python version and dependencies inline, and
uv builds and caches an environment for it on first run.

Fork this repo rather than cloning it — the skills you author here are yours,
and the owner prefix below is derived from your own remote. Then:

```sh
./agents.py sync     # fetch remote sources, build, symlink into your config
./agents.py status   # confirm what landed, and where it came from
```

That's the whole setup. From then on opencode loads these skills, rules,
subagents, and plugins in every session, in every project, with no per-project
configuration.

Once you've changed your own resources or edited `config.yaml`, run `sync`
again to link everything up. It's safe to re-run.

## Resource Types

Four kinds of resource, one directory each. Each carries its own `README.md`
with the detail. Three are symlinked out as they are; skills are rendered
first, to apply the owner prefix, as described under [Naming](#naming).

### Skills

[`skills/`](skills/) — procedural knowledge any agent loads on demand, when
a task matches the skill's description. Skills you author live here; skills
from other people are declared as `sources` and cloned into `.vendor/`, a
generated directory that is gitignored.

### Subagents

[`subagents/`](subagents/) — named agents you can switch to or delegate to,
one `*.md` file each, declaring a model, tool permissions, and a system
prompt. See [`subagents/examples/`](subagents/examples/) for a worked example.

### Rules

[`rules/`](rules/) — instructions loaded into every session, one file per
theme. They can be linked as individual files, merged into a single
`AGENTS.md`, or a mixture of both.

### Plugins

[`plugins/`](plugins/) — JavaScript or TypeScript that hooks into opencode's
runtime to add tools, intercept tool calls, or answer permission prompts. Real
code with no sandbox, so reach for a skill first. See
[`plugins/examples/`](plugins/examples/).

## Adding skills

### Your own skills

```sh
mkdir -p skills/my-skill
$EDITOR skills/my-skill/SKILL.md
./agents.py sync
```

Write the frontmatter `name` unprefixed. The prefix is applied at build time,
so changing `owner` in `config.yaml` renames every one of your skills at once.

### Remote skills

Add an entry to `sources` in `config.yaml` and run sync:

```yaml
sources:
  - repo: someone/skills    # or a full git URL
    ref: main               # branch, tag, or commit (optional)
    path: skills            # subdirectory to scan (optional)
```

Repos are always cloned over SSH: `someone/skills` and an `https://` URL
alike become `git@host:someone/skills.git`. HTTPS prompts for a username on
anything private, which fails outright when git runs non-interactively, so
private sources work the same way public ones do provided your SSH key is
loaded.

Skills from this source install as `someone-<skill>`: the prefix defaults to
the org the repo belongs to. Set `owner` explicitly to override it.

`path` also takes a list, to pull from several subdirectories:

```yaml
    path:
      - skills/engineering
      - skills/misc
```

An entry reading `not <path>` excludes instead, so you can take a whole tree
minus part of it. Globs work in either direction:

```yaml
    path:
      - skills
      - not skills/deprecated
      - not skills/*.archived
```

Excluding a directory excludes everything beneath it. With no `path` at all,
the whole repo is scanned.

`fetch` clones into `.vendor/<host>/<org>/<repo>` and checks out `ref`,
detached. Re-running `sync` pulls the latest and relinks, so remote skills
stay current. Removing a source from `config.yaml` removes its symlinks on the
next sync.

### Private sources

`config.local.yaml` is gitignored and layered on top of `config.yaml`: its
`sources` are appended, and any other key it sets overrides. Put work-internal
or private settings there so this repo can stay public without advertising
them.

## Naming

Every installed skill is prefixed by whoever authored it:

- skills in `skills/` get the `owner` from `config.yaml` → `sonniesedge-chezmoi`
- skills from a remote get that source's `owner` → `mattpocock-tdd`

`owner: auto` derives the prefix from this repo's own git remote, so a repo
published at `github.com/sonniesedge/agents` yields `sonniesedge`. Set a
literal string instead to pin it regardless of remote, and `owner_remote` to
read something other than `origin`. If `auto` can't resolve, sync stops and
tells you rather than guessing — a wrong prefix would rename every skill you
author. `./agents.py status` always reports which route was taken.

The spec wants a skill's `name` to match its directory name, so `sync` renders
each skill into `.build/skills/<owner>-<name>/` with a rewritten `SKILL.md`,
then symlinks that. `.build/` is generated and gitignored. Every other file in
the skill is symlinked back to its source, so scripts and references stay live
— only `SKILL.md` edits need a re-run of `./agents.py sync`.

Changing the prefix is safe to do: the next sync removes the old symlinks and
creates the new ones.

## Usage

```sh
./agents.py                  # list the available commands
./agents.py sync             # fetch remotes, rebuild, refresh symlinks
./agents.py sync --no-fetch  # rebuild and relink without touching the network
./agents.py status           # what is linked, and where it came from
./agents.py list             # every resolvable skill
./agents.py fetch            # update remote sources only
./agents.py unlink           # remove every symlink this repo owns
```

`sync` is the everyday command and is safe to re-run. It only ever touches
symlinks that point back into this repo — anything else in the target
directories is left alone and reported as a warning.

It is not the default, though: run with no command and you get the list
above. `sync` reaches the network and rewrites symlinks, so it is worth
asking for rather than getting by accident.

### JSON output

`--json` works with any command, for programmatic usage:

```sh
./agents.py status --json | jq '.targets[] | select(.state != "linked")'
```

Warnings go into the document rather than to stderr, and failures are JSON
too, with `ok: false` and a non-zero exit. The flag is accepted either before
or after the command.

### Colour

Output is colourised when it is going to a terminal, and plain when it is
piped or redirected, so captured output stays free of escape codes. Colour is
decided per stream: redirecting stdout to a file still leaves warnings on your
terminal coloured.

To turn it off regardless, pass `--no-color` (or `--no-colour`), or set
[`NO_COLOR`](https://no-color.org) in the environment. `--json` never
colourises.

## Targets

`config.yaml` decides where things land, grouped by tool:

```yaml
targets:
  opencode:
    skills: ~/.config/opencode/skill
    subagents: ~/.config/opencode/agent
    plugins: ~/.config/opencode/plugin
    rules: ~/.config/opencode/rules
    config: ~/.config/opencode/opencode.jsonc
```

Every kind is optional — drop a line to stop managing it. The four resource
types are recognised, plus `config`, which is a tool's own settings file
rather than a resource this repo defines:

| kind        | shape     | source                       |
| ----------- | --------- | ---------------------------- |
| `skills`    | directory | `.build/skills/` (prefixed)  |
| `subagents` | directory | `subagents/`                 |
| `plugins`   | directory | `plugins/`                   |
| `rules`     | directory | `rules/`                     |
| `config`    | file      | `settings/<tool>/<filename>` |

Anything else is a typo and sync says so, rather than silently linking
nothing.

Adding a second tool is config-only. `rules` is a directory both tools read,
so the same themed files serve both:

```yaml
targets:
  claude:
    skills: ~/.claude/skills
    rules: ~/.claude/rules
```

Claude Code reads `~/.claude/rules/` natively; opencode must be pointed at its
rules directory from `opencode.jsonc`. Sync warns if that wiring is missing.

Any target can be written longhand to pass options. `rules` takes `merge`,
which concatenates the themed files into a single generated `AGENTS.md`
instead of linking them separately:

```yaml
rules:
  path: ~/.config/opencode/rules
  merge: true
```

A bare string is shorthand for `path`. See `rules/README.md`.

Retargeting anything is safe: sync records what it linked and removes the old
location on the next run.

`config` is per-tool instead, read from a directory named after the tool —
`settings/opencode/opencode.jsonc` for the above, and
`settings/claude/settings.json` for a `claude.config` target.

Everything under `settings/` except the READMEs is gitignored: tool configs
tend to name internal hosts, services, and providers. The repo owns the
symlink; the content stays local.

None of these targets will overwrite a file the repo did not create. If
something is already there and is not a symlink pointing back here, sync warns
and leaves it untouched.

Note that `rules/` is deliberately not a root `AGENTS.md`. Both tools check
for local rule files before global ones, so a root copy would make your
personal rules double as this repo's project rules whenever you worked in
here.
