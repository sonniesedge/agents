#!/usr/bin/env python3
"""Manage user-scoped agent skills, agent files, and plugins.

Locally-authored skills live unprefixed under skills/. Remote skills are
cloned into .vendor/ from the sources declared in config.yaml. Both are
rendered into .build/skills/<owner>-<name>/ with a frontmatter `name` that
matches the directory, per the Agent Skills spec (agentskills.io), and then
symlinked into the targets declared in config.yaml.

Usage:
    ./scripts/agents.py sync            fetch + build + link (the everyday command)
    ./scripts/agents.py fetch           clone/update remote sources only
    ./scripts/agents.py build           render .build/ only
    ./scripts/agents.py link            refresh symlinks only
    ./scripts/agents.py status          show what is installed and where it came from
    ./scripts/agents.py list            list every resolvable skill
    ./scripts/agents.py unlink          remove every symlink this repo owns
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import NoReturn
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

REPO = Path(__file__).resolve().parent.parent
VENDOR = REPO / ".vendor"
BUILD = REPO / ".build"
SKILL_FILE = "SKILL.md"
# Targets that are a single file rather than a directory of entries.
FILE_TARGETS = frozenset({"rules", "config"})
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.DOTALL)
NAME_LINE = re.compile(r"^name:.*$", re.MULTILINE)


# --------------------------------------------------------------------------
# output


class Out:
    quiet = False

    @staticmethod
    def say(msg: str) -> None:
        if not Out.quiet:
            print(msg)

    @staticmethod
    def warn(msg: str) -> None:
        print(f"warning: {msg}", file=sys.stderr)

    @staticmethod
    def die(msg: str) -> NoReturn:
        sys.exit(f"error: {msg}")


# --------------------------------------------------------------------------
# config


def split_git_url(url: str) -> list[str]:
    """Break a git URL into its path segments, host first.

    Handles the three shapes git accepts:
        https://github.com/org/repo.git  -> [github.com, org, repo]
        git@github.com:org/repo.git      -> [github.com, org, repo]
        ssh://git@github.com/org/repo    -> [github.com, org, repo]
    """
    body = url.strip()
    for prefix in ("https://", "http://", "ssh://", "git+ssh://"):
        body = body.removeprefix(prefix)
    body = body.split("@", 1)[-1]  # drop any user@ portion
    body = body.replace(":", "/").removesuffix(".git")
    return [p for p in body.split("/") if p and p not in (".", "..")]


@dataclass
class Source:
    owner: str
    repo: str
    ref: str | None = None
    path: str = ""
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    @property
    def url(self) -> str:
        if "://" in self.repo or self.repo.startswith("git@"):
            return self.repo
        return f"https://github.com/{self.repo}.git"

    @property
    def slug(self) -> str:
        """Filesystem-safe identity for this source inside .vendor/."""
        return "/".join(split_git_url(self.url))

    @property
    def checkout(self) -> Path:
        return VENDOR / self.slug

    def wants(self, name: str) -> bool:
        if self.include and not any(fnmatch.fnmatch(name, p) for p in self.include):
            return False
        return not any(fnmatch.fnmatch(name, p) for p in self.exclude)


@dataclass
class Config:
    owner: str
    owner_from: str  # how `owner` was resolved, for `status`
    targets: dict[str, Path]
    sources: list[Source]


def expand(raw: str) -> Path:
    return Path(os.path.expandvars(str(raw))).expanduser()


def derive_owner(remote: str) -> tuple[str, str]:
    """Infer the owner prefix from this repo's own git remote.

    Returns (owner, explanation). Exits with guidance if it cannot be found,
    because guessing here would rename every skill you author.
    """
    hint = (
        f"Set `owner:` explicitly in config.yaml, or add the remote:\n"
        f"    git remote add {remote} git@github.com:<org>/<repo>.git"
    )
    try:
        url = git("remote", "get-url", remote, cwd=REPO)
    except RuntimeError:
        Out.die(f"owner is `auto` but this repo has no '{remote}' remote.\n{hint}")

    parts = split_git_url(url)
    if len(parts) < 3:
        Out.die(f"owner is `auto` but could not parse an org from '{url}'.\n{hint}")
    return parts[-2], f"auto, from {remote} ({url})"


CONFIG_FILE = "config.yaml"
LOCAL_CONFIG_FILE = "config.local.yaml"
RETIRED = ("agents.yaml", "skills.yaml", "skills.local.yaml")


def load_config() -> Config:
    main = REPO / CONFIG_FILE
    if not main.exists():
        stale = [f for f in RETIRED if (REPO / f).exists()]
        hint = (
            f"\nFound {', '.join(stale)}: these merged into {CONFIG_FILE}."
            if stale
            else ""
        )
        Out.die(f"missing {main}{hint}")

    # config.local.yaml is gitignored: somewhere to keep private or
    # work-internal settings without publishing them. Scalar keys override,
    # `sources` accumulate.
    layers: list[tuple[str, dict]] = []
    for path in (main, REPO / LOCAL_CONFIG_FILE):
        if path.exists():
            layers.append((path.name, yaml.safe_load(path.read_text()) or {}))

    data: dict = {}
    for _, layer in layers:
        data.update(layer)

    raw_owner = data.get("owner")
    if raw_owner is None or str(raw_owner).strip().lower() in ("auto", ""):
        owner, owner_from = derive_owner(str(data.get("owner_remote") or "origin"))
    else:
        owner, owner_from = str(raw_owner).strip(), CONFIG_FILE

    targets = {k: expand(v) for k, v in (data.get("targets") or {}).items()}
    for key in ("skills", "agents", "plugins"):
        if key not in targets:
            Out.die(f"{CONFIG_FILE} targets must include `{key}`")

    sources = []
    for name, layer in layers:
        for i, entry in enumerate(layer.get("sources") or []):
            src_owner, src_repo = entry.get("owner"), entry.get("repo")
            if not src_owner or not src_repo:
                Out.die(f"{name} source #{i + 1} needs both `owner` and `repo`")
            sources.append(
                Source(
                    owner=str(src_owner),
                    repo=str(src_repo),
                    ref=entry.get("ref"),
                    path=(entry.get("path") or "").strip("/"),
                    include=list(entry.get("include") or []),
                    exclude=list(entry.get("exclude") or []),
                )
            )
    return Config(
        owner=owner, owner_from=owner_from, targets=targets, sources=sources
    )


# --------------------------------------------------------------------------
# discovery


@dataclass
class Skill:
    owner: str
    name: str  # unprefixed, as found on disk
    src: Path  # directory containing SKILL.md
    origin: str  # "local" or the source repo slug

    @property
    def full(self) -> str:
        return f"{self.owner}-{self.name}"


def find_skills(root: Path, owner: str, origin: str) -> list[Skill]:
    """Recursively collect every directory holding a SKILL.md."""
    if not root.is_dir():
        return []
    found = []
    for skill_md in sorted(root.rglob(SKILL_FILE)):
        d = skill_md.parent
        if any(part.startswith(".") for part in d.relative_to(root).parts):
            continue
        found.append(Skill(owner=owner, name=d.name, src=d, origin=origin))
    return found


def collect(cfg: Config, *, require_fetch: bool = True) -> list[Skill]:
    skills = find_skills(REPO / "skills", cfg.owner, "local")

    for source in cfg.sources:
        if not source.checkout.exists():
            if require_fetch:
                Out.warn(f"{source.slug} not fetched yet; run `./scripts/agents.py fetch`")
            continue
        root = source.checkout / source.path if source.path else source.checkout
        if not root.is_dir():
            Out.warn(f"{source.slug}: path '{source.path}' does not exist")
            continue
        for skill in find_skills(root, source.owner, source.slug):
            if source.wants(skill.name):
                skills.append(skill)

    seen: dict[str, Skill] = {}
    for skill in skills:
        if skill.full in seen:
            Out.warn(
                f"duplicate skill '{skill.full}' from {skill.origin}; "
                f"keeping the one from {seen[skill.full].origin}"
            )
            continue
        seen[skill.full] = skill
    return sorted(seen.values(), key=lambda s: s.full)


# --------------------------------------------------------------------------
# fetch


def git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result.stdout.strip()


def fetch(cfg: Config) -> None:
    if not cfg.sources:
        Out.say("no remote sources declared in config.yaml")
        return
    for source in cfg.sources:
        dest = source.checkout
        try:
            if dest.exists():
                Out.say(f"updating {source.slug}")
                git("fetch", "--tags", "--prune", "origin", cwd=dest)
            else:
                Out.say(f"cloning {source.slug}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                git("clone", "--quiet", source.url, str(dest))

            ref = source.ref or git(
                "rev-parse", "--abbrev-ref", "origin/HEAD", cwd=dest
            ).split("/")[-1]
            # Prefer the remote-tracking branch so updates actually land.
            target = ref
            try:
                git("rev-parse", "--verify", f"origin/{ref}", cwd=dest)
                target = f"origin/{ref}"
            except RuntimeError:
                pass
            git("checkout", "--quiet", "--detach", target, cwd=dest)
            Out.say(f"  {source.slug} @ {git('rev-parse', '--short', 'HEAD', cwd=dest)}")
        except RuntimeError as exc:
            Out.warn(f"{source.slug}: {exc}")


# --------------------------------------------------------------------------
# build


def render_skill_md(text: str, full_name: str, skill: Skill) -> str:
    """Return SKILL.md with its frontmatter `name` forced to full_name."""
    match = FRONTMATTER.match(text)
    if not match:
        Out.warn(f"{skill.origin}/{skill.name}: no YAML frontmatter; copying as-is")
        return text

    block, body = match.group(1), text[match.end() :]
    if NAME_LINE.search(block):
        block = NAME_LINE.sub(f"name: {full_name}", block, count=1)
    else:
        block = f"name: {full_name}\n{block}"
    return f"---\n{block}\n---\n{body}"


def build(cfg: Config, skills: list[Skill]) -> Path:
    out = BUILD / "skills"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for skill in skills:
        dest = out / skill.full
        dest.mkdir()
        for entry in sorted(skill.src.iterdir()):
            if entry.name == SKILL_FILE:
                continue
            # Symlink everything else so edits in the source are live.
            (dest / entry.name).symlink_to(entry.resolve())
        text = (skill.src / SKILL_FILE).read_text(encoding="utf-8")
        (dest / SKILL_FILE).write_text(
            render_skill_md(text, skill.full, skill), encoding="utf-8"
        )
    Out.say(f"built {len(skills)} skill(s) into {out.relative_to(REPO)}")
    return out


# --------------------------------------------------------------------------
# link


def owned_by_repo(link: Path) -> bool:
    """True if `link` is a symlink pointing somewhere inside this repo."""
    if not link.is_symlink():
        return False
    target = Path(os.path.realpath(link))
    return target == REPO or REPO in target.parents


def relink(target_dir: Path, wanted: dict[str, Path]) -> tuple[int, int]:
    """Make target_dir contain exactly `wanted` among repo-owned symlinks."""
    target_dir.mkdir(parents=True, exist_ok=True)
    created = removed = 0

    for existing in sorted(target_dir.iterdir()):
        if owned_by_repo(existing) and existing.name not in wanted:
            existing.unlink()
            removed += 1
            Out.say(f"  - {existing.name}")

    for name, src in sorted(wanted.items()):
        link = target_dir / name
        src = src.resolve()
        if link.is_symlink():
            if Path(os.path.realpath(link)) == src:
                continue
            if not owned_by_repo(link):
                Out.warn(f"{link} is a foreign symlink; leaving it alone")
                continue
            link.unlink()
        elif link.exists():
            Out.warn(f"{link} exists and is not a symlink; leaving it alone")
            continue
        link.symlink_to(src)
        created += 1
        Out.say(f"  + {name}")

    return created, removed


def link_file(link: Path, src: Path | None) -> None:
    """Point a single path at `src`, or remove it when `src` is None.

    Used for targets that are one file rather than a directory of entries,
    like opencode's global ~/.config/opencode/AGENTS.md.
    """
    if src is None or not src.exists():
        if owned_by_repo(link):
            link.unlink()
            Out.say(f"  - {link.name}")
        return

    src = src.resolve()
    if link.is_symlink():
        if Path(os.path.realpath(link)) == src:
            return
        if not owned_by_repo(link):
            Out.warn(f"{link} is a foreign symlink; leaving it alone")
            return
        link.unlink()
    elif link.exists():
        Out.warn(f"{link} exists and is not a symlink; leaving it alone")
        return

    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(src)
    Out.say(f"  + {link.name}")


def link(cfg: Config, built: Path) -> None:
    Out.say(f"linking skills -> {cfg.targets['skills']}")
    relink(
        cfg.targets["skills"],
        {d.name: d for d in sorted(built.iterdir()) if d.is_dir()},
    )

    agents_src = REPO / "agent"
    Out.say(f"linking agents -> {cfg.targets['agents']}")
    relink(
        cfg.targets["agents"],
        {
            f.name: f
            for f in sorted(agents_src.glob("*.md"))
            if not f.name.startswith(".")
        }
        if agents_src.is_dir()
        else {},
    )

    plugins_src = REPO / "plugin"
    Out.say(f"linking plugins -> {cfg.targets['plugins']}")
    relink(
        cfg.targets["plugins"],
        {
            f.name: f
            for f in sorted(plugins_src.iterdir())
            if not f.name.startswith(".")
        }
        if plugins_src.is_dir()
        else {},
    )

    # Optional, and a single file rather than a directory: opencode's global
    # rules live at exactly ~/.config/opencode/AGENTS.md.
    if "rules" in cfg.targets:
        Out.say(f"linking rules  -> {cfg.targets['rules']}")
        link_file(cfg.targets["rules"], REPO / "rules" / "AGENTS.md")

    # Also a single file. Gitignored, since a personal opencode config tends
    # to name internal hosts and services.
    if "config" in cfg.targets:
        Out.say(f"linking config -> {cfg.targets['config']}")
        link_file(cfg.targets["config"], REPO / "config" / "opencode.jsonc")


# --------------------------------------------------------------------------
# commands


def cmd_fetch(cfg: Config, _: argparse.Namespace) -> None:
    fetch(cfg)


def cmd_build(cfg: Config, _: argparse.Namespace) -> None:
    build(cfg, collect(cfg))


def cmd_link(cfg: Config, _: argparse.Namespace) -> None:
    built = BUILD / "skills"
    if not built.is_dir():
        built = build(cfg, collect(cfg))
    link(cfg, built)


def cmd_sync(cfg: Config, args: argparse.Namespace) -> None:
    if not args.no_fetch:
        fetch(cfg)
    link(cfg, build(cfg, collect(cfg)))
    Out.say("sync complete")


def cmd_list(cfg: Config, _: argparse.Namespace) -> None:
    skills = collect(cfg, require_fetch=False)
    if not skills:
        Out.say("no skills found")
        return
    width = max(len(s.full) for s in skills)
    for skill in skills:
        print(f"{skill.full:<{width}}  {skill.origin}")


def cmd_status(cfg: Config, _: argparse.Namespace) -> None:
    skills = {s.full: s for s in collect(cfg, require_fetch=False)}
    print(f"repo   {REPO}")
    print(f"owner  {cfg.owner}  ({cfg.owner_from})")

    for source in cfg.sources:
        if source.checkout.exists():
            try:
                rev = git("rev-parse", "--short", "HEAD", cwd=source.checkout)
            except RuntimeError:
                rev = "?"
            print(f"source {source.slug} @ {rev} (owner: {source.owner})")
        else:
            print(f"source {source.slug} NOT FETCHED (owner: {source.owner})")

    for kind, target in cfg.targets.items():
        print(f"\n{kind} -> {target}")
        if kind in FILE_TARGETS:
            if owned_by_repo(target):
                broken = "" if target.exists() else "  BROKEN"
                print(f"  {target.name}  <- local{broken}")
            elif target.exists():
                print("  (exists, but not linked from this repo)")
            else:
                print("  (not linked)")
            continue
        if not target.is_dir():
            print("  (target directory does not exist)")
            continue
        managed = [e for e in sorted(target.iterdir()) if owned_by_repo(e)]
        if not managed:
            print("  (nothing linked from this repo)")
        for entry in managed:
            note = ""
            if kind == "skills":
                skill = skills.get(entry.name)
                note = f"  <- {skill.origin}" if skill else "  <- STALE"
            broken = "" if entry.exists() else "  BROKEN"
            print(f"  {entry.name}{note}{broken}")


def cmd_unlink(cfg: Config, _: argparse.Namespace) -> None:
    total = 0
    for kind, target in cfg.targets.items():
        if kind in FILE_TARGETS:
            if owned_by_repo(target):
                Out.say(f"unlinking {kind} from {target}")
                target.unlink()
                total += 1
                Out.say(f"  - {target.name}")
            continue
        if not target.is_dir():
            continue
        Out.say(f"unlinking {kind} from {target}")
        for entry in sorted(target.iterdir()):
            if owned_by_repo(entry):
                entry.unlink()
                total += 1
                Out.say(f"  - {entry.name}")
    Out.say(f"removed {total} symlink(s)")


COMMANDS = {
    "sync": cmd_sync,
    "fetch": cmd_fetch,
    "build": cmd_build,
    "link": cmd_link,
    "list": cmd_list,
    "status": cmd_status,
    "unlink": cmd_unlink,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agents.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-q", "--quiet", action="store_true")
    sub = parser.add_subparsers(dest="command")
    for name in COMMANDS:
        p = sub.add_parser(name)
        if name == "sync":
            p.add_argument(
                "--no-fetch",
                action="store_true",
                help="skip updating remote sources",
            )

    args = parser.parse_args()
    Out.quiet = args.quiet
    COMMANDS[args.command or "sync"](load_config(), args)


if __name__ == "__main__":
    main()
