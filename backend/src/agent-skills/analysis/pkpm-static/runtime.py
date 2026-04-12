"""PKPM static analysis skill — runtime.

Converts a V2 StructureModelV2 JSON payload into a PKPM JWS project file
via APIPyInterface, then invokes JWSCYCLE.exe for structural analysis.

Environment variables
---------------------
PKPM_CYCLE_PATH : str
    Full path to JWSCYCLE.exe on the local machine.
PKPM_WORK_DIR : str, optional
    Directory where PKPM project files are written.
    Defaults to a 'pkpm_projects' subfolder in the system temp directory.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict

from contracts import EngineNotAvailableError


def _check_pkpm_available() -> str:
    """Return PKPM_CYCLE_PATH or raise EngineNotAvailableError."""
    cycle_path = os.getenv("PKPM_CYCLE_PATH", "").strip()
    if not cycle_path:
        raise EngineNotAvailableError(
            engine="pkpm",
            reason=(
                "PKPM_CYCLE_PATH environment variable is not set. "
                "Set it to the full path of JWSCYCLE.exe."
            ),
        )
    if not Path(cycle_path).is_file():
        raise EngineNotAvailableError(
            engine="pkpm",
            reason=f"JWSCYCLE.exe not found at: {cycle_path}",
        )
    return cycle_path


def _import_apipyinterface() -> None:
    """Ensure APIPyInterface can be imported; raise EngineNotAvailableError if not."""
    try:
        import APIPyInterface  # noqa: F401
    except ImportError as exc:
        raise EngineNotAvailableError(
            engine="pkpm",
            reason=f"APIPyInterface Python extension not found: {exc}",
        ) from exc


def run_analysis(model: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Convert V2 model to PKPM JWS and run SATWE static analysis.

    Parameters
    ----------
    model : dict
        Deserialized StructureModelV2 payload (raw dict, not Pydantic instance).
    parameters : dict
        Analysis parameters forwarded from the API request.

    Returns
    -------
    dict
        AnalysisResult-shaped dict with status / summary / detailed / warnings.

    Raises
    ------
    EngineNotAvailableError
        When PKPM is not installed or APIPyInterface is unavailable.
    RuntimeError
        When JWS generation or SATWE analysis fails.
    """
    cycle_path = _check_pkpm_available()
    _import_apipyinterface()

    from pkpm_converter import convert_v2_to_jws  # local import after availability check

    # ---- Determine working directory ----
    base_work_dir = Path(
        os.getenv("PKPM_WORK_DIR", "").strip()
        or Path(tempfile.gettempdir()) / "pkpm_projects"
    )
    project_name = f"sc_{uuid.uuid4().hex[:8]}"
    work_dir = base_work_dir / project_name

    warnings: list[str] = []

    # ---- Phase 1: Generate JWS ----
    try:
        jws_path = convert_v2_to_jws(model, work_dir, project_name)
    except Exception as exc:
        raise RuntimeError(f"PKPM JWS generation failed: {exc}") from exc

    # ---- Phase 2: Run SATWE via JWSCYCLE.exe ----
    try:
        result = subprocess.run(
            [cycle_path, str(jws_path)],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            stderr_snippet = (result.stderr or "")[:500]
            raise RuntimeError(
                f"JWSCYCLE.exe exited with code {result.returncode}. "
                f"stderr: {stderr_snippet}"
            )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("PKPM analysis timed out after 600 s") from exc
    except FileNotFoundError as exc:
        raise RuntimeError(f"Cannot launch JWSCYCLE.exe: {exc}") from exc

    # ---- Phase 3: Collect results ----
    result_files = list(work_dir.glob("*.OUT")) + list(work_dir.glob("*.out"))
    summary_lines: list[str] = []
    for rfile in result_files[:3]:
        try:
            text = rfile.read_text(encoding="gbk", errors="replace")
            summary_lines.append(f"=== {rfile.name} ===\n{text[:2000]}")
        except Exception as read_exc:
            warnings.append(f"Could not read result file {rfile.name}: {read_exc}")

    return {
        "status": "success",
        "summary": {
            "engine": "pkpm-static",
            "jws_path": str(jws_path),
            "work_dir": str(work_dir),
            "output_files": [str(p) for p in result_files],
        },
        "detailed": {
            "raw_output": "\n\n".join(summary_lines) if summary_lines else "(no .OUT files found)",
        },
        "warnings": warnings,
    }
