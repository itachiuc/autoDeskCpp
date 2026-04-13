#!/usr/bin/env python3
"""
update_build_version.py

Build-process utility that stamps the current BuildNum (from the environment)
into two source files:
  - SConstruct  : updates  point=<N>,
  - VERSION     : updates  ADLMSDK_VERSION_POINT=<N>
"""

import os
import re
import sys
import logging
import tempfile
from pathlib import Path
from dataclasses import dataclass

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FileUpdateSpec:
    """Describes how to find and patch a version line inside one file."""
    relative_path: str          # relative to src_root
    pattern:       str          # regex to match the line
    replacement:   str          # replacement string (may contain {build_num})

    def compiled_pattern(self) -> re.Pattern:
        return re.compile(self.pattern)

    def render_replacement(self, build_num: str) -> str:
        return self.replacement.format(build_num=build_num)


FILE_SPECS = [
    FileUpdateSpec(
        relative_path="SConstruct",
        pattern=r"point=\d+",
        replacement="point={build_num}",
    ),
    FileUpdateSpec(
        relative_path="VERSION",
        pattern=r"ADLMSDK_VERSION_POINT=\d+",
        replacement="ADLMSDK_VERSION_POINT={build_num}",
    ),
]

SRC_SUBDIR = Path("develop", "global", "src")


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def patch_file(file_path: Path, spec: FileUpdateSpec, build_num: str) -> bool:
    """
    Replaces all lines in *file_path* matching spec.pattern with the
    rendered replacement.

    Uses an atomic write (temp-file + rename) so the target is never left
    in a partial state if the process is interrupted.

    Returns True if at least one substitution was made, False otherwise.
    """
    pattern     = spec.compiled_pattern()
    replacement = spec.render_replacement(build_num)
    substitutions_made = 0

    # Write to a sibling temp-file; rename is atomic on POSIX
    dir_path = file_path.parent
    try:
        with (
            file_path.open("r", encoding="utf-8") as src,
            tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8",
                dir=dir_path, delete=False
            ) as tmp,
        ):
            tmp_path = Path(tmp.name)
            for line in src:
                new_line, n = pattern.subn(replacement, line)
                substitutions_made += n
                tmp.write(new_line)

    except OSError as exc:
        # Clean up the temp file if something went wrong mid-write
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to patch '{file_path}': {exc}") from exc

    # Preserve original permissions on the replacement file
    original_mode = file_path.stat().st_mode
    tmp_path.chmod(original_mode)

    # Atomic swap
    tmp_path.replace(file_path)

    return substitutions_made > 0


def update_version_files(src_root: Path, build_num: str) -> None:
    """Iterates over FILE_SPECS and patches each file."""
    for spec in FILE_SPECS:
        file_path = src_root / spec.relative_path
        log.info("Patching '%s' with build number %s …", file_path, build_num)

        if not file_path.is_file():
            raise FileNotFoundError(f"Expected file not found: '{file_path}'")

        changed = patch_file(file_path, spec, build_num)

        if changed:
            log.info("  ✓ Updated successfully.")
        else:
            # Warn but don't abort — the pattern might legitimately be absent
            # in some build configurations.
            log.warning(
                "  ⚠ No match found for pattern '%s' in '%s'. "
                "File was not modified.",
                spec.pattern, file_path,
            )


# ---------------------------------------------------------------------------
# Environment resolution
# ---------------------------------------------------------------------------

def resolve_env() -> tuple[Path, str]:
    """
    Reads required environment variables, validates them, and returns
    (src_root, build_num).
    """
    missing = [v for v in ("SourcePath", "BuildNum") if v not in os.environ]
    if missing:
        raise EnvironmentError(
            f"Required environment variable(s) not set: {', '.join(missing)}"
        )

    source_path = Path(os.environ["SourcePath"])
    build_num   = os.environ["BuildNum"].strip()

    if not source_path.is_dir():
        raise NotADirectoryError(f"SourcePath does not exist: '{source_path}'")

    if not build_num.isdigit():
        raise ValueError(
            f"BuildNum must be a non-negative integer; got: '{build_num}'"
        )

    src_root = source_path / SRC_SUBDIR
    if not src_root.is_dir():
        raise NotADirectoryError(f"Source root does not exist: '{src_root}'")

    return src_root, build_num


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    try:
        src_root, build_num = resolve_env()
        update_version_files(src_root, build_num)
        log.info("All files updated successfully.")
        return 0
    except (EnvironmentError, FileNotFoundError, NotADirectoryError, ValueError) as exc:
        log.error("Configuration error — %s", exc)
        return 1
    except RuntimeError as exc:
        log.error("Patch failed — %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())