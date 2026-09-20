from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NEW_PROJECT = REPO_ROOT / "scripts/new_logo_project.py"
VALIDATE = REPO_ROOT / "scripts/validate_logo_project.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        check=False,
        capture_output=True,
        text=True,
    )


def png_bytes(width: int, height: int) -> bytes:
    def chunk(name: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data))

    raw = b"".join(b"\x00" + b"\x00\x00\x00\xff" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def replace(path: Path, old: str, new: str) -> None:
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


class WorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.output_root = Path(self.temp.name)
        created = run(str(NEW_PROJECT), "sample-product", "--name", "Sample", "--output-root", str(self.output_root))
        self.assertEqual(created.returncode, 0, created.stderr)
        self.project = self.output_root / "sample-product"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_new_project_passes_structure_gate(self) -> None:
        result = run(str(VALIDATE), str(self.project), "--gate", "structure")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[PASS] structure", result.stdout)

    def test_new_project_does_not_overwrite(self) -> None:
        result = run(str(NEW_PROJECT), "sample-product", "--name", "Again", "--output-root", str(self.output_root))
        self.assertEqual(result.returncode, 2)
        self.assertIn("不会覆盖", result.stderr)

    def test_empty_project_is_blocked_at_intake(self) -> None:
        result = run(str(VALIDATE), str(self.project), "--gate", "intake")
        self.assertEqual(result.returncode, 1)
        self.assertIn("[BLOCKED] intake", result.stdout)

    def test_generation_gate_rejects_non_square_png(self) -> None:
        (self.project / "source/prd.md").write_text("# Product PRD\n", encoding="utf-8")

        brief = self.project / "01-brief.md"
        replace(brief, "brief_status: draft", "brief_status: ready")
        replace(
            brief,
            "| S01 | [待填写] | [待填写] | [待填写] | [待填写] |",
            "| S01 | source/prd.md | v1 | 是 | 测试来源 |",
        )

        directions = self.project / "02-directions.md"
        replace(directions, "direction_status: draft", "direction_status: approved")
        replace(directions, 'human_approved_by: ""', 'human_approved_by: "Tester"')
        replace(directions, 'human_approved_at: ""', 'human_approved_at: "2026-09-15T12:00:00+08:00"')
        replace(directions, "[方向名]", "测试方向")
        replace(directions, "- [ ]", "- [x]")

        records = []
        for direction_number in range(1, 4):
            direction = f"DIR-{direction_number:02d}"
            for candidate_number in range(1, 5):
                candidate_id = f"{direction}-C{candidate_number:02d}"
                relative = Path("candidates") / f"{candidate_id}.png"
                output = self.project / relative
                height = 32 if candidate_id == "DIR-03-C04" else 64
                output.write_bytes(png_bytes(64, height))
                records.append(
                    {
                        "candidate_id": candidate_id,
                        "direction_id": direction,
                        "created_at": "2026-09-15T12:00:00+08:00",
                        "tool": "test",
                        "model": "test-model",
                        "prompt_version": "v1",
                        "prompt": f"Prompt for {candidate_id}",
                        "input_references": [],
                        "output_path": str(relative),
                        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                    }
                )
        (self.project / "03-generation-log.jsonl").write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )

        result = run(str(VALIDATE), str(self.project), "--gate", "generation")
        self.assertEqual(result.returncode, 1)
        self.assertIn("DIR-03-C04: 首轮候选必须为方形，当前 64×32", result.stdout)

    def test_complete_fixture_passes_all_gates(self) -> None:
        (self.project / "source/prd.md").write_text("# Product PRD\n", encoding="utf-8")

        brief = self.project / "01-brief.md"
        replace(brief, "brief_status: draft", "brief_status: ready")
        replace(
            brief,
            "| S01 | [待填写] | [待填写] | [待填写] | [待填写] |",
            "| S01 | source/prd.md | v1 | 是 | 测试来源 |",
        )

        directions = self.project / "02-directions.md"
        replace(directions, "direction_status: draft", "direction_status: approved")
        replace(directions, 'human_approved_by: ""', 'human_approved_by: "Tester"')
        replace(directions, 'human_approved_at: ""', 'human_approved_at: "2026-09-15T12:00:00+08:00"')
        replace(directions, "[方向名]", "测试方向")
        replace(directions, "- [ ]", "- [x]")

        records = []
        for direction_number in range(1, 4):
            direction = f"DIR-{direction_number:02d}"
            for candidate_number in range(1, 5):
                candidate_id = f"{direction}-C{candidate_number:02d}"
                relative = Path("candidates") / f"{candidate_id}.png"
                output = self.project / relative
                output.write_bytes(png_bytes(64, 64))
                records.append(
                    {
                        "candidate_id": candidate_id,
                        "direction_id": direction,
                        "created_at": "2026-09-15T12:00:00+08:00",
                        "tool": "test",
                        "model": "test-model",
                        "prompt_version": "v1",
                        "prompt": f"Prompt for {candidate_id}",
                        "batch_variable": "composition",
                        "input_references": [],
                        "seed": None,
                        "output_path": str(relative),
                        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                        "notes": "",
                    }
                )
        (self.project / "03-generation-log.jsonl").write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )

        selected_relative = Path("selected/DIR-01-C01.png")
        (self.project / selected_relative).write_bytes((self.project / "candidates/DIR-01-C01.png").read_bytes())
        review = self.project / "04-review.md"
        replace(review, "review_status: draft", "review_status: approved")
        replace(review, 'retained_candidate_ids: ""', 'retained_candidate_ids: "DIR-01-C01"')
        replace(review, 'retained_asset_paths: ""', f'retained_asset_paths: "{selected_relative}"')
        replace(review, 'human_approved_by: ""', 'human_approved_by: "Tester"')
        replace(review, 'human_approved_at: ""', 'human_approved_at: "2026-09-15T13:00:00+08:00"')
        replace(review, "- [ ]", "- [x]")

        (self.project / "delivery/logo-master.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0h10v10H0z"/></svg>',
            encoding="utf-8",
        )
        (self.project / "delivery/logo-1024.png").write_bytes(png_bytes(1024, 1024))
        (self.project / "delivery/logo-32.png").write_bytes(png_bytes(32, 32))
        checklist = self.project / "05-delivery-checklist.md"
        replace(checklist, "delivery_status: draft", "delivery_status: validated")
        replace(checklist, 'validated_at: ""', 'validated_at: "2026-09-15T14:00:00+08:00"')
        replace(checklist, 'validated_by: ""', 'validated_by: "Tester"')
        required, optional = checklist.read_text(encoding="utf-8").split("## 按需项", maxsplit=1)
        checklist.write_text(required.replace("- [ ]", "- [x]") + "## 按需项" + optional, encoding="utf-8")

        result = run(str(VALIDATE), str(self.project), "--gate", "all")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[PASS] delivery", result.stdout)


if __name__ == "__main__":
    unittest.main()
