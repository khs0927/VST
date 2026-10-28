"""Thin adapters for independently installed open-source projects.

The official Point-and-Play source, checkpoints and dependencies are NOT
vendored, copied or installed by this package. Inference is explicitly opt-in.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Callable, Protocol


@dataclass(frozen=True)
class Cue:
    mixture: Path
    label: str
    start_seconds: float
    end_seconds: float
    audio_cue: Path | None = None

    def validate(self):
        if not self.mixture.is_file():
            raise FileNotFoundError(self.mixture)
        if not self.label.strip():
            raise ValueError("explicit target instrument label required")
        if not (0 <= self.start_seconds < self.end_seconds):
            raise ValueError("invalid cue time window")
        if self.audio_cue is not None and not self.audio_cue.is_file():
            raise FileNotFoundError(self.audio_cue)


class SynthProvider(Protocol):
    def generate(self, cue: Cue, pitches: list[int], velocities: list[int], out_dir: Path) -> list[Path]: ...


class ModelNotConfigured(RuntimeError):
    pass


class PointAndPlayAdapter:
    """Invoke upstream's real `python -m point_and_play.generate` CLI.

    One call per velocity batches all requested pitches, avoiding repeated
    model loads. Upstream WAV naming is checked against its public CLI source.
    `runner` is injectable for CPU-only argument contract tests.
    """

    def __init__(self, *, repo_dir: Path | None = None, encoder: Path | None = None,
                 decoder: Path | None = None, python: str | None = None,
                 runner: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.repo_dir = repo_dir
        self.encoder = encoder
        self.decoder = decoder
        self.python = python or sys.executable
        self.runner = runner

    def _validate_setup(self):
        if self.repo_dir is None or self.encoder is None or self.decoder is None:
            raise ModelNotConfigured("provide explicit upstream Point-and-Play repo, encoder and decoder paths")
        for f in [self.encoder, self.decoder]:
            if not Path(f).is_file():
                raise ModelNotConfigured(f"checkpoint not found: {f}")
        if not (Path(self.repo_dir) / "point_and_play" / "generate.py").is_file():
            raise ModelNotConfigured("official Point-and-Play module missing from upstream repo directory")

    def generate(self, cue: Cue, pitches: list[int], velocities: list[int], out_dir: Path) -> list[Path]:
        cue.validate()
        self._validate_setup()
        if not pitches or not velocities:
            raise ValueError("at least one pitch and velocity required")
        if any(type(p) is not int or not 0 <= p <= 127 for p in pitches):
            raise ValueError("MIDI pitch out of range")
        if any(type(v) is not int or not 1 <= v <= 127 for v in velocities):
            raise ValueError("MIDI velocity out of range")
        if len(set(pitches)) != len(pitches) or len(set(velocities)) != len(velocities):
            raise ValueError("duplicate pitches or velocities")
        if abs((cue.end_seconds - cue.start_seconds) - 4.0) > 1e-6:
            raise ValueError("Point-and-Play upstream inference uses a 4-second mixture window")
        # Do not overwrite stale outputs, even when an upstream invocation fails.
        out_dir = out_dir.resolve()
        if out_dir.exists() and any(out_dir.iterdir()):
            raise FileExistsError("refusing to overwrite non-empty output directory")
        out_dir.mkdir(parents=True, exist_ok=True)
        result = []
        for v in velocities:
            velocity_dir = out_dir / f"velocity_{v:03d}"
            velocity_dir.mkdir()
            cmd = [self.python, "-m", "point_and_play.generate",
                   "--encoder", str(Path(self.encoder).resolve()),
                   "--decoder", str(Path(self.decoder).resolve()),
                   "--mixture", str(cue.mixture.resolve()),
                   "--offset", str(cue.start_seconds),
                   "--pitches", *(str(p) for p in pitches),
                   "--velocity", str(v),
                   "--out-dir", str(velocity_dir), "--save-report"]
            if cue.audio_cue is not None:
                cmd.extend(["--cue-audio", str(cue.audio_cue.resolve())])
            else:
                cmd.extend(["--text", cue.label])
            self.runner(cmd, cwd=str(Path(self.repo_dir).resolve()), check=True,
                        timeout=3600, capture_output=True, text=True)
            expected = {f"pitch{p:03d}_vel{v:03d}.wav" for p in pitches}
            actual = {p.name for p in velocity_dir.glob("*.wav")}
            if actual != expected:
                raise RuntimeError(f"upstream WAV outputs mismatch for velocity {v}: expected={sorted(expected)} got={sorted(actual)}")
            for p in pitches:
                dest = out_dir / f"n{p:03d}_v{v:03d}.wav"
                shutil.move(str(velocity_dir / f"pitch{p:03d}_vel{v:03d}.wav"), str(dest))
                result.append(dest)
        return result
