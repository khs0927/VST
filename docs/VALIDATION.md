# Validation gates

| Gate | Evidence | Status |
|---|---|---|
| G0 | GitHub commit SHA, branch, changed files | GitHub |
| G1 | Remote CPU pytest test log | Automated |
| G2 | SHA256 audit, proper SFZ and Decent XML | Automated with synthetic test WAV |
| G3 | Real CUDA inference log, model checkpoint hashes, generated WAV | **Not tested** |
| G4 | Blind A/B versus authorized isolated ground truth, cue attribution | **Not tested** |
| G5 | Real upstream sfizz C++ 1.2.3 build + synthetic SFZ/MIDI → WAV (38912 frames, 48 kHz, stereo) | **PASS** [run 40697828381](https://github.com/khs0927/VST/actions/runs/40697828381) |
| G6a | Generic upstream sfizz-ui Linux VST3 compiled (`sfizz.vst3/Contents/x86_64-linux/sfizz.so`) | **PASS** [compile log](https://github.com/khs0927/VST/actions/runs/40698440624), pluginval separately unresolved |
| G6b | HISE produces a *distinct per-instrument* VST3 with unique ID/branding | **Not built** |
| G7 | pluginval strictness 5+ and real DAW MIDI playback | **Not tested** |
| G8 | Authenticated permanent remote MCP registration | **Not deployed** |

The synthetic WAV and mocked upstream provider establish integration only. They are not evidence of neural timbre cloning or instrument identification. Do not upload songs, weights or secrets to GitHub Actions.
