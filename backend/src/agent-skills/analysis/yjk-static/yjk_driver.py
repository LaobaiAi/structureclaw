# -*- coding: utf-8 -*-
"""YJK analysis driver -- subprocess entry point.

Must run under YJK's bundled Python 3.10.  Do NOT add extra CLI
arguments; YJKAPI uses sys.argv[1] for internal state and will
break if unexpected args are present.

Usage (called by runtime.py via subprocess):
    <YJK_PYTHON> yjk_driver.py <model.json> <work_dir>

Reads the V2 model JSON, converts to .ydb, launches YJK GUI, runs a
full static analysis, collects available .OUT text as fallback result
content, and outputs the final result JSON to stdout.

The sequence below strictly follows the proven three_story_steel_frame.py
pattern from the YJK SDK.
"""
from __future__ import annotations

import json
import os
import sys
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _emit_json(payload: dict) -> None:
    """Write the final result JSON to stdout (the ONLY stdout we produce).

    Flush stderr first so any YJKAPI noise that leaked to stdout is
    already written, then write our JSON on its own line.
    """
    sys.stderr.flush()
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _error(message: str) -> None:
    _emit_json({
        "status": "error",
        "summary": {"engine": "yjk-static"},
        "data": {},
        "detailed": {"error": message},
        "warnings": [message],
    })


def _setup_paths() -> str:
    """Set up sys.path and os.environ["PATH"] for YJK.

    Returns the resolved YJKS_ROOT directory.
    """
    yjks_root = os.environ.get(
        "YJKS_ROOT",
        os.environ.get("YJK_PATH", r"D:\YJKS\YJKS_8_0_0"),
    ).strip().strip('"')

    yjks_exe_env = os.environ.get("YJKS_EXE", "").strip().strip('"')
    if yjks_exe_env and os.path.isfile(yjks_exe_env):
        root = os.path.dirname(os.path.abspath(yjks_exe_env))
    elif os.path.isdir(yjks_root):
        root = yjks_root
    else:
        root = yjks_root

    # DLL search path
    os.environ["PATH"] = root + os.pathsep + os.environ.get("PATH", "")

    # Python import paths: YJKS_ROOT itself (for native wrappers) and
    # the driver's own directory (for yjk_converter).
    for p in (root, SCRIPT_DIR):
        if p and p not in sys.path:
            sys.path.insert(0, p)

    return root


def _find_yjks_exe(root: str) -> str | None:
    for name in ("yjks.exe", "YJKS.exe"):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            return p
    return None


def _run_cmd(cmd: str, arg: str = "") -> bool:
    """Execute a YJK command and return success status.

    Returns True if the command succeeded, False if YJK is no longer running.
    """
    from YJKAPI import YJKSControl
    print(f"[yjk_driver] RunCmd({cmd!r}, {arg!r})", file=sys.stderr, flush=True)
    try:
        YJKSControl.RunCmd(cmd, arg)
        # Check if YJK is still running after the command
        if not _is_yjk_running():
            print(f"[yjk_driver] WARNING: YJK process terminated after {cmd}", file=sys.stderr, flush=True)
            return False
        return True
    except Exception as exc:
        print(f"[yjk_driver] ERROR in RunCmd({cmd}): {exc}", file=sys.stderr, flush=True)
        return False


def _is_yjk_running() -> bool:
    """Check if the YJK process is still running."""
    import subprocess
    try:
        # Use tasklist to check if yjks.exe is running
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq yjks.exe"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return "yjks.exe" in result.stdout.lower()
    except Exception:
        return True  # Assume running if we can't check


def _collect_out_files(work_dir: str) -> str:
    """Read .OUT/.out files under work_dir as fallback result text."""
    lines: list[str] = []
    for dirpath, _dirs, files in os.walk(work_dir):
        for f in sorted(files):
            if f.upper().endswith(".OUT"):
                fp = os.path.join(dirpath, f)
                try:
                    text = open(fp, encoding="gbk", errors="replace").read()
                    lines.append(f"=== {f} ===\n{text[:3000]}")
                except Exception:
                    pass
    return "\n\n".join(lines) if lines else "(no .OUT files found)"


def main() -> int:
    # -- Parse arguments ------------------------------------------------
    if len(sys.argv) < 3:
        _error("Usage: yjk_driver.py <model.json> <work_dir>")
        return 1

    model_path = sys.argv[1]
    work_dir = sys.argv[2]

    # Strip our arguments so YJKAPI sees no stray sys.argv[1]
    sys.argv = [sys.argv[0]]

    yjks_root = _setup_paths()

    try:
        return _run(model_path, work_dir, yjks_root)
    except Exception:
        _error(f"Unhandled exception in yjk_driver:\n{traceback.format_exc()}")
        return 1


