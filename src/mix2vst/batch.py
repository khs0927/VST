"""Plan multiple cue-conditioned instruments from ONE mixture without stem separation."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from .core import Note, create_sfz
from .exports import audit_instrument, export_decent
from .providers import Cue, PointAndPlayAdapter


_SAFE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,62}$")


@dataclass(frozen=True)
class InstrumentJob:
    name: str
    label: str
    offset: float
    pitches: tuple[int, ...]
    velocities: tuple[int, ...]
    cue_audio: Path | None = None

    def validate(self):
        if not _SAFE.fullmatch(self.name):
            raise ValueError("unsafe instrument name")
        if not self.label.strip():
            raise ValueError("target instrument label required")
        if self.offset < 0:
            raise ValueError("offset must be >= 0")
        if not self.pitches or len(set(self.pitches)) != len(self.pitches):
            raise ValueError("pitches must be unique and nonempty")
        if not self.velocities or len(set(self.velocities)) != len(self.velocities):
            raise ValueError("velocities must be unique and nonempty")
        if any(type(p) is not int or p not in range(0, 128) for p in self.pitches):
            raise ValueError("pitch out of range")
        if any(type(v) is not int or v not in range(1, 128) for v in self.velocities):
            raise ValueError("velocity out of range")


@dataclass(frozen=True)
class BatchPlan:
    mixture: Path
    rights_confirmed: bool
    jobs: tuple[InstrumentJob, ...]

    @staticmethod
    def from_json(path: Path) -> "BatchPlan":
        path = Path(path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("batch JSON must be object")
        allowed = {"mixture", "rights_confirmed", "instruments"}
        if set(raw) - allowed:
            raise ValueError("unknown batch fields")
        mixture = Path(raw["mixture"]).expanduser()
        if not mixture.is_absolute():
            mixture = path.parent / mixture
        if not mixture.is_file():
            raise FileNotFoundError(mixture)
        if not isinstance(raw.get("instruments"), list) or not raw["instruments"]:
            raise ValueError("provide at least one instrument cue")
        if len(raw["instruments"]) > 24:
            raise ValueError("too many cues; limit 24")
        jobs = []
        for entry in raw["instruments"]:
            if not isinstance(entry, dict):
                raise ValueError("instrument entries must be objects")
            if set(entry) - {"name", "label", "offset", "pitches", "velocities", "cue_audio"}:
                raise ValueError("unknown instrument field")
            cue_audio = entry.get("cue_audio")
            if cue_audio:
                cue_audio = Path(cue_audio).expanduser()
                if not cue_audio.is_absolute():
                    cue_audio = path.parent / cue_audio
                if not cue_audio.is_file():
                    raise FileNotFoundError(cue_audio)
            job = InstrumentJob(name=entry["name"], label=entry["label"],
                                offset=entry["offset"], pitches=tuple(entry["pitches"]),
                                velocities=tuple(entry["velocities"]), cue_audio=cue_audio)
            job.validate()
            jobs.append(job)
        if len({j.name for j in jobs}) != len(jobs):
            raise ValueError("instrument names must be unique")
        rights = raw.get("rights_confirmed", False)
        if type(rights) is not bool:
            raise ValueError("rights_confirmed must be boolean")
        return BatchPlan(mixture.resolve(), rights, tuple(jobs))

    def describe(self):
        return {
            "mode": "stemless", "source": str(self.mixture),
            "rights_confirmed": self.rights_confirmed,
            "instruments": [
                {"name": j.name, "label": j.label, "cue_window": [j.offset, j.offset + 4],
                 "notes": len(j.pitches) * len(j.velocities), "velocities": list(j.velocities)}
                for j in self.jobs],
            "caveat": "explicit cues, not automatic source identification; no quality guarantee",
        }

    def execute(self, adapter: PointAndPlayAdapter, dest: Path, *, model_consent: bool):
        if not self.rights_confirmed or not model_consent:
            raise PermissionError("rights_confirmed=true and explicit --execute flag required")
        dest = Path(dest).resolve()
        if dest.exists() and any(dest.iterdir()):
            raise FileExistsError("refusing to overwrite batch output")
        dest.mkdir(parents=True, exist_ok=True)
        result = []
        for job in self.jobs:
            folder = dest / job.name
            adapter.generate(Cue(self.mixture, job.label, job.offset,
                                 job.offset + 4, job.cue_audio),
                             list(job.pitches), list(job.velocities),
                             folder / "_generated")
            notes = [Note(p, v, f"n{p:03d}_v{v:03d}.wav")
                     for p in job.pitches for v in job.velocities]
            sample_folder = folder / "instrument"
            create_sfz(folder / "_generated", sample_folder, notes, name=job.name)
            export_decent(sample_folder)
            # Generated upstream CLAP scores are estimates, not independent fidelity proof.
            result.append({"name": job.name, "instrument_dir": str(sample_folder),
                           "audit": audit_instrument(sample_folder, require_audio=False)})
        return result
