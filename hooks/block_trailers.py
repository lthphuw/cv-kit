#!/usr/bin/env python3
"""PreToolUse hook: deny git/svn commits whose message carries a trailer."""
from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

TRAILER_RE = re.compile(
    r"(?i)(?:^|[\s\"']|\\[nrt])(?:co-authored-by|signed-off-by|generated-by|claude-session|acked-by|"
    r"(?:review|reviewed|tested|reported|suggested|helped|patch|found)[ -]by):\s*\S"
)
# "Generated with" counts only at the start of a line, of a quoted message, or after a literal \n,
# so "Add anchors generated with k-means" is allowed. The robot emoji is matched anywhere.
GENERATED_RE = re.compile(r"(?im)(?:^|[\"']|\\[nrt])[ \t]*generated with|🤖")
SHORT_SIGNOFF_RE = re.compile(r"-[A-Za-z]*s[A-Za-z]*")
SEPARATOR_RE = re.compile(r"[;&|<>()]+")
FALLBACK_TOKEN_RE = re.compile(r"[;&|<>()]+|[^\s;&|<>()]+")
HEREDOC_RE = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _without_heredoc_bodies(command: str) -> str:
    """Drop each heredoc body that has a terminator line; a `<<WORD` without one hides nothing."""
    lines = command.split("\n")
    kept = []
    index = 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        match = HEREDOC_RE.search(line)
        if match is None:
            continue
        terminator = next(
            (end for end in range(index, len(lines)) if lines[end].strip() == match.group(2)), None
        )
        if terminator is not None:
            index = terminator + 1
    return "\n".join(kept)


def _tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        # An unbalanced quote in the command itself. Split the separators out so
        # the segments below still end at each shell operator.
        return FALLBACK_TOKEN_RE.findall(command)


def _segments(tokens: list[str]) -> list[list[str]]:
    """Split tokens at shell operators, so each list is one simple command."""
    segments: list[list[str]] = [[]]
    for token in tokens:
        if SEPARATOR_RE.fullmatch(token):
            segments.append([])
        else:
            segments[-1].append(token)
    return segments


def _commit_in_segment(segment: list[str]) -> tuple[str, list[str]] | None:
    for index, token in enumerate(segment):
        if token == "commit" and "git" in segment[:index]:
            return "git", segment[index + 1 :]
        if token in ("commit", "ci") and "svn" in segment[:index]:
            return "svn", segment[index + 1 :]
    return None


def commit_args(command: str) -> list[tuple[str, list[str]]]:
    """Return (vcs, args) for every commit in the command, args stopping at the next operator."""
    commits = []
    for segment in _segments(_tokens(_without_heredoc_bodies(command))):
        found = _commit_in_segment(segment)
        if found is not None:
            commits.append(found)
    return commits


def _message_files(args: list[str]) -> list[str]:
    files = []
    for index, arg in enumerate(args):
        if arg in ("-F", "--file") and index + 1 < len(args):
            files.append(args[index + 1])
        elif arg.startswith("--file="):
            files.append(arg.split("=", 1)[1])
    return files


def violations(command: str, cwd: str) -> list[str]:
    commits = commit_args(command)
    if not commits:
        return []
    texts = [command]
    for _, args in commits:
        for name in _message_files(args):
            path = Path(cwd) / name
            if name != "-" and path.is_file():
                texts.append(path.read_text(encoding="utf-8", errors="replace"))
    found = []
    for text in texts:
        if TRAILER_RE.search(text):
            found.append("a trailer line (Co-Authored-By, Signed-off-by, ...)")
        if GENERATED_RE.search(text):
            found.append("a 'Generated with' attribution")
    for vcs, args in commits:
        if vcs == "git":
            for arg in args:
                if arg in ("--signoff", "--trailer") or arg.startswith("--trailer="):
                    found.append(f"the {arg.split('=')[0]} flag")
                elif SHORT_SIGNOFF_RE.fullmatch(arg):
                    found.append("the -s (sign-off) flag")
    return sorted(set(found))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return 0
    cwd = payload.get("cwd")
    found = violations(command, cwd if isinstance(cwd, str) else ".")
    if not found:
        return 0
    print(
        "Commit blocked: the message contains " + "; ".join(found) + ". "
        "A commit message is a subject line plus an optional body, with no trailers. "
        "Rewrite the message without them and commit again. "
        "If the hook blocks a line you were instructed to add and cannot drop "
        "(for example a managed attribution policy), stop and tell the user; do not retry.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
