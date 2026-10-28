# Mixture Instrument Factory (stemless-first, open-source fusion)

Research-led, **honestly staged** framework for taking a selected instrument timbre *directly from a full music mixture* and turning synthesized notes into a playable sample instrument. **No stem separation** is used.

> Status: CPU-only orchestration layer tested. Actual Point-and-Play CUDA inference, timbre fidelity, VST3 build and audio playback not yet verified.

## Reuse upstream, write only glue

- **Point-and-Play** (MIT code; https://github.com/User-tian/Point-and-Play) — real upstream Python CLI for mixture + 4-second cue + MIDI note and velocity to WAV. This repo now contains a functioning subprocess **adapter**, not a fake model or rewrite of its synthesizer.
- **SFZ** — minimal 125-line deterministic exporter to stitch generated WAVs into an instrument library, with pitch and velocity zoning and SHA-256. This lightweight glue is intentionally used instead of embedding another large GPL application; it is not a synthesis engine.
- **HISE, LiveSynth, sfizioso, pluginval, DawDreamer, other tools** — integration points, not installed or falsely claimed working. See [UPSTREAMS.md](UPSTREAMS.md).

## Offline CPU core

```sh
python -m pip install -e '.[test]'
python -m pytest -q
mix2vst package-sfz --samples ./my-notes --notes ./notes.json --out ./local-output --name violin
```

Example notes file:

```json
[
  {"midi":60,"velocity":64,"wav":"C4.wav","confidence":0.92},
  {"midi":67,"velocity":96,"wav":"G4.wav","confidence":0.91}
]
```

## Optional real upstream inference

In a CUDA-capable **separate** Python environment, explicitly install the official Point-and-Play project according to its README, and obtain checkpoints after checking licenses. Never commit audio/checkpoints. Use:

```sh
mix2vst run-point-play \
  --repo-dir /path/to/Point-and-Play \
  --encoder /path/to/checkpoints/encoder.pt \
  --decoder /path/to/checkpoints/matched_decoder.pt \
  --python /path/to/pointplay-venv/bin/python \
  --mixture /path/to/recording.wav \
  --label guitar --offset 30 \
  --pitches 48 55 60 67 \
  --velocities 64 100 \
  --out /private/output --name cloned-guitar
```

The script calls the official `python -m point_and_play.generate` once **per velocity**, batching requested pitches, checks the exact expected filenames from upstream's public CLI, and creates `instrument/cloned-guitar.sfz`, `instrument/Samples/` and an auditable manifest. A failed/ambiguous upstream output aborts rather than assigning a possibly wrong note.

**Known limitation:** Selected 4-second window must contain a sufficiently identifiable target instrument. Same-category overlap may make cloning unreliable. Model quality is unmeasured; do not call samples source-exact. Only use audio with rights. Test on legally cleared stems as *ground truth for comparison*, not as a processing dependency.

## Validation and CI

`pytest` tests pure orchestration and a mocked upstream CLI, not neural model sound fidelity. GitHub Actions `ci.yml` deliberately avoids installing model weights or consuming GPU. Full independent VST3 and audio render validation are future stages and must not be reported as passed.

No paid services, CI dispatch, workflow deployment or production publishing is triggered by this source archive.

## Remaining roadmap

- [x] Real upstream CLI adapter + fail-closed, per-velocity batch contract tests
- [x] Simple WAV note → `.sfz` sample-map exporter with SHA-256 and tests
- [ ] Evaluate multiple cue windows and compare timbre consistency / same-category confusion
- [ ] Record and verify licensed checkpoint hashes, pinned upstream commit, source provenance
- [ ] **Run CUDA inference** for a permitted, real mixed song
- [ ] Compare audio against legally cleared multitrack ground truth (evaluation only)
- [ ] Use upstream converter / HISE to compile an actual `.vst3`
- [ ] pluginval and DawDreamer full end-to-end render/compatibility check
- [ ] MCP FastMCP endpoint with approved storage and explicit execution policy
