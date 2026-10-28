"""Evidence-oriented environment readiness; never claims absent tools are ready."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import shutil
import subprocess


def probe() -> dict:
    result = {
        "sfizz_render": bool(shutil.which("sfizz_render") or shutil.which("sfizz-render")),
        "pluginval": bool(shutil.which("pluginval")),
        "hise": bool(shutil.which("HISE") or shutil.which("hise")),
        "fastmcp": importlib.util.find_spec("fastmcp") is not None,
        "torch": importlib.util.find_spec("torch") is not None,
        "cuda": False,
        "vst3_compiled": False,
        "real_mixture_audio_tested": False,
    }
    if result["torch"]:
        try:
            import torch
            result["cuda"] = bool(torch.cuda.is_available())
        except Exception as exc:
            result["torch_probe_error"] = type(exc).__name__
    return result


def validate_plugin(vst3: Path, *, executable: str = "pluginval",
                    runner=subprocess.run, timeout: int = 300) -> dict:
    plugin = Path(vst3).resolve()
    if not plugin.exists() or not plugin.name.endswith(".vst3"):
        raise FileNotFoundError("provide an existing .vst3 plugin")
    tool = shutil.which(executable) if executable == "pluginval" else executable
    if not tool:
        raise RuntimeError("pluginval is unavailable; install Tracktion/pluginval first")
    cmd = [tool, "--strictness-level", "5", "--skip-gui-tests", str(plugin)]
    done = runner(cmd, check=True, timeout=timeout, capture_output=True, text=True)
    return {"status": "passed", "plugin": str(plugin),
            "validator": "Tracktion/pluginval", "exit_code": done.returncode}
