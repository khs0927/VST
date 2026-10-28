"""CLI: bridge original OSS inference to sample-library packaging."""
import argparse
import json
from pathlib import Path
from .core import Note, create_sfz, parse_notes
from .providers import Cue, PointAndPlayAdapter


def main(argv=None):
    p = argparse.ArgumentParser(prog="mix2vst")
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("package-sfz", help="Package MIDI-pitched WAV files as SFZ")
    c.add_argument("--samples", required=True, type=Path)
    c.add_argument("--notes", required=True, type=Path)
    c.add_argument("--out", required=True, type=Path)
    c.add_argument("--name", default="instrument")

    g = sub.add_parser("run-point-play", help="Opt-in official Point-and-Play inference and SFZ export")
    g.add_argument("--repo-dir", required=True, type=Path, help="Separately checked-out official project")
    g.add_argument("--encoder", required=True, type=Path)
    g.add_argument("--decoder", required=True, type=Path)
    g.add_argument("--python", help="Interpreter in official project's configured CUDA environment")
    g.add_argument("--mixture", required=True, type=Path)
    g.add_argument("--label", required=True, help="One target instrument category (e.g., guitar)")
    g.add_argument("--offset", type=float, required=True, help="Start of 4-second cue window")
    g.add_argument("--audio-cue", type=Path, help="Optional audio cue instead of label")
    g.add_argument("--pitches", type=int, nargs="+", required=True)
    g.add_argument("--velocities", type=int, nargs="+", required=True)
    g.add_argument("--out", type=Path, required=True)
    g.add_argument("--name", default="cloned-instrument")

    a = p.parse_args(argv)
    if a.command == "package-sfz":
        result = create_sfz(a.samples, a.out, parse_notes(a.notes), name=a.name)
        print(json.dumps({"out": str(a.out), "name": result["name"], "regions": len(result["notes"])}))
    elif a.command == "run-point-play":
        cue = Cue(a.mixture, a.label, a.offset, a.offset + 4, a.audio_cue)
        adapter = PointAndPlayAdapter(repo_dir=a.repo_dir, encoder=a.encoder,
                                      decoder=a.decoder, python=a.python)
        sample_dir = a.out / "_generated"
        adapter.generate(cue, a.pitches, a.velocities, sample_dir)
        notes = [Note(p, v, f"n{p:03d}_v{v:03d}.wav")
                 for p in a.pitches for v in a.velocities]
        result = create_sfz(sample_dir, a.out / "instrument", notes, name=a.name)
        print(json.dumps({"out": str(a.out / "instrument"),
                          "name": result["name"], "regions": len(result["notes"]),
                          "source": "Point-and-Play upstream, unverified quality"}))


if __name__ == "__main__":
    main()
