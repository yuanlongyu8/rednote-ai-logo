#!/usr/bin/env python3
"""Create a new traceable RedNote AI Logo project."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "project-template"
TEMPLATE_MAP = {
    "01-brief.md": "01-brief.md",
    "02-directions.md": "02-directions.md",
    "03-calibration-log.md": "03-calibration-log.md",
    "04-review.md": "04-review.md",
    "05-delivery-checklist.md": "05-delivery-checklist.md",
    "evidence.md": "evidence.md",
}
DIRECTORIES = ("source", "candidates", "selected", "review", "delivery")


def valid_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", value):
        raise argparse.ArgumentTypeError(
            "slug 只能包含小写字母、数字和连字符，且必须以字母或数字开头"
        )
    return value


def render_template(source: Path, values: dict[str, str]) -> str:
    rendered = source.read_text(encoding="utf-8")
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered


def create_project(slug: str, name: str, output_root: Path) -> Path:
    destination = output_root / slug
    if destination.exists():
        raise FileExistsError(f"目标已存在，不会覆盖：{destination}")

    destination.mkdir(parents=True)
    for directory in DIRECTORIES:
        (destination / directory).mkdir()

    values = {
        "PROJECT_SLUG": slug,
        "PROJECT_NAME": name,
        "CREATED_AT": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    for target_name, template_name in TEMPLATE_MAP.items():
        content = render_template(TEMPLATE_ROOT / template_name, values)
        (destination / target_name).write_text(content, encoding="utf-8")

    (destination / "03-generation-log.jsonl").touch()
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", type=valid_slug, help="项目目录名，例如 phase-now")
    parser.add_argument("--name", required=True, help="展示名称，例如 PhaseNow")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd() / "projects",
        help="项目根目录；默认是当前目录下的 projects/",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        destination = create_project(args.slug, args.name, args.output_root)
    except FileExistsError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(f"Created logo workflow project: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
