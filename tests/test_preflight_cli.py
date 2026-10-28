import json
from pathlib import Path
import pytest
from mix2vst.cli import main
from mix2vst.preflight import probe, validate_plugin


def test_preflight_has_honest_defaults():
    report = probe()
    assert report["vst3_compiled"] is False
    assert report["real_mixture_audio_tested"] is False


def test_validate_vst3_needs_binary(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_plugin(tmp_path / "never-built.vst3")


def test_validate_pluginval_contract(tmp_path):
    plugin = tmp_path / "demo.vst3"
    plugin.mkdir()
    class Done:
        returncode = 0
    seen = []
    def runner(cmd, **kw):
        seen.append(cmd)
        return Done()
    out = validate_plugin(plugin, executable="/mock/pluginval", runner=runner)
    assert out["status"] == "passed"
    assert "--skip-gui-tests" in seen[0]


def test_cli_preflight(capsys):
    main(["preflight"])
    value = json.loads(capsys.readouterr().out)
    assert "cuda" in value


def test_cli_run_batch_refuses_unconfirmed(tmp_path):
    with pytest.raises(PermissionError, match="--execute"):
        main(["run-batch", "--spec", str(tmp_path / "test.json"),
              "--out", str(tmp_path / "out"), "--repo-dir", str(tmp_path),
              "--encoder", str(tmp_path / "encoder.pt"),
              "--decoder", str(tmp_path / "decoder.pt")])
