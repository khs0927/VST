import json
import os
import struct
import wave
import pytest
from mix2vst.batch import BatchPlan
from mix2vst.mcp_bridge import _approved_path


def wav(p):
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
        w.writeframes(struct.pack("<200h", *([0] * 200)))


def make_plan(tmp_path, rights=False):
    wav(tmp_path / "mix.wav")
    data = {"mixture": "mix.wav", "rights_confirmed": rights,
            "instruments": [
                {"name": "piano", "label": "keyboard", "offset": 1.5,
                 "pitches": [48, 60], "velocities": [60, 105]},
                {"name": "guitar", "label": "guitar", "offset": 9,
                 "pitches": [40, 55], "velocities": [80]}]}
    f = tmp_path / "jobs.json"
    f.write_text(json.dumps(data))
    return f, data


def test_batch_plan_without_gpu(tmp_path):
    f, _ = make_plan(tmp_path)
    plan = BatchPlan.from_json(f)
    p = plan.describe()
    assert p["mode"] == "stemless"
    assert [item["notes"] for item in p["instruments"]] == [4, 2]


def test_cannot_execute_unlicensed(tmp_path):
    f, _ = make_plan(tmp_path)
    plan = BatchPlan.from_json(f)
    with pytest.raises(PermissionError, match="rights_confirmed"):
        plan.execute(None, tmp_path / "output", model_consent=True)


def test_requires_explicit_execute(tmp_path):
    f, _ = make_plan(tmp_path, True)
    with pytest.raises(PermissionError, match="explicit"):
        BatchPlan.from_json(f).execute(None, tmp_path / "output", model_consent=False)


def test_duplicate_names_rejected(tmp_path):
    f, data = make_plan(tmp_path)
    data["instruments"].append(dict(data["instruments"][0]))
    f.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="unique"):
        BatchPlan.from_json(f)


def test_mcp_workspace_boundary(tmp_path, monkeypatch):
    sub = tmp_path / "safe"
    sub.mkdir()
    (sub / "test.json").write_text("{}")
    monkeypatch.setenv("MIX2VST_WORKSPACE", str(sub))
    assert _approved_path("test.json") == (sub / "test.json")
    with pytest.raises(PermissionError, match="outside"):
        _approved_path("../safe2.json")


def test_mcp_refuses_unconfigured_workspace(tmp_path, monkeypatch):
    monkeypatch.delenv("MIX2VST_WORKSPACE", raising=False)
    with pytest.raises(PermissionError):
        _approved_path("test.json")
