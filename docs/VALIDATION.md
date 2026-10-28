# Validation gates

| Gate | Evidence | Status |
|---|---|---|
| G0 | GitHub commit SHA, branch, changed files | GitHub |
| G1 | Remote CPU pytest test log | Automated |
| G2 | SHA256 audit, proper SFZ and Decent XML | Automated with synthetic test WAV |
| G3 | Real CUDA inference log, model checkpoint hashes, generated WAV | **Not tested** |
| G4 | Blind A/B versus authorized isolated ground truth, cue attribution | **Not tested** |
| G5 | Installed sfizz executable produces playable non-silent WAV | **Not tested** |
| G6 | HISE produces self-contained native VST3 | **Not built** |
| G7 | pluginval strictness 5+ and real DAW MIDI playback | **Not tested** |
| G8 | Authenticated permanent remote MCP registration | **Not deployed** |

The synthetic WAV and mocked upstream provider establish integration only. They are not evidence of neural timbre cloning or instrument identification. Do not upload songs, weights or secrets to GitHub Actions.
