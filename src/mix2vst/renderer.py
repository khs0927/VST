"""Delegate SFZ audio rendering to the upstream sfizz-render executable."""
from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import struct
import wave


def make_test_midi(path: Path, *, pitch: int = 60, velocity: int = 100) -> Path:
    """Tiny single-note standard MIDI file; avoids bundling a sequencing engine."""
    if not (0 <= pitch <= 127 and 1 <= velocity <= 127):
        raise ValueError("MIDI note values out of range")
    # Type 0; ticks-per-quarter 480, note-off after 480 ticks.
    events = bytes([0, 0x90, pitch, velocity, 0x83, 0x60, 0x80, pitch, 0, 0, 0xFF, 0x2F, 0])
    data = b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) + b"MTrk" + struct.pack(">I", len(events)) + events
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def render_sfizz(sfz: Path, midi: Path, target: Path, *,
                 executable: str = "sfizz_render", timeout: int = 120,
                 runner=subprocess.run) -> dict:
    """Render through third-party sfizz, not custom Python audio synthesis."""
    sfz, midi, target = Path(sfz), Path(midi), Path(target)
    if not sfz.is_file() or not midi.is_file():
        raise FileNotFoundError("SFZ and MIDI must already exist")
    command = shutil.which(executable) if executable == "sfizz_render" else executable
    if not command:
        raise RuntimeError("sfizz_render is not installed; install upstream sfizz separately")
    if target.exists():
        raise FileExistsError("will not replace an existing output WAV")
    target.parent.mkdir(parents=True, exist_ok=True)
    runner([command, "--sfz", str(sfz.resolve()), "--midi", str(midi.resolve()),
            "--wav", str(target.resolve())], check=True, timeout=timeout,
           capture_output=True, text=True)
    if not target.is_file():
        raise RuntimeError("sfizz renderer returned without producing WAV")
    with wave.open(str(target), "rb") as w:
        frames, rate = w.getnframes(), w.getframerate()
        if frames <= 0 or rate < 8000:
            raise ValueError("sfizz rendered an invalid WAV")
        return {"path": str(target), "frames": frames, "sample_rate": rate}
