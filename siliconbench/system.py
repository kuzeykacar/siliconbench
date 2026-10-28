"""Describe the machine, so results from different Macs can be compared."""
import os, platform, subprocess

def _sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""

def info():
    d = dict(os=platform.platform(), python=platform.python_version(), machine=platform.machine())
    if platform.system() == "Darwin":
        d["chip"] = _sh(["sysctl", "-n", "machdep.cpu.brand_string"])
        mem = _sh(["sysctl", "-n", "hw.memsize"]); d["ram_gb"] = round(int(mem) / 2**30) if mem.isdigit() else None
        d["cores"] = _sh(["sysctl", "-n", "hw.ncpu"])
        d["on_battery"] = "Battery Power" in _sh(["pmset", "-g", "batt"])
    else:
        d["cores"] = os.cpu_count()
    return d
