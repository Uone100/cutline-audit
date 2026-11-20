"""Audit an exported SRT against source cues and the actual kept video ranges."""
import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from difflib import SequenceMatcher
from pathlib import Path


@dataclass(frozen=True)
class Cue:
    start: int
    end: int
    text: str
    source_block: int
    segment: int = 0


STAMP = r"(\d{2,}):([0-5]\d):([0-5]\d)[,.](\d{3})"
TIMELINE = re.compile(STAMP + r"\s*-->\s*" + STAMP)


def milliseconds(parts):
    h, m, s, ms = map(int, parts)
    return ((h * 60 + m) * 60 + s) * 1000 + ms


def subtitles(path):
    raw = path.read_text(encoding="utf-8-sig").strip()
    cues = []
    for number, block in enumerate(re.split(r"\n[ \t]*\n+", raw) if raw else [], 1):
        lines = block.splitlines()
        if lines[0].strip().isdigit():
            lines = lines[1:]
        match = TIMELINE.fullmatch(lines[0].strip()) if len(lines) >= 2 else None
        if not match:
            raise ValueError(f"{path.name}: invalid timeline or text at block {number}")
        start, end = milliseconds(match.groups()[:4]), milliseconds(match.groups()[4:])
        if start >= end:
            raise ValueError(f"{path.name}: nonpositive cue at block {number}")
        cues.append(Cue(start, end, "\n".join(lines[1:]), number))
    return sorted(cues, key=lambda c: c.start)


def ranges(path):
    result = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.reader(stream, strict=True):
            if not row or not any(x.strip() for x in row):
                continue
            if not result and [v.strip().lower() for v in row[:2]] == ["start", "end"]:
                continue
            if len(row) < 2:
                raise ValueError("Each CSV record needs start and end in seconds")
            times = [Decimal(x.strip()) for x in row[:2]]
            if not all(t.is_finite() and t >= 0 for t in times):
                raise ValueError("Invalid source time")
            start, end = [int((t*1000).to_integral_value(rounding=ROUND_HALF_UP)) for t in times]
            if end <= start:
                raise ValueError("Each kept range must last at least one millisecond")
            result.append((start, end))
    if not result:
        raise ValueError("Empty keep list")
    return result


def project(source, kept):
    expected = []
    offset = 0
    for segment, (start, end) in enumerate(kept, 1):
        for cue in source:
            if cue.start >= end:
                break
            left, right = max(start, cue.start), min(end, cue.end)
            if left < right:
                expected.append(Cue(offset + left-start, offset + right-start, cue.text,
                                    cue.source_block, segment))
        offset += end-start
    return expected


def audit(expected, actual, tolerance):
    # Whitespace and line wrap can change on export. Keep case, markup and words significant.
    def key(cue):
        return " ".join(cue.text.split())
    alignment = SequenceMatcher(None, list(map(key, expected)), list(map(key, actual)), autojunk=False)
    issues = []
    for op, i, j, k, l in alignment.get_opcodes():
        if op != "equal":
            issues.append(dict(kind=op, expected=[dict(segment=c.segment, source_block=c.source_block,
                                                        start_ms=c.start, end_ms=c.end) for c in expected[i:j]],
                               exported_blocks=[c.source_block for c in actual[k:l]]))
            continue
        for a,b in zip(expected[i:j],actual[k:l]):
            start_drift, end_drift = b.start-a.start,b.end-a.end
            if max(abs(start_drift),abs(end_drift)) > tolerance:
                issues.append(dict(kind="timing", segment=a.segment, source_block=a.source_block,
                                   exported_block=b.source_block, expected_start_ms=a.start,
                                   expected_end_ms=a.end, start_drift_ms=start_drift,end_drift_ms=end_drift))
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "kept_csv", "exported"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--tolerance-ms", type=int, default=0)
    args = parser.parse_args()
    if args.tolerance_ms < 0:
        parser.error("Tolerance must be nonnegative")
    try:
        expected = project(subtitles(args.source), ranges(args.kept_csv))
        actual = subtitles(args.exported)
        issues = audit(expected, actual, args.tolerance_ms)
    except (OSError, ValueError, InvalidOperation, csv.Error) as err:
        parser.exit(2, f"Input error: {err}\n")
    print(json.dumps(dict(result="review" if issues else "pass", expected_cues=len(expected),
                          exported_cues=len(actual), tolerance_ms=args.tolerance_ms,
                          differences=issues), indent=2))
    return int(bool(issues))


if __name__ == "__main__":
    sys.exit(main())
