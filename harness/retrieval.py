"""Small local discovery helper: bounded hits first, explicit expansion on demand."""
from __future__ import annotations

import argparse
import json
import pathlib
import re


def find(paths: list[pathlib.Path], term: str, limit: int = 8, expand: bool = False) -> dict:
    if limit < 1:
        raise ValueError("limit must be positive")
    hits = []
    total = 0
    missing = []
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    for path in paths:
        if not path.is_file():
            missing.append(str(path))
            continue
        with path.open("r", encoding="utf-8", errors="replace") as source:
            for number, raw_line in enumerate(source, 1):
                line = raw_line.rstrip("\r\n")
                if pattern.search(line):
                    total += 1
                    if expand or len(hits) < limit:
                        hits.append({"path": str(path), "line": number,
                                     "excerpt": line if expand else line[:240],
                                     "line_truncated": not expand and len(line) > 240})
    return {"term": term, "hits": hits, "total_hits": total, "truncated": total > len(hits),
            "expand_command": "rerun with --expand" if total > len(hits) or any(h["line_truncated"] for h in hits) else None,
            "missing_paths": missing,
            "source_paths": [str(p) for p in paths]}


def read_lines(path: pathlib.Path, start: int, end: int) -> dict:
    """Read one exact source interval after discovery, without expanding other hits."""
    if start < 1 or end < start:
        raise ValueError("line range must have positive start and end >= start")
    if not path.is_file():
        raise FileNotFoundError(path)
    lines = []
    with path.open("r", encoding="utf-8", errors="replace") as source:
        for number, raw_line in enumerate(source, 1):
            if number > end:
                break
            if number >= start:
                lines.append({"line": number, "text": raw_line.rstrip("\r\n")})
    return {"path": str(path), "start": start, "end": end, "lines": lines,
            "complete_range": bool(lines) and lines[-1]["line"] == end}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("term", nargs="?")
    p.add_argument("paths", nargs="*", type=pathlib.Path)
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--expand", action="store_true")
    p.add_argument("--read-lines", nargs=3, metavar=("PATH", "START", "END"))
    a = p.parse_args()
    if a.read_lines:
        if a.term is not None or a.paths or a.expand:
            p.error("--read-lines cannot be combined with search arguments")
        path, start, end = a.read_lines
        result = read_lines(pathlib.Path(path), int(start), int(end))
    else:
        if not a.term or not a.paths:
            p.error("search requires TERM and at least one PATH")
        result = find(a.paths, a.term, a.limit, a.expand)
    print(json.dumps(result, ensure_ascii=False))
