import struct
import wave
from pathlib import Path
import pytest
from mix2vst.providers import Cue, PointAndPlayAdapter, ModelNotConfigured


def wav(p):
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(struct.pack("<100h", *([0]*100)))


def setup(tmp_path, runner):
    repo = tmp_path / "official" / "point_and_play"
    repo.mkdir(parents=True)
    (repo / "generate.py").write_text("# official module fixture\n")
    e = tmp_path / "encoder.pt"
    d = tmp_path / "decoder.pt"
    e.write_bytes(b"test")
    d.write_bytes(b"test")
    mix = tmp_path / "mix.wav"
    wav(mix)
    adapter = PointAndPlayAdapter(repo_dir=repo.parent, encoder=e, decoder=d, runner=runner)
    return adapter, Cue(mix, "guitar", 30, 34)


def test_upstream_cli_integration_without_gpu(tmp_path):
    calls = []
    def runner(cmd, *, cwd, check, timeout, capture_output, text):
        calls.append(cmd)
        assert cmd[1:3] == ["-m", "point_and_play.generate"]
        assert "--text" in cmd and cmd[-1] == "guitar"
        assert "--save-report" in cmd
        pitches = []
        ix = cmd.index("--pitches") + 1
        while ix < len(cmd) and not cmd[ix].startswith("--"):
            pitches.append(int(cmd[ix])); ix += 1
        assert pitches == [60, 64]
        velocity = int(cmd[cmd.index("--velocity") + 1])
        out = Path(cmd[cmd.index("--out-dir") + 1])
        for pitch in pitches:
            wav(out / f"pitch{pitch:03d}_vel{velocity:03d}.wav")
    adapter, cue = setup(tmp_path, runner)
    result = adapter.generate(cue, [60, 64], [75, 112], tmp_path / "output")
    assert len(result) == 4
    assert all(x.is_file() for x in result)
    assert len(calls) == 2  # One upstream load per velocity, not per note


def test_reject_bad_cue_window(tmp_path):
    adapter, cue = setup(tmp_path, lambda *a, **k: None)
    with pytest.raises(ValueError, match="4-second"):
        adapter.generate(Cue(cue.mixture, "guitar", 1, 3), [60], [90], tmp_path / "out")


def test_refuse_overwrite(tmp_path):
    adapter, cue = setup(tmp_path, lambda *a, **k: None)
    out = tmp_path / "out"; out.mkdir(); (out / "keep.txt").write_text("keep")
    with pytest.raises(FileExistsError):
        adapter.generate(cue, [60], [90], out)
    assert (out / "keep.txt").read_text() == "keep"


def test_no_fabricated_output(tmp_path):
    adapter, cue = setup(tmp_path, lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="upstream WAV outputs mismatch"):
        adapter.generate(cue, [60], [90], tmp_path / "out")


def test_no_model_configured(tmp_path):
    mix = tmp_path / "mix.wav"; wav(mix)
    with pytest.raises(ModelNotConfigured):
        PointAndPlayAdapter().generate(Cue(mix, "piano", 0, 4), [60], [100], tmp_path / "out")


def test_reject_extra_upstream_files(tmp_path):
    def runner(cmd, *, cwd, check, timeout, capture_output, text):
        out = Path(cmd[cmd.index("--out-dir")+1]); wav(out / "unidentified.wav")
    adapter, cue = setup(tmp_path, runner)
    with pytest.raises(RuntimeError, match="upstream WAV outputs mismatch"):
        adapter.generate(cue, [60], [90], tmp_path / "out")
