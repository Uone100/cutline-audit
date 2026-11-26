# Cutline Audit

Find where an exported subtitle track diverges from a recut timeline. Give it the original SRT, **actual kept source ranges in export order**, and the exported SRT. Each timing finding identifies the source subtitle, kept segment, exported subtitle and timing error in milliseconds. Runs locally with Python 3.9+ and its standard library.

[Download v0.1.0 ZIP](https://github.com/Uone100/cutline-audit/releases/download/v0.1.0/cutline-audit-0.1.0.zip)

Extract the ZIP and follow the worked example below with Python 3.9 or newer.

## Try a known failure

Download the versioned ZIP under **Assets**, unzip it, and run from the extracted directory. [Latest release](https://github.com/Uone100/cutline-audit/releases/latest)

```sh
python cutline_audit.py examples/source.srt examples/keep.csv examples/export.srt
```

The example removes four seconds from a recording. In segment 2, the last subtitle starts and ends **250 ms late**. Change the exported times to 00:00:03,500 and 00:00:05,000 to see a passing report. Use `--tolerance-ms 40` for a 40 ms allowance. Exit codes are 0 for a match, 1 for differences, and 2 for invalid input.

## What it checks

The first two CSV columns are start and end in decimal seconds, with an optional Start,End header. Each range represents an actual interval kept from one 1× source. Reordered and repeated intervals are supported. If a keyframe moved the cut, enter the measured range. A mismatch establishes disagreement with the supplied ranges; it does not establish sync with speech in the video.

Cues are clipped to each range and placed consecutively in export order. Gaps, edits to dialogue and inserted cues are reported as sequence differences. Wrapping and whitespace are normalized. Repeated identical dialogue can make alignment ambiguous; inspect adjacent cues. If the editor intentionally joins two fragments across a cut, the output flags that for review. Inputs are plain UTF-8 SRT files with timestamps and text. All comparisons are read-only.

Run `python -m unittest -v` to check the example and boundary cases. The workflow is motivated by a real request for subtitle synchronization and the accompanying sidecar workaround. [LosslessCut discussion and worked example](https://github.com/mifi/lossless-cut/issues/3209)
