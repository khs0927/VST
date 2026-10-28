# Open-source components — integration status

| Component | Source | Current integration / reality |
|---|---|---|
| Point-and-Play | https://github.com/User-tian/Point-and-Play | Official CLI subprocess, CUDA model not actually run |
| sfizz and sfizz_render | https://github.com/sfztools/sfizz | External renderer invocation, mock tested, binary not present on CI |
| Decent Sampler | https://decentsampler-developers-guide.readthedocs.io/en/latest/the-groups-element.html | Generates official XML preset/sample zones, playback not tested |
| pluginval | https://github.com/Tracktion/pluginval | Validation CLI adapter, no compiled native plugin provided |
| HISE | https://github.com/christophhart/HISE | Independent VST3 requires complete project and working toolchain; not built |
| FastMCP | https://github.com/jlowin/fastmcp | Optional local read-only stdio MCP, not deployed |
| LiveSynth | https://github.com/KyungsuKim42/livesynth | Research comparison only, no integration claimed |
| MuScriptor | https://github.com/muscriptor/muscriptor | Optional; model weights CC BY-NC 4.0, not integrated |

## Legal & technical caveats

- Stemless means the original **mixture** goes to Point-and-Play. It needs an **explicit instrument cue**, not automatic instrument enumeration.
- Model notes are generated estimates of timbre, not lossless extraction of an individual source recording. Two similar overlapping instruments may be indistinguishable.
- Upstream code license (Point-and-Play MIT) differs from checkpoint assets/CLAP/DiffRhythm and copyrighted reference music. Commercial use requires checking *all* rights.
- SFZ / Decent presets require an existing sampler. A self-contained independent VST3 is a separate, unverified milestone.
