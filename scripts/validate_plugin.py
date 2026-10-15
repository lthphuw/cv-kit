"""Check the cv-kit house rules that `claude plugin validate` does not enforce."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
LOCAL_PATH_RE = re.compile(r"/Users/|[A-Za-z]:\\")
LINK_RE = re.compile(r"\]\((?!https?://|#|mailto:)([^)#\s]+)")
SKILL_DIR_RE = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/([^\s`)\"']+)")
HOOK_COMMAND_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"'`;|&()<>]+)")
PLUGIN_ROOT_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s`)\"']+)")
# An agent that can fetch pages or run commands must say that what it reads is not an order.
FETCH_TOOLS = {"WebFetch", "WebSearch", "Bash"}
UNTRUSTED_RULE = "are data, not instructions"
README_ROW_RE = re.compile(r"^\| (Skill|Agent) \| `([^`]+)` \|", re.M)
README_CATALOG_RE = re.compile(r"has (\d+) rows\. (\d+) are marked `verified` and (\d+) are marked `UNVERIFIED`")
SKILL_KEYS = {
    "name", "description", "when_to_use", "disable-model-invocation", "user-invocable", "paths",
    "allowed-tools", "argument-hint", "model", "effort", "context", "agent", "license",
    "compatibility", "metadata",
}
AGENT_IGNORED = {"permissionMode", "hooks", "mcpServers", "initialPrompt"}
CATALOG_STATUS = {"verified", "UNVERIFIED"}
SCAN_PATHS = ["skills", "agents", "hooks", "rules", "shared", "evals", ".claude-plugin", "README.md"]
SCAN_SUFFIXES = {".md", ".json", ".py", ".sh", ".yml", ".yaml", ".js", ".html"}


def read_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("no frontmatter at line 1")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data, text


def _inside(root: Path, target: Path) -> bool:
    return target.exists() and root.resolve() in [target.resolve(), *target.resolve().parents]


def _check_links(md: Path, root: Path, text: str) -> list[str]:
    errors = []
    refs = [(rel, md.parent / rel) for rel in LINK_RE.findall(text) + SKILL_DIR_RE.findall(text)]
    refs += [(rel, root / rel) for rel in PLUGIN_ROOT_RE.findall(text)]
    for rel, target in refs:
        if not _inside(root, target):
            errors.append(f"{md}: reference {rel!r} does not resolve inside the plugin")
    return errors


def check_skills(root: Path) -> list[str]:
    errors: list[str] = []
    seen: dict[str, Path] = {}
    total = 0
    for directory in sorted(p for p in (root / "skills").glob("*") if p.is_dir()):
        if not (directory / "SKILL.md").exists():
            errors.append(f"{directory}: missing SKILL.md")
    for md in sorted(root.glob("skills/*/SKILL.md")):
        try:
            fm, text = read_frontmatter(md)
        except Exception as exc:  # malformed YAML must not stop the run
            errors.append(f"{md}: frontmatter error: {exc}")
            continue
        name, desc = str(fm.get("name", "")), str(fm.get("description", ""))
        total += len(desc)
        if name != md.parent.name or not NAME_RE.match(name) or len(name) > 64:
            errors.append(f"{md}: name {name!r} must equal its directory and match [a-z0-9-]")
        if name in seen:
            errors.append(f"{md}: duplicate name, also in {seen[name]}")
        seen[name] = md
        if not desc or len(desc) > 1024:
            errors.append(f"{md}: description empty or over 1024 characters ({len(desc)})")
        elif not desc.startswith("Use when"):
            errors.append(f"{md}: description must start with 'Use when'")
        for key in sorted(set(fm) - SKILL_KEYS):
            errors.append(f"{md}: unknown frontmatter key {key!r}")
        if text.count("\n") + 1 > 500:
            errors.append(f"{md}: more than 500 lines")
        errors += _check_links(md, root, text)
    if total > 8000:
        errors.append(f"skills: descriptions total {total} characters, budget is 8000")
    return errors


def check_agents(root: Path) -> list[str]:
    errors: list[str] = []
    skill_names = {p.parent.name for p in root.glob("skills/*/SKILL.md")}
    for md in sorted(root.glob("agents/*.md")):
        try:
            fm, text = read_frontmatter(md)
        except Exception as exc:
            errors.append(f"{md}: frontmatter error: {exc}")
            continue
        name = str(fm.get("name", ""))
        if not name or ":" in name:
            errors.append(f"{md}: agent name {name!r} is empty or contains ':'")
        if not fm.get("description"):
            errors.append(f"{md}: missing description")
        for key in sorted(AGENT_IGNORED & set(fm)):
            errors.append(f"{md}: {key} is ignored for plugin agents")
        for skill in fm.get("skills") or []:
            if skill not in skill_names:
                errors.append(f"{md}: preloads unknown skill {skill!r}")
        listed = fm.get("tools") or []
        tools = {str(t).strip() for t in (listed if isinstance(listed, list) else str(listed).split(","))}
        if tools & FETCH_TOOLS and UNTRUSTED_RULE not in text:
            errors.append(f"{md}: has {', '.join(sorted(tools & FETCH_TOOLS))} but never says fetched content "
                          f"{UNTRUSTED_RULE!r}")
        errors += _check_links(md, root, text)
    return errors


def _load_json(path: Path, errors: list[str]) -> dict | None:
    if not path.exists():
        errors.append(f"{path}: missing")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: expected a JSON object")
        return None
    return data


def check_manifests(root: Path) -> list[str]:
    errors: list[str] = []
    plugin = _load_json(root / ".claude-plugin/plugin.json", errors)
    market = _load_json(root / ".claude-plugin/marketplace.json", errors)
    if plugin is not None and market is not None:
        if "version" not in plugin:
            errors.append(".claude-plugin/plugin.json: version is required (single source)")
        plugins = market.get("plugins", [])
        if not isinstance(plugins, list):
            errors.append(".claude-plugin/marketplace.json: 'plugins' must be a list")
            plugins = []
        entries = {}
        for entry in plugins:
            if not isinstance(entry, dict):
                errors.append(f".claude-plugin/marketplace.json: plugin entry {entry!r} is not a JSON object")
                continue
            entries[entry.get("name")] = entry
        if plugin.get("name") not in entries:
            errors.append("marketplace.json: no plugin entry matches plugin.json name")
        for name, entry in entries.items():
            if "version" in entry:
                errors.append(f"marketplace.json: entry {name!r} must not set version")
    hooks_file = root / "hooks/hooks.json"
    if hooks_file.exists():
        hooks = _load_json(hooks_file, errors)
        if hooks is not None:
            if "hooks" not in hooks:
                errors.append(f"{hooks_file}: needs a top-level 'hooks' key")
            else:
                errors += _check_hook_paths(root, hooks_file, hooks["hooks"])
    return errors


def _check_hook_paths(root: Path, hooks_file: Path, events: object) -> list[str]:
    if not isinstance(events, dict):
        return [f"{hooks_file}: 'hooks' must be a JSON object keyed by event name"]
    errors = []
    for groups in events.values():
        if not isinstance(groups, list):
            errors.append(f"{hooks_file}: event groups {groups!r} must be a list")
            continue
        for group in groups:
            if not isinstance(group, dict):
                errors.append(f"{hooks_file}: hook group {group!r} is not a JSON object")
                continue
            for handler in group.get("hooks", []):
                if not isinstance(handler, dict):
                    errors.append(f"{hooks_file}: hook handler {handler!r} is not a JSON object")
                    continue
                errors += _check_handler_paths(root, hooks_file, handler)
    return errors


def _check_handler_paths(root: Path, hooks_file: Path, handler: dict) -> list[str]:
    errors = []
    for arg in handler.get("args", []):
        if "${CLAUDE_PLUGIN_ROOT}" in arg:
            target = root / arg.replace("${CLAUDE_PLUGIN_ROOT}/", "")
            if not target.exists():
                errors.append(f"{hooks_file}: {arg} does not exist")
    command = handler.get("command", "")
    if isinstance(command, str):
        for match in HOOK_COMMAND_PATH_RE.finditer(command):
            if not (root / match.group(1)).exists():
                errors.append(f"{hooks_file}: {match.group(0)} does not exist")
    return errors


def check_rules(root: Path) -> list[str]:
    return [
        f"{md}: more than 200 lines"
        for md in sorted(root.glob("rules/*.md"))
        if md.read_text(encoding="utf-8").count("\n") + 1 > 200
    ]


def check_catalog(root: Path) -> list[str]:
    path = root / "shared/catalog.md"
    if not path.exists():
        return []
    errors, in_table = [], False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("| Model |"):
            in_table = True
            continue
        if not line.startswith("|"):
            in_table = False
            continue
        if not in_table or set(line) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        where = f"{path}:{number}"
        if len(cells) != 8:
            errors.append(f"{where}: expected 8 cells, found {len(cells)}")
            continue
        status = cells[7]
        if status not in CATALOG_STATUS:
            errors.append(f"{where}: Status {status!r} must be verified or UNVERIFIED")
        elif status == "verified" and cells[2] != "—" and not ARXIV_RE.match(cells[2]):
            errors.append(f"{where}: verified row has invalid arXiv id {cells[2]!r}")
    return errors


def check_readme(root: Path) -> list[str]:
    """The README's component table and catalog counts must match the files."""
    path = root / "README.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    listed = {(kind.lower(), name) for kind, name in README_ROW_RE.findall(text)}
    present = {("skill", p.parent.name) for p in root.glob("skills/*/SKILL.md")}
    present |= {("agent", read_frontmatter(p)[0].get("name", p.stem)) for p in root.glob("agents/*.md")}
    errors = [f"README.md: no table row for {kind} {name!r}" for kind, name in sorted(present - listed)]
    errors += [f"README.md: table lists {kind} {name!r}, which does not exist" for kind, name in sorted(listed - present)]
    catalog = root / "shared/catalog.md"
    match = README_CATALOG_RE.search(text)
    if match and catalog.exists():
        statuses = [line.rstrip().rstrip("|").split("|")[-1].strip()
                    for line in catalog.read_text(encoding="utf-8").splitlines() if line.startswith("|")]
        counts = (statuses.count("verified") + statuses.count("UNVERIFIED"),
                  statuses.count("verified"), statuses.count("UNVERIFIED"))
        if tuple(int(n) for n in match.groups()) != counts:
            errors.append(f"README.md: catalog counts {match.group(0)!r} do not match shared/catalog.md "
                          f"({counts[0]} rows, {counts[1]} verified, {counts[2]} UNVERIFIED)")
    return errors


def check_local_paths(root: Path) -> list[str]:
    errors = []
    for name in SCAN_PATHS:
        base = root / name
        files = [base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []
        for file in files:
            if file.is_file() and file.suffix in SCAN_SUFFIXES and LOCAL_PATH_RE.search(file.read_text(encoding="utf-8")):
                errors.append(f"{file}: contains a local path")
    return errors


def run_checks(root: Path) -> list[str]:
    errors: list[str] = []
    for check in (check_skills, check_agents, check_manifests, check_rules, check_catalog, check_readme,
                  check_local_paths):
        errors += check(root)
    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path(__file__).resolve().parents[1]
    errors = run_checks(root)
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
