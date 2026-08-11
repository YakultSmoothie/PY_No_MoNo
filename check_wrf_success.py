#!/usr/bin/env python3
"""
Check WRF member completion from member*/rsl.error.0000 files.

Default behavior is equivalent to checking:
    tail -n 1 member*/rsl.error.0000

Example:
    python check_wrf_success.py
    python check_wrf_success.py --member-count 64
    python check_wrf_success.py /work/u2292799/work/2026-0721-ETKF_to_d04/RUN-forecast/WRF-RUN/run1
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional, Tuple, Union


SUCCESS_TEXT = "SUCCESS COMPLETE WRF"
RUNNING_TEXT = "Timing for main"


def read_last_line(path: Path) -> str:
    """Return the last line of a text file, or an empty string for empty files."""
    last_line = ""
    with path.open("r", encoding="utf-8", errors="replace") as file_obj:
        for line in file_obj:
            last_line = line.rstrip("\r\n")
    return last_line


def natural_member_key(path: Path) -> Tuple[str, Union[int, str]]:
    """Sort member1, member2, ... member10 in numerical order when possible."""
    member_name = path.parent.name
    digits = "".join(ch for ch in member_name if ch.isdigit())
    if digits:
        return member_name.rstrip(digits), int(digits)
    return member_name, member_name


def build_expected_files(run_dir: Path, member_count: Optional[int]) -> List[Path]:
    if member_count is None:
        return sorted(run_dir.glob("member*/rsl.error.0000"), key=natural_member_key)

    width = max(3, len(str(member_count)))
    return [
        run_dir / f"member{member_id:0{width}d}" / "rsl.error.0000"
        for member_id in range(1, member_count + 1)
    ]


def check_members(
    run_dir: Path,
    pattern: str,
    success_text: str,
    running_text: str,
    member_count: Optional[int],
) -> int:
    if member_count is None:
        rsl_files = sorted(run_dir.glob(pattern), key=natural_member_key)
    else:
        rsl_files = build_expected_files(run_dir, member_count)

    if not rsl_files:
        print(f"No files matched: {run_dir / pattern}")
        return 2

    success_count = 0
    running_count = 0
    not_started_count = 0
    error_count = 0

    for rsl_file in rsl_files:
        member_name = rsl_file.parent.name

        if not rsl_file.exists():
            not_started_count += 1
            print(f"[WAIT] {member_name:<12} rsl.error.0000 not found")
            continue

        try:
            last_line = read_last_line(rsl_file)
        except OSError as exc:
            error_count += 1
            print(f"[ERR ] {member_name:<12} {rsl_file} : {exc}")
            continue

        if success_text in last_line:
            success_count += 1
            print(f"[ OK ] {member_name:<12} {last_line}")
        elif not last_line:
            not_started_count += 1
            print(f"[WAIT] {member_name:<12} rsl.error.0000 is empty")
        elif running_text in last_line:
            running_count += 1
            print(f"[RUN ] {member_name:<12} {last_line}")
        else:
            error_count += 1
            print(f"[MISS] {member_name:<12} {last_line}")

    total_count = success_count + running_count + not_started_count + error_count
    print()
    print(f"success     = {success_count}")
    print(f"running     = {running_count}")
    print(f"not_started = {not_started_count}")
    print(f"error       = {error_count}")
    print(f"total       = {total_count}")

    return 0 if running_count == 0 and not_started_count == 0 and error_count == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count completed WRF members from the final line of rsl.error.0000 files."
    )
    parser.add_argument(
        "run_dir",
        nargs="?",
        default=".",
        help="WRF run directory containing member*/rsl.error.0000 files. Default: current directory.",
    )
    parser.add_argument(
        "--pattern",
        default="member*/rsl.error.0000",
        help="Glob pattern under run_dir. Default: member*/rsl.error.0000",
    )
    parser.add_argument(
        "--success-text",
        default=SUCCESS_TEXT,
        help=f"Text expected in the last line. Default: {SUCCESS_TEXT!r}",
    )
    parser.add_argument(
        "--running-text",
        default=RUNNING_TEXT,
        help=f"Text treated as still running in the last line. Default: {RUNNING_TEXT!r}",
    )
    parser.add_argument(
        "--member-count",
        type=int,
        help="Expected member count. Use this to report members whose rsl.error.0000 has not been created yet.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser()

    if not run_dir.is_dir():
        print(f"Run directory does not exist: {run_dir}")
        return 2

    return check_members(
        run_dir,
        args.pattern,
        args.success_text,
        args.running_text,
        args.member_count,
    )


if __name__ == "__main__":
    raise SystemExit(main())
