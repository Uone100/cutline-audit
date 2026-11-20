"""Build the downloadable release without including local data or caches."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import sys

root = Path(__file__).resolve().parent
files = ["README.md", "cutline_audit.py", "test_cutline.py",
         "examples/keep.csv", "examples/source.srt", "examples/export.srt"]
if __name__ == "__main__":
    with ZipFile(sys.argv[1], "x") as archive:
        for name in files:
            entry = ZipInfo(name)
            entry.compress_type = ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, (root / name).read_bytes())
