#!/usr/bin/env python3
"""Validate .claude-plugin/marketplace.json and the plugins it points at.

Checks the things that actually break a marketplace at install time:
  - marketplace.json parses and has the required top-level fields
  - every local `source` path exists and holds a plugin
  - each plugin.json name matches both its directory and its marketplace entry
  - every skill has a SKILL.md with `name` and `description` frontmatter
  - each skill's `name` matches its directory name

Exit status is 0 when clean, 1 when any error is found.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

errors: list[str] = []
warnings: list[str] = []


def error(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Parse the top-level scalar keys of a --- delimited YAML frontmatter block."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fields: dict[str, str] = {}
    key = None
    for line in text[3:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace() and key:  # continuation of a folded value
            fields[key] += " " + line.strip()
            continue
        head, sep, value = line.partition(":")
        if not sep:
            continue
        key = head.strip()
        fields[key] = value.strip().strip("\"'")
    return fields


def check_skill(skill_dir: Path, plugin_label: str) -> None:
    rel = skill_dir.relative_to(ROOT)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        error(f"{plugin_label}: {rel} has no SKILL.md")
        return
    fields = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if fields is None:
        error(f"{rel}/SKILL.md: missing or unterminated --- frontmatter block")
        return
    for required in ("name", "description"):
        if not fields.get(required):
            error(f"{rel}/SKILL.md: frontmatter is missing `{required}`")
    name = fields.get("name")
    if name and name != skill_dir.name:
        error(f"{rel}/SKILL.md: name `{name}` does not match directory `{skill_dir.name}`")
    if name and not KEBAB.match(name):
        error(f"{rel}/SKILL.md: name `{name}` is not kebab-case")
    description = fields.get("description", "")
    if description and len(description) < 30:
        warn(f"{rel}/SKILL.md: description is very short; say when the skill should trigger")


def check_plugin(entry: dict, index: int) -> None:
    label = entry.get("name") or f"plugins[{index}]"

    for required in ("name", "source"):
        if not entry.get(required):
            error(f"{label}: marketplace entry is missing `{required}`")
    if entry.get("name") and not KEBAB.match(entry["name"]):
        error(f"{label}: marketplace entry name is not kebab-case")

    source = entry.get("source")
    if not isinstance(source, str):
        # Remote sources (github, url, npm, ...) are resolved at install time.
        if isinstance(source, dict) and not source.get("source"):
            error(f"{label}: object source is missing its `source` discriminator")
        return

    plugin_dir = (ROOT / source).resolve()
    if not plugin_dir.is_dir():
        error(f"{label}: source `{source}` does not exist")
        return
    if ROOT not in plugin_dir.parents and plugin_dir != ROOT:
        error(f"{label}: source `{source}` escapes the repository root")
        return

    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            error(f"{label}: .claude-plugin/plugin.json is not valid JSON ({exc})")
            data = {}
        if not data.get("name"):
            error(f"{label}: plugin.json is missing `name`")
        elif data["name"] != entry.get("name"):
            error(
                f"{label}: plugin.json name `{data['name']}` does not match "
                f"marketplace entry `{entry.get('name')}`"
            )
        elif data["name"] != plugin_dir.name:
            error(f"{label}: plugin.json name does not match directory `{plugin_dir.name}`")
    else:
        warn(f"{label}: no .claude-plugin/plugin.json (allowed — components auto-discover)")

    skills_root = plugin_dir / "skills"
    if skills_root.is_dir():
        skill_dirs = sorted(d for d in skills_root.iterdir() if d.is_dir())
        if not skill_dirs:
            warn(f"{label}: skills/ exists but is empty")
        for skill_dir in skill_dirs:
            check_skill(skill_dir, label)

    components = ("skills", "commands", "agents", "hooks", "bin", ".mcp.json")
    if not any((plugin_dir / c).exists() for c in components):
        warn(f"{label}: no skills/, commands/, agents/, hooks/, bin/, or .mcp.json found")


def main() -> int:
    if not MARKETPLACE.is_file():
        print(f"error: {MARKETPLACE.relative_to(ROOT)} not found", file=sys.stderr)
        return 1
    try:
        data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: marketplace.json is not valid JSON: {exc}", file=sys.stderr)
        return 1

    for required in ("name", "owner", "plugins"):
        if required not in data:
            error(f"marketplace.json is missing required field `{required}`")
    if isinstance(data.get("owner"), dict) and not data["owner"].get("name"):
        error("marketplace.json: owner is missing `name`")

    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        error("marketplace.json: `plugins` must be an array")
        plugins = []

    seen: set[str] = set()
    for i, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            error(f"plugins[{i}] is not an object")
            continue
        name = entry.get("name")
        if name in seen:
            error(f"duplicate plugin name `{name}`")
        seen.add(name)
        check_plugin(entry, i)

    on_disk = {d.name for d in (ROOT / "plugins").iterdir() if d.is_dir()} if (ROOT / "plugins").is_dir() else set()
    for orphan in sorted(on_disk - seen):
        warn(f"plugins/{orphan} exists but is not listed in marketplace.json")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"\nOK: {len(plugins)} plugin(s) validated, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
