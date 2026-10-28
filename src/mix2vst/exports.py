"""Interop with existing samplers: Decent Sampler XML and SFZ audit.

This is file-format glue, not a sampler, synthesizer or VST implementation.
"""
from __future__ import annotations
from pathlib import Path
from xml.etree import ElementTree as ET
import hashlib
import json
import re
import wave

_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def audit_instrument(folder: Path, *, require_audio: bool = True) -> dict:
    """Fail closed if a package is missing, altered or has malformed WAV data."""
    folder = Path(folder).resolve()
    manifest_file = folder / "manifest.json"
    info = json.loads(manifest_file.read_text(encoding="utf-8"))
    if info.get("format") != "sfz" or not _NAME.fullmatch(info.get("name", "")):
        raise ValueError("unexpected manifest format or name")
    sfz_file = folder / (info["name"] + ".sfz")
    if not sfz_file.is_file():
        raise FileNotFoundError(sfz_file)
    regions = info.get("notes")
    if not isinstance(regions, list) or not regions:
        raise ValueError("no sample regions")
    if sfz_file.read_text(encoding="utf-8").count("<region>") != len(regions):
        raise ValueError("SFZ and manifest region count disagree")
    verified = []
    for n in regions:
        name = n.get("wav")
        if not isinstance(name, str) or not _NAME.fullmatch(name) or not name.lower().endswith(".wav"):
            raise ValueError("invalid sample basename")
        path = folder / "Samples" / name
        if not path.is_file() or not path.resolve().is_relative_to(folder):
            raise FileNotFoundError(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != n.get("sha256"):
            raise ValueError("sample SHA256 mismatch: " + name)
        with wave.open(str(path), "rb") as f:
            if f.getnframes() <= 0 or f.getnchannels() not in (1, 2):
                raise ValueError("invalid wave sample: " + name)
            if require_audio and not any(f.readframes(min(4096, f.getnframes()))):
                raise ValueError("silent starting frame window: " + name)
        for k in ("midi", "lokey", "hikey", "lovel", "hivel"):
            if type(n.get(k)) is not int:
                raise ValueError("non-integer zone " + k)
        if not 0 <= n["lokey"] <= n["midi"] <= n["hikey"] <= 127:
            raise ValueError("bad key zone")
        if not 1 <= n["lovel"] <= n["hivel"] <= 127:
            raise ValueError("bad velocity zone")
        verified.append(name)
    return {"status": "passed", "samples": len(verified), "name": info["name"], "sha256_valid": True}


def export_decent(folder: Path) -> Path:
    """Wrap existing regions as playable .dspreset for free Decent Sampler."""
    audit_instrument(folder, require_audio=False)
    folder = Path(folder).resolve()
    info = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    top = ET.Element("DecentSampler", {"minVersion": "1.0.0"})
    groups = ET.SubElement(top, "groups")
    group = ET.SubElement(groups, "group", {"name": info["name"]})
    for n in info["notes"]:
        if n["midi"] == 0:
            raise ValueError("Decent Sampler rootNote must be 1..127")
        ET.SubElement(group, "sample", {
            "path": "Samples/" + n["wav"], "rootNote": str(n["midi"]),
            "loNote": str(n["lokey"]), "hiNote": str(n["hikey"]),
            "loVel": str(n["lovel"]), "hiVel": str(n["hivel"]),
        })
    target = folder / (info["name"] + ".dspreset")
    tree = ET.ElementTree(top)
    ET.indent(tree, space="  ")
    tree.write(target, encoding="utf-8", xml_declaration=True)
    return target
