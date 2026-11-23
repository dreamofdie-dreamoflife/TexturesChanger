import hashlib
import json
from pathlib import Path
import struct
import subprocess

root = Path(__file__).resolve().parents[2]
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
assets = []
def asset(path):
    data = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(data).hexdigest()}

for folder in range(1, 9):
    for png in sorted((root / "textures" / str(folder)).glob("*")):
        if png.suffix.lower() != ".png" or png.is_symlink() or not png.is_file():
            continue
        if not 33 <= png.stat().st_size <= 262144:
            continue
        with png.open("rb") as image:
            header = image.read(33)
        if header[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR":
            continue
        if not all(1 <= dimension <= 256 for dimension in struct.unpack(">II", header[16:24])):
            continue
        entry = {"png": asset(png)}
        model = png.with_suffix(".json")
        if model.is_file() and not model.is_symlink() and 0 < model.stat().st_size <= 16384:
            entry["model"] = asset(model)
        assets.append(entry)

target = root / "catalog.json"
if target.exists():
    previous = json.loads(target.read_text(encoding="utf-8"))
    if previous.get("version") == 1 and previous.get("assets") == assets:
        raise SystemExit(0)
catalog = {"version": 1, "revision": revision, "assets": assets}
target.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
