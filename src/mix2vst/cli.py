"""CLI for independent open-source synthesis engines and sample players."""
import argparse
import json
from pathlib import Path

from .batch import BatchPlan
from .core import Note, create_sfz, parse_notes
from .exports import audit_instrument, export_decent
from .preflight import probe, validate_plugin
from .providers import Cue, PointAndPlayAdapter
from .renderer import make_test_midi, render_sfizz


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

    plan = sub.add_parser("plan-batch", help="Validate and describe a multi-instrument no-stems plan (no GPU)")
    plan.add_argument("--spec", type=Path, required=True)
    run = sub.add_parser("run-batch", help="Execute explicit approved multi-instrument plan on CUDA host")
    run.add_argument("--spec", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--repo-dir", type=Path, required=True)
    run.add_argument("--encoder", type=Path, required=True)
    run.add_argument("--decoder", type=Path, required=True)
    run.add_argument("--python")
    run.add_argument("--execute", action="store_true")

    exp = sub.add_parser("export-decent", help="Create an actual .dspreset from an SFZ instrument package")
    exp.add_argument("--library", type=Path, required=True)
    audit = sub.add_parser("audit", help="Verify sample SHA256 and WAV integrity")
    audit.add_argument("--library", type=Path, required=True)
    gen = sub.add_parser("make-midi", help="Generate a tiny MIDI file for external sfizz renderer QA")
    gen.add_argument("--out", type=Path, required=True)
    gen.add_argument("--pitch", type=int, default=60)
    gen.add_argument("--velocity", type=int, default=100)
    render = sub.add_parser("render-sfizz", help="Call installed upstream sfizz_render")
    render.add_argument("--sfz", type=Path, required=True)
    render.add_argument("--midi", type=Path, required=True)
    render.add_argument("--out", type=Path, required=True)
    validator = sub.add_parser("validate-vst3", help="Call installed pluginval on an existing binary")
    validator.add_argument("--plugin", type=Path, required=True)
    sub.add_parser("preflight", help="Show CPU/GPU and optional tools, evidence-only")

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
        export_decent(a.out / "instrument")
        print(json.dumps({"out": str(a.out / "instrument"),
                          "name": result["name"], "regions": len(result["notes"]),
                          "source": "Point-and-Play upstream, audio fidelity not verified"}))
    elif a.command == "plan-batch":
        print(json.dumps(BatchPlan.from_json(a.spec).describe(), indent=2))
    elif a.command == "run-batch":
        if not a.execute:
            raise PermissionError("must explicitly specify --execute")
        pstate = probe()
        if not pstate["cuda"]:
            raise RuntimeError("CUDA is unavailable; model inference is not claimed or attempted")
        adapter = PointAndPlayAdapter(repo_dir=a.repo_dir, encoder=a.encoder,
                                      decoder=a.decoder, python=a.python)
        result = BatchPlan.from_json(a.spec).execute(adapter, a.out, model_consent=a.execute)
        print(json.dumps(result, indent=2))
    elif a.command == "export-decent":
        print(json.dumps({"dspreset": str(export_decent(a.library))}))
    elif a.command == "audit":
        print(json.dumps(audit_instrument(a.library, require_audio=False), indent=2))
    elif a.command == "make-midi":
        print(json.dumps({"midi": str(make_test_midi(a.out, pitch=a.pitch, velocity=a.velocity))}))
    elif a.command == "render-sfizz":
        print(json.dumps(render_sfizz(a.sfz, a.midi, a.out), indent=2))
    elif a.command == "validate-vst3":
        print(json.dumps(validate_plugin(a.plugin), indent=2))
    elif a.command == "preflight":
        print(json.dumps(probe(), indent=2))


if __name__ == "__main__":
    main()
