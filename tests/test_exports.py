import hashlib
import json
import struct
import wave
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

from mix2vst.core import Note, create_sfz
from mix2vst.exports import audit_instrument, export_decent
from mix2vst.renderer import make_test_midi, render_sfizz


def wav(p):
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(struct.pack("<200h", *([1000] * 200)))


def library(tmp_path):
    samples = tmp_path / "source"
    samples.mkdir()
    wav(samples / "c.wav")
    wav(samples / "g.wav")
    out = tmp_path / "out"
    create_sfz(samples, out, [Note(60, 40, "c.wav"), Note(67, 100, "g.wav")], name="demo")
    return out


def test_audit_and_export_decent(tmp_path):
    out = library(tmp_path)
    a = audit_instrument(out)
    assert a["sha256_valid"] and a["samples"] == 2
    preset = export_decent(out)
    root = ET.parse(preset).getroot()
    assert root.tag == "DecentSampler"
    regions = root.findall("./groups/group/sample")
    assert len(regions) == 2
    assert regions[0].attrib["path"].startswith("Samples/")
    assert (out / regions[0].attrib["path"]).is_file()


def test_detect_corrupted_audio(tmp_path):
    out = library(tmp_path)
    (out / "Samples/c.wav").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="SHA256"):
        audit_instrument(out)


def test_detect_manifest_injection(tmp_path):
    out = library(tmp_path)
    path = out / "manifest.json"
    info = json.loads(path.read_text())
    info["notes"][0]["wav"] = "../outside.wav"
    path.write_text(json.dumps(info))
    with pytest.raises(ValueError, match="basename"):
        audit_instrument(out)


def test_valid_midi_file(tmp_path):
    p = make_test_midi(tmp_path / "probe.mid", pitch=60)
    assert p.read_bytes()[:4] == b"MThd"
    assert p.read_bytes()[14:18] == b"MTrk"


def test_renderer_fail_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("mix2vst.renderer.shutil.which", lambda executable: None)
    out = library(tmp_path)
    m = make_test_midi(tmp_path / "x.mid")
    with pytest.raises(RuntimeError, match="not installed"):
        render_sfizz(out / "demo.sfz", m, tmp_path / "p.wav")


def test_renderer_contract_mock(tmp_path):
    out = library(tmp_path)
    m = make_test_midi(tmp_path / "x.mid")
    def mock_runner(command, **kwargs):
        assert command[1:3] == ["--sfz", str((out / "demo.sfz").resolve())]
        target = Path(command[command.index("--wav") + 1])
        wav(target)
    info = render_sfizz(out / "demo.sfz", m, tmp_path / "p.wav",
                         executable="/fake/sfizz_render", runner=mock_runner)
    assert info["frames"] == 200
