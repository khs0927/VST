# VST — Mixture Instrument Factory v0.2.0

A **stemless-first, open-source fusion** pipeline. Provide a mixed music file and explicit target-instrument cue windows. Use the original Point-and-Play code to synthesize a pitch/velocity grid, then export playable SFZ and free Decent Sampler presets. No pretrained weights or music recordings are redistributed.

**Verified scope:** CPU tests on mock audio/model output. **NOT proven:** actual CUDA inference, target-source similarity, standalone per-instrument VST3 build, real DAW playback.

## Install and test the free CPU foundation

```bash
python -m pip install -e '.[test]'
python -m pytest -q
mix2vst preflight
```

## Create and audit a playable instrument library

```bash
mix2vst package-sfz --samples /private/wavs --notes /private/notes.json \
  --out /private/library/guitar --name guitar
mix2vst audit --library /private/library/guitar
mix2vst export-decent --library /private/library/guitar
mix2vst make-midi --out /private/probe.mid --pitch 60
# Requires independently installed sfizz_render:
mix2vst render-sfizz --sfz /private/library/guitar/guitar.sfz \
  --midi /private/probe.mid --out /private/probe.wav
```

`notes.json` example: `[{"midi":60,"velocity":64,"wav":"C4.wav"}]`. A `.dspreset` opens in the free Decent Sampler VST3; it is **not** a separately compiled VST3.

## Plan and run many instruments without stem separation

Create a JSON manifest based on `examples/batch.example.json`, specifying one named instrument, an explicit category and a 4-second time offset per target.

```bash
mix2vst plan-batch --spec /private/jobs.json
```

On an **independently configured CUDA** machine after installing the official [Point-and-Play](https://github.com/User-tian/Point-and-Play) project, checkpoint assets, licensing review and supplying your authorized source mix:

```bash
mix2vst run-batch --spec /private/jobs.json \
  --repo-dir /path/to/Point-and-Play \
  --encoder /path/to/encoder.pt --decoder /path/to/matched_decoder.pt \
  --python /path/to/venv/bin/python \
  --out /private/output --execute
```

Must explicitly set `rights_confirmed: true` in JSON and pass `--execute`, and a local CUDA device must be available. This code calls **official upstream model**; it does not reimplement neural synthesis. It produces SFZ + Decent presets for each target.

## MCP tools (read-only by design)

```bash
python -m pip install -e '.[mcp]'
export MIX2VST_WORKSPACE=/private/approved-workspace
mix2vst-mcp
```

The local stdio MCP exposes only plan and integrity audit tools with filesystem boundaries. It is **not** an installed permanent public ChatGPT plugin. Public server deployment needs separate OAuth security and approval.

## Already compiled VST3 validation

After HISE or another project compiles an actual `MyInstrument.vst3` and you separately install pluginval:

```bash
mix2vst validate-vst3 --plugin /path/to/MyInstrument.vst3
```

Compilation of a separate plugin **cannot** be claimed from only an SFZ preset. Requires HISE project, compiler, samples, license review and host OS. Project metadata and tests: [UPSTREAMS.md](UPSTREAMS.md), [Validation gates](docs/VALIDATION.md).

**Policy:** free CPU GitHub Actions only; no deployment, charge, source recordings, pretrained weights or automatic main merge.
