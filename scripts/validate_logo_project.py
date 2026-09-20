#!/usr/bin/env python3
"""Validate evidence and delivery gates for a logo workflow project."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


GATE_ORDER = (
    "structure",
    "intake",
    "brief",
    "directions",
    "generation",
    "selection",
    "delivery",
)
REQUIRED_FILES = (
    "01-brief.md",
    "02-directions.md",
    "03-generation-log.jsonl",
    "03-calibration-log.md",
    "04-review.md",
    "05-delivery-checklist.md",
    "evidence.md",
)
REQUIRED_DIRECTORIES = ("source", "candidates", "selected", "review", "delivery")
GENERATION_FIELDS = (
    "candidate_id",
    "direction_id",
    "created_at",
    "tool",
    "model",
    "prompt_version",
    "prompt",
    "input_references",
    "output_path",
    "output_sha256",
)


@dataclass
class GateResult:
    name: str
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


def text_field(path: Path, field_name: str) -> str:
    if not path.is_file():
        return ""
    pattern = re.compile(rf"^{re.escape(field_name)}:\s*(.*?)\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip('"').strip("'")
    return ""


def require_status(result: GateResult, path: Path, field_name: str, expected: str) -> None:
    actual = text_field(path, field_name)
    if actual != expected:
        result.errors.append(f"{path.name}: {field_name} 应为 {expected!r}，当前为 {actual!r}")


def require_human_approval(result: GateResult, path: Path) -> None:
    for field_name in ("human_approved_by", "human_approved_at"):
        if not text_field(path, field_name):
            result.errors.append(f"{path.name}: 缺少 {field_name}")


def is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(24)
    except OSError:
        return None
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", header[16:24])


def required_checkboxes(text: str) -> list[str]:
    match = re.search(r"^## 必需项\s*$([\s\S]*?)(?=^## |\Z)", text, flags=re.MULTILINE)
    if not match:
        return ["缺少“必需项”章节"]
    return [
        line.strip()
        for line in match.group(1).splitlines()
        if re.match(r"^- \[ \]", line.strip())
    ]


def validate_structure(root: Path) -> GateResult:
    result = GateResult("structure")
    if not root.is_dir():
        result.errors.append(f"项目目录不存在：{root}")
        return result
    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            result.errors.append(f"缺少文件：{name}")
    for name in REQUIRED_DIRECTORIES:
        if not (root / name).is_dir():
            result.errors.append(f"缺少目录：{name}/")
    return result


def validate_intake(root: Path) -> GateResult:
    result = GateResult("intake")
    source_files = [path for path in (root / "source").rglob("*") if path.is_file()]
    if not source_files:
        result.errors.append("source/ 中还没有 PRD 或等价来源文件")
    return result


def validate_brief(root: Path) -> GateResult:
    result = GateResult("brief")
    path = root / "01-brief.md"
    require_status(result, path, "brief_status", "ready")
    if path.is_file():
        rows = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if re.match(r"^\| S\d+ \|", line) and "[待填写]" not in line
        ]
        if not rows:
            result.errors.append("01-brief.md: 来源索引中没有已填写的 Sxx 记录")
    return result


def validate_directions(root: Path) -> GateResult:
    result = GateResult("directions")
    path = root / "02-directions.md"
    require_status(result, path, "direction_status", "approved")
    require_human_approval(result, path)
    if not path.is_file():
        return result
    text = path.read_text(encoding="utf-8")
    titles = re.findall(r"^## (DIR-[A-Za-z0-9-]+) · (.+)$", text, flags=re.MULTILINE)
    active = [(direction, title) for direction, title in titles if "[方向名]" not in title]
    if not active:
        result.errors.append("02-directions.md: 至少需要一个正式方向")
    if re.search(r"^- \[ \]", text, flags=re.MULTILINE):
        result.errors.append("02-directions.md: 策略确认仍有未勾选项")
    return result


def load_generation_records(path: Path, result: GateResult) -> list[dict]:
    records: list[dict] = []
    if not path.is_file():
        return records
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            result.errors.append(f"03-generation-log.jsonl:{line_number}: JSON 无效：{error.msg}")
            continue
        if not isinstance(record, dict):
            result.errors.append(f"03-generation-log.jsonl:{line_number}: 每行必须是 JSON object")
            continue
        missing = [field for field in GENERATION_FIELDS if field not in record]
        if missing:
            result.errors.append(
                f"03-generation-log.jsonl:{line_number}: 缺少字段 {', '.join(missing)}"
            )
            continue
        records.append(record)
    return records


def validate_generation(root: Path) -> GateResult:
    result = GateResult("generation")
    records = load_generation_records(root / "03-generation-log.jsonl", result)
    candidate_ids: set[str] = set()
    for record in records:
        candidate_id = str(record["candidate_id"])
        if candidate_id in candidate_ids:
            result.errors.append(f"候选 ID 重复：{candidate_id}")
        candidate_ids.add(candidate_id)

        direction = str(record["direction_id"])
        if not re.fullmatch(r"DIR-[A-Za-z0-9-]+", direction):
            result.errors.append(f"{candidate_id}: direction_id 无效：{direction}")

        output = root / str(record["output_path"])
        if not is_inside(output, root):
            result.errors.append(f"{candidate_id}: output_path 超出项目目录")
        elif not output.is_file():
            result.errors.append(f"{candidate_id}: 输出不存在：{record['output_path']}")
        else:
            if sha256(output) != str(record["output_sha256"]):
                result.errors.append(f"{candidate_id}: output_sha256 与当前文件不一致")
            actual_size = png_size(output)
            if actual_size is None:
                result.errors.append(f"{candidate_id}: 输出不是有效 PNG")
            elif actual_size[0] != actual_size[1]:
                result.errors.append(
                    f"{candidate_id}: 首轮候选必须为方形，当前 {actual_size[0]}×{actual_size[1]}"
                )

        for field_name in ("created_at", "tool", "model", "prompt_version", "prompt"):
            if not str(record[field_name]).strip():
                result.errors.append(f"{candidate_id}: {field_name} 不能为空")
        if not isinstance(record["input_references"], list):
            result.errors.append(f"{candidate_id}: input_references 必须是数组")

    if not records:
        result.errors.append("03-generation-log.jsonl: 至少需要一个有记录的候选")
    return result


def validate_selection(root: Path) -> GateResult:
    result = GateResult("selection")
    path = root / "04-review.md"
    require_status(result, path, "review_status", "approved")
    require_human_approval(result, path)
    candidate_ids = [value.strip() for value in text_field(path, "retained_candidate_ids").split(",") if value.strip()]
    selected_paths = [value.strip() for value in text_field(path, "retained_asset_paths").split(",") if value.strip()]
    if not candidate_ids:
        result.errors.append("04-review.md: 缺少 retained_candidate_ids")
    if len(candidate_ids) != len(selected_paths):
        result.errors.append("04-review.md: retained_candidate_ids 与 retained_asset_paths 数量不一致")
    for selected_path in selected_paths:
        selected = root / selected_path
        if not is_inside(selected, root) or not selected.is_file():
            result.errors.append(f"04-review.md: 保留资产不存在或路径越界：{selected_path}")

    generation_result = GateResult("generation-records")
    records = load_generation_records(root / "03-generation-log.jsonl", generation_result)
    known_ids = {str(record.get("candidate_id")) for record in records}
    for candidate_id in candidate_ids:
        if candidate_id not in known_ids:
            result.errors.append(f"04-review.md: 保留候选未出现在生成记录中：{candidate_id}")
    if path.is_file() and re.search(r"^- \[ \]", path.read_text(encoding="utf-8"), flags=re.MULTILINE):
        result.errors.append("04-review.md: 淘汰门禁仍有未勾选项")
    return result


def validate_delivery(root: Path) -> GateResult:
    result = GateResult("delivery")
    checklist = root / "05-delivery-checklist.md"
    require_status(result, checklist, "delivery_status", "validated")
    for field_name in ("validated_by", "validated_at"):
        if not text_field(checklist, field_name):
            result.errors.append(f"05-delivery-checklist.md: 缺少 {field_name}")

    svg = root / "delivery/logo-master.svg"
    if not svg.is_file():
        result.errors.append("缺少 delivery/logo-master.svg")
    else:
        try:
            tree = ET.parse(svg)
            if not tree.getroot().tag.lower().endswith("svg"):
                result.errors.append("delivery/logo-master.svg: 根元素不是 svg")
            if any(element.tag.lower().endswith("image") for element in tree.iter()):
                result.errors.append("delivery/logo-master.svg: 包含 image 元素，可能嵌入了位图")
        except ET.ParseError as error:
            result.errors.append(f"delivery/logo-master.svg: XML 无效：{error}")

    for name, expected in (("logo-1024.png", (1024, 1024)), ("logo-32.png", (32, 32))):
        path = root / "delivery" / name
        actual = png_size(path)
        if actual is None:
            result.errors.append(f"delivery/{name}: 缺失或不是有效 PNG")
        elif actual != expected:
            result.errors.append(f"delivery/{name}: 应为 {expected[0]}×{expected[1]}，当前 {actual[0]}×{actual[1]}")

    if checklist.is_file():
        unchecked = required_checkboxes(checklist.read_text(encoding="utf-8"))
        if unchecked:
            result.errors.append(f"05-delivery-checklist.md: 必需项仍有 {len(unchecked)} 项未勾选")
    return result


VALIDATORS = {
    "structure": validate_structure,
    "intake": validate_intake,
    "brief": validate_brief,
    "directions": validate_directions,
    "generation": validate_generation,
    "selection": validate_selection,
    "delivery": validate_delivery,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="由 new_logo_project.py 创建的项目目录")
    parser.add_argument("--gate", choices=(*GATE_ORDER, "all"), default="all")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_index = len(GATE_ORDER) - 1 if args.gate == "all" else GATE_ORDER.index(args.gate)
    results = [VALIDATORS[name](args.project) for name in GATE_ORDER[: target_index + 1]]
    for result in results:
        label = "PASS" if result.passed else "BLOCKED"
        print(f"[{label}] {result.name}")
        for error in result.errors:
            print(f"  - {error}")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
