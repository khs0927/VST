# Open-source composition, not reimplementation

This repository contains only a thin integration layer. Upstream algorithms are **not reimplemented**; do not copy third-party weights or trained audio into Git. Every optional upstream is installed separately and must be license-reviewed.

| Source | Repository | Responsibility | Status |
|---|---|---|---|
| Point-and-Play | https://github.com/User-tian/Point-and-Play | **Primary**. Mixed audio + instrument cue + note/velocity -> WAV samples | `run-point-play` adapter, GPU not exercised |
| LiveSynth | https://github.com/KyungsuKim42/livesynth | Experimental real-time MIDI instrument, useful for comparisons | Planned; no false adapter |
| HISE | https://github.com/christophhart/HISE | Compile standalone VST3 from prepared multisamples | Planned; GPLv3/commercial licensing |
| Decent Sampler | https://www.decentsamples.com/product/decent-sampler-plugin/ | Free host for `.dspreset` multisample libraries | Optional, not bundled |
| sfizioso | https://github.com/rullopat/sfizioso | SFZ C++ player library (BSD-2); early-stage fork | Candidate; not bundled |
| SFZ-to-HISE converter | https://github.com/anderseklov/SFZ-to-HISE-converter | Bridge SFZ maps to HISE samplemaps | Candidate; check extra license clauses |
| pluginval | https://github.com/Tracktion/pluginval | Validate built VST3 at CI / on supported host | Planned |
| DawDreamer | https://github.com/DBraun/DawDreamer | Offline MIDI-to-audio render / automated tests | Planned; GPLv3 |
| librosa | https://github.com/librosa/librosa | Optional onset/feature analysis | Planned |
| MuScriptor | https://github.com/muscriptor/muscriptor | Optional multi-instrument transcription | Optional model weights CC BY-NC 4.0 |

## Important caveats

- The input to Point-and-Play is a mixture; **no stem separation** is invoked.
- It uses a 4-second reference window and requires a **specified** instrument cue. It does not automatically discover every independently identifiable instrument in a recording.
- This adapter groups pitches **once per velocity**, using the upstream's documented `--pitches` argument and exact `pitchNNN_velNNN.wav` filename contract, avoiding per-note model reloads. Upstream CLI currently uses CUDA and does not perform instrument auto-discovery.
- Any `.sfz` is an **instrument library** for a compatible plugin, **not a standalone `.vst3` binary**.
- Point-and-Play repo MIT does not automatically license pretrained model checkpoints, external CLAP, DiffRhythm, or recordings for unrestricted commercial redistribution.
- Never use noncommercial weights or copyrighted sample sources in commercial outputs without adequate rights.