def _run(model_path: str, work_dir: str, yjks_root: str) -> int:
    # -- Import YJKAPI (requires sys.path set up by _setup_paths) ------
    # Redirect stdout during import so any YJKAPI banner/init messages
    # go to stderr and don't corrupt our JSON output channel.
    import io
    _real_stdout = sys.stdout
    sys.stdout = io.TextIOWrapper(sys.stderr.buffer, encoding=sys.stderr.encoding or "utf-8")
    try:
        from YJKAPI import ControlConfig, YJKSControl
    finally:
        sys.stdout = _real_stdout

    # -- Read V2 model JSON ---------------------------------------------
    with open(model_path, "r", encoding="utf-8") as f:
        model_data = json.load(f)

    project = model_data.get("project")
    project_name = (
        project.get("name", "sc_model") if isinstance(project, dict) else "sc_model"
    ) or "sc_model"
    ydb_filename = f"{project_name}.ydb"

    # -- Phase 1: Convert V2 -> .ydb ------------------------------------
    print("[yjk_driver] Phase 1: V2 -> YDB conversion", file=sys.stderr, flush=True)
    from yjk_converter import convert_v2_to_ydb

    try:
        ydb_path = convert_v2_to_ydb(model_data, work_dir, ydb_filename)
    except Exception as exc:
        _error(f"V2 -> YDB conversion failed: {exc}")
        return 1
    print(f"[yjk_driver] ydb_path = {ydb_path}", file=sys.stderr, flush=True)

    # -- Phase 2: Launch YJK (control.py test01 pattern) ----------------
    yjks_exe_env = os.environ.get("YJKS_EXE", "").strip().strip('"')
    yjks_exe = (
        yjks_exe_env if yjks_exe_env and os.path.isfile(yjks_exe_env)
        else _find_yjks_exe(yjks_root)
    )
    if not yjks_exe or not os.path.isfile(yjks_exe):
        _error(f"yjks.exe not found (YJKS_ROOT={yjks_root})")
        return 1

    version = os.environ.get("YJK_VERSION", "8.0.0").strip()

    # Default: show the YJK GUI so the user can observe the full workflow.
    # Set YJK_INVISIBLE=1 in .env to run fully headless (CI / unattended).
    cfg = ControlConfig()
    cfg.Version = version
    cfg.Invisible = os.environ.get("YJK_INVISIBLE", "0").strip() == "1"
    YJKSControl.initConfig(cfg)

    print(f"[yjk_driver] Phase 2: RunYJK({yjks_exe})", file=sys.stderr, flush=True)
    msg = YJKSControl.RunYJK(yjks_exe)
    print(f"[yjk_driver] RunYJK returned: {msg}", file=sys.stderr, flush=True)

    # -- Phase 3: Open/create project + import ydb ----------------------
    project_dir = os.path.dirname(os.path.abspath(ydb_path))
    yjk_project = os.path.join(project_dir, f"{project_name}.yjk")

    print(f"[yjk_driver] Phase 3: project = {yjk_project}", file=sys.stderr, flush=True)
    if os.path.isfile(yjk_project):
        if not _run_cmd("UIOpen", yjk_project):
            _error("YJK crashed while opening project")
            return 1
    else:
        if not _run_cmd("UINew", yjk_project):
            _error("YJK crashed while creating new project")
            return 1

    if not _run_cmd("yjk_importydb", ydb_path):
        _error("YJK crashed while importing YDB file - the model may have invalid geometry or sections")
        return 1

    # -- Phase 4: Model preparation (exact three_story_steel_frame.py) --
    print("[yjk_driver] Phase 4: model repair / prep", file=sys.stderr, flush=True)
    if not _run_cmd("yjk_repair"):
        _error("YJK crashed during model repair")
        return 1
    if not _run_cmd("yjk_save"):
        _error("YJK crashed during save")
        return 1
    if not _run_cmd("yjk_formslab_alllayer"):
        _error("YJK crashed during slab formation")
        return 1
    if not _run_cmd("yjk_setlayersupport"):
        _error("YJK crashed during layer support setup")
        return 1

    # -- Phase 5: Preprocessing + full analysis -------------------------
    print("[yjk_driver] Phase 5: preprocessing + calculation", file=sys.stderr, flush=True)
    if not _run_cmd("yjkspre_genmodrel"):
        _error("YJK crashed during model relation generation")
        return 1
    if not _run_cmd("yjktransload_tlplan"):
        _error("YJK crashed during plan load transfer")
        return 1
    if not _run_cmd("yjktransload_tlvert"):
        _error("YJK crashed during vertical load transfer")
        return 1
    if not _run_cmd("SetCurrentLabel", "IDSPRE_ROOT"):
        _error("YJK crashed during label switch")
        return 1
    if not _run_cmd("yjkdesign_dsncalculating_all"):
        _error("YJK crashed during design calculation - this often happens when the model has no valid structural data or missing sections")
        return 1
    if not _run_cmd("SetCurrentLabel", "IDDSN_DSP"):
        _error("YJK crashed during final label switch")
        return 1

    print("[yjk_driver] Phase 5 complete: analysis finished", file=sys.stderr, flush=True)

    # -- Phase 6: Skip result extraction for now -------------------------
    # TODO: implement structured result extraction via yjks_pyload
    print("[yjk_driver] Phase 6: result extraction skipped (not yet implemented)", file=sys.stderr, flush=True)

    # -- Phase 7: Build final output ------------------------------------
    warnings: list[str] = []
    warnings.append("Structured result extraction not yet implemented; returning .OUT files as fallback")

    output: dict = {
        "status": "success",
        "summary": {
            "engine": "yjk-static",
            "ydb_path": ydb_path,
            "yjk_project": yjk_project,
            "work_dir": work_dir,
        },
        "data": {},
        "detailed": {"raw_output": _collect_out_files(work_dir)},
        "warnings": warnings,
    }

    _emit_json(output)
    print("[yjk_driver] done", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
