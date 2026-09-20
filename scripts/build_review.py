#!/usr/bin/env python3
"""Build an offline, version-bound logo review and Figma handoff. Stdlib only."""
import argparse
import base64
import hashlib
import json
import re
import shutil
import struct
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
FILTER = re.compile(r"(?:hue-rotate\(-?\d+(?:\.\d+)?deg\)|(?:grayscale|brightness|contrast)\(\d+(?:\.\d+)?\))(?: (?:hue-rotate\(-?\d+(?:\.\d+)?deg\)|(?:grayscale|brightness|contrast)\(\d+(?:\.\d+)?\)))*$")


def prepare(path):
    root = path.resolve().parent
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("schemaVersion") == 1, "schemaVersion must be 1"
    for key in ("project", "revision"):
        assert isinstance(data.get(key), str) and data[key].strip(), f"missing {key}"
    assets = {}

    def asset(name):
        assert isinstance(name, str), "asset path must be string"
        file = (root / name).resolve()
        assert file.is_relative_to(root), f"asset outside project: {name}"
        raw = file.read_bytes()
        assert len(raw) >= 33 and raw[:8] == b"\x89PNG\r\n\x1a\n" and raw[12:16] == b"IHDR", f"not PNG: {name}"
        w, h = struct.unpack(">II", raw[16:24])
        assert 0 < w <= 16384 and 0 < h <= 16384, f"invalid size: {name}"
        assert len(raw) <= 16 * 1024 * 1024, f"asset over 16MB: {name}"
        assets[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "width": w, "height": h,
                        "data": "data:image/png;base64," + base64.b64encode(raw).decode()}

    def numbers(values, count):
        return isinstance(values, list) and len(values) == count and all(type(v) in (int, float) and abs(v) <= 2000 for v in values)

    concepts = data.get("concepts")
    assert isinstance(concepts, list) and 0 < len(concepts) <= 30, "require 1–30 concepts"
    ids = set()
    for c in concepts:
        for key in ("id", "title", "version", "concept", "changes", "status"):
            assert isinstance(c.get(key), str) and c[key].strip(), f"concept missing {key}"
        assert c["id"] not in ids, "duplicate concept id"
        ids.add(c["id"])
        assert c["status"] in ("exploration", "retained", "parked"), "invalid status"
        p = c["placement"]
        assert p["mode"] in ("contain", "full-bleed"), "invalid placement mode"
        p.setdefault("scale", .8 if p["mode"] == "contain" else 1)
        p.setdefault("x", (1 - p["scale"]) / 2)
        p.setdefault("y", (1 - p["scale"]) / 2)
        p.setdefault("background", "#ffffff")
        assert numbers([p["scale"], p["x"], p["y"]], 3) and 0 < p["scale"] <= 4, "invalid placement"
        assert re.fullmatch(r"#[0-9a-fA-F]{6}", p["background"]), "use 6-digit background hex"
        if c.get("previous"):
            asset(c["previous"])
        assert isinstance(c.get("palettes"), list) and 0 < len(c["palettes"]) <= 12, "require 1–12 palettes"
        palette_ids = set()
        for pal in c["palettes"]:
            assert pal.get("id") and pal["id"] not in palette_ids, "invalid/duplicate palette id"
            palette_ids.add(pal["id"])
            assert pal.get("label"), "missing palette label"
            assert pal["kind"] in ("original", "color-artwork", "filter-preview", "grayscale-preview", "monochrome-artwork"), "invalid palette kind"
            if pal["kind"] == "monochrome-artwork":
                assert pal.get("humanReviewed") is True, "monochrome requires real human review"
            pal.setdefault("filter", "none")
            assert pal["filter"] == "none" or FILTER.fullmatch(pal["filter"]), "unsupported filter"
            if pal["kind"] in ("original", "color-artwork", "monochrome-artwork"):
                assert pal["filter"] == "none", "artwork cannot hide a preview filter"
            asset(pal["asset"])
    assert any(c["status"] != "parked" for c in concepts), "no active concepts"
    scene = data.get("scene")
    if scene:
        assert scene.get("label"), "scene needs source/label"
        assert 100 <= scene["width"] <= 2000 and 100 <= scene["height"] <= 3000, "invalid scene size"
        assert numbers(scene["slot"], 3) and scene["slot"][2] > 0, "invalid icon slot"
        x, y, w = scene["slot"]
        assert x >= 0 and y >= 0 and x + w <= 100 and y + w * scene["width"] / scene["height"] <= 100, "slot outside phone"
        for name in ("background", "overlay"):
            if scene.get(name):
                asset(scene[name])
                assert numbers(scene[name + "Rect"], 4) and min(scene[name + "Rect"][2:]) > 0, "invalid scene rect"
    data["assets"] = assets
    assert sum(len(a["data"]) for a in assets.values()) < 80 * 1024 * 1024, "review too large; split batch"
    data["snapshotBase"] = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        data = prepare(args.manifest)
        if args.check:
            print(f"PASS: {len(data['concepts'])} concepts, {len(data['assets'])} PNG assets; visual/human review not implied")
            return
        assert args.out and not args.out.exists(), "--out must be a new directory"
        html = (SKILL / "assets/review.html").read_text(encoding="utf-8")
        payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
        args.out.mkdir(parents=True)
        (args.out / "index.html").write_text(html.replace("__REVIEW_DATA__", payload), encoding="utf-8")
        shutil.copytree(SKILL / "assets/figma-plugin", args.out / "figma-plugin")
        print(args.out.resolve() / "index.html")
    except (AssertionError, KeyError, ValueError, OSError, TypeError) as error:
        parser.exit(1, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
