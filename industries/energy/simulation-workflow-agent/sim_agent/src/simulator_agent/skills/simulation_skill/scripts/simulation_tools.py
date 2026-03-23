# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Simulation Tools for OPM Flow

Tools for running, monitoring, and parsing OPM Flow simulations.
"""

import json
import logging
import os
import re
import smtplib
import subprocess
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Optional

from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field


# ============================================================================
# Input Schemas
# ============================================================================


class RunSimulationInput(BaseModel):
    data_file: str = Field(..., description="Path to the simulator input (DATA) file")
    output_dir: Optional[str] = Field(
        default=None, description="Directory for output files (default: same as DATA file)"
    )
    num_threads: int = Field(
        default=1, description="Number of threads for parallel simulation"
    )
    num_mpi_processes: int = Field(
        default=1,
        description="Number of MPI processes (np). When > 1, runs via mpirun -np N flow ...",
    )
    additional_args: Optional[str] = Field(
        default=None, description="Additional command-line arguments"
    )
    background: bool = Field(
        default=True,
        description=(
            "If True, start flow and return immediately. "
            "If False, wait for completion and return full report: on failure includes return code, stdout, stderr, and parsed PRT errors/tail."
        ),
    )


class MonitorSimulationInput(BaseModel):
    output_dir: str = Field(..., description="Directory containing simulation output files")
    tail_lines: int = Field(
        default=80, description="Number of lines to read from end of PRT file"
    )
    use_llm_summary: bool = Field(
        default=False, description="Summarize the PRT tail with an LLM"
    )
    llm_model: Optional[str] = Field(
        default=None, description="Optional LLM model override for summary"
    )


class StopSimulationInput(BaseModel):
    pid: int = Field(..., description="Process ID to stop")
    output_dir: Optional[str] = Field(
        default=None, description="Optional output directory with run metadata"
    )
    force: bool = Field(default=False, description="Force kill the process")


class NotifyOnCompletionInput(BaseModel):
    output_dir: str = Field(..., description="Directory containing simulation output files")
    to_email: str = Field(..., description="Recipient email address")
    subject: Optional[str] = Field(
        default="Simulation completed",
        description="Email subject",
    )
    body: Optional[str] = Field(
        default=None, description="Optional email body override"
    )
    tail_lines: int = Field(
        default=80, description="Number of lines to read from end of PRT file"
    )


class PlotSummaryMetricInput(BaseModel):
    output_dir: str = Field(..., description="Directory containing simulation output files")
    metric_request: str = Field(
        ...,
        description=(
            "User request or summary keyword(s). For multiple metrics on one plot use comma-separated keywords, e.g. 'FOPT, FWPT' or 'FOPT,FWPT'."
        ),
    )
    manual_hint: Optional[str] = Field(
        default=None,
        description="Optional manual context or retrieved snippet to help map keywords",
    )
    save_path: Optional[str] = Field(
        default=None, description="Optional path to save the plot image"
    )


class PlotCompareSummaryMetricInput(BaseModel):
    output_dir: str = Field(
        ...,
        description=(
            "Directory to save the plot and, when not using case_paths, directory containing .SMSPEC files to compare."
        ),
    )
    metric_request: str = Field(
        ...,
        description="Summary keyword to compare, e.g. FOPT (cumulative oil), FOPR (oil rate)",
    )
    case_stems: Optional[str] = Field(
        default=None,
        description=(
            "Comma-separated case name stems to compare (e.g. SPE10_TOPLAYER,SPE10_TOPLAYER_AGENT_GENERATED). "
            "If omitted and case_paths not set, all .SMSPEC files in output_dir are compared."
        ),
    )
    case_paths: Optional[str] = Field(
        default=None,
        description=(
            "Comma-separated paths to DATA files (or .SMSPEC) for the cases to compare. "
            "Use when comparing cases from different directories (e.g. BASE/SPE10.DATA and INFILL/SPE10_INFILL.DATA)."
        ),
    )
    save_path: Optional[str] = Field(
        default=None, description="Optional path to save the comparison plot image"
    )


# ============================================================================
# Helper Functions
# ============================================================================

# When the agent runs in Docker, user paths (e.g. /home/user/.../sim_agent/data/...)
# don't exist in the container. Set OPM_PROJECT_ROOT in the container to the path to
# the sim_agent directory (e.g. /app/sim_agent); paths containing "sim_agent"
# will be resolved relative to it.
def _resolve_data_file_path(data_file: str) -> Path:
    """Resolve DATA file path, including host path -> container path when in Docker."""
    p = Path(data_file)
    if p.exists():
        return p.resolve()
    # Try relative to cwd (e.g. data/knowledge_base/examples/spe1/SPE1CASE1.DATA)
    cwd_candidate = (Path.cwd() / data_file).resolve()
    if cwd_candidate.exists():
        return cwd_candidate
    # In Docker: resolve host path to container path using OPM_PROJECT_ROOT
    project_root = os.environ.get("OPM_PROJECT_ROOT")
    if project_root:
        root = Path(project_root)
        # Strip host path prefix: .../sim_agent/data/... -> data/...
        if "sim_agent" in data_file:
            parts = data_file.split("sim_agent", 1)
            suffix = parts[-1].lstrip("/\\")
        elif "data" in data_file:
            parts = data_file.split("data", 1)
            suffix = "data" + parts[-1]
        elif data_file.startswith("/knowledge_base") or data_file.startswith("knowledge_base"):
            # LLM or user sometimes drops "data/" prefix; resolve as data/knowledge_base/...
            rest = data_file.split("knowledge_base", 1)[-1].lstrip("/\\")
            suffix = "data/knowledge_base/" + rest if rest else "data/knowledge_base"
        else:
            suffix = data_file
        container_candidate = (root / suffix).resolve()
        if container_candidate.exists():
            return container_candidate
    return p


def _parse_prt_file(prt_path: Path) -> Dict[str, any]:
    """
    Parse OPM .PRT file for progress and warnings.
    
    Returns dict with:
    - current_time: Current simulation time
    - total_time: Total simulation time
    - progress_pct: Progress percentage
    - warnings: List of warning messages
    - errors: List of error messages
    """
    if not prt_path.exists():
        return {
            "status": "not_started",
            "message": "PRT file not found"
        }
    
    try:
        with open(prt_path, 'r') as f:
            content = f.read()
        
        # Extract timestep information
        # This is a simplified parser - real implementation would be more robust
        lines = content.split('\n')
        
        current_time = None
        warnings = []
        errors = []
        
        for line in lines:
            # Look for timestep information
            if 'Time step' in line or 'Report step' in line:
                # Extract time information
                pass
            
            # Look for warnings
            if 'Warning' in line or 'WARNING' in line:
                warnings.append(line.strip())
            
            # Look for error messages (skip option names like ContinueOnConvergenceError="0")
            line_stripped = line.strip()
            line_upper = line.upper()
            is_option_key = bool(re.search(r"\w+Error\s*=", line) or re.search(r"\w+Error=\"", line))
            is_error_msg = (
                line_stripped.startswith("Error:")
                or " Error:" in line
                or (line_upper.startswith("ERROR") and ":" in line)
                or " Unrecoverable errors" in line_upper
                or "Error summary:" in line_upper
                or ("FATAL" in line_upper and "=" not in line)
                or ("EXCEPTION" in line_upper and "=" not in line)
                or re.search(r"\bfailed\b", line_upper)
            )
            if is_error_msg and not is_option_key:
                errors.append(line_stripped)
        
        return {
            "status": "running",
            "warnings": warnings[-10:] if warnings else [],
            "errors": errors[-20:] if errors else [],  # Keep more errors for failure report
            "message": f"Found {len(warnings)} warnings, {len(errors)} errors"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error parsing PRT file: {str(e)}"
        }


def _find_case_name(data_file: Path) -> str:
    """Extract case name from DATA file path."""
    # OPM uses the DATA file name (without extension) as the case name
    return data_file.stem


def _read_tail(file_path: Path, lines: int = 80) -> str:
    """Read last N lines from a text file without loading it fully."""
    if lines <= 0:
        return ""
    buffer_size = 4096
    data = bytearray()
    with open(file_path, "rb") as f:
        f.seek(0, os.SEEK_END)
        position = f.tell()
        while position > 0 and data.count(b"\n") <= lines:
            read_size = min(buffer_size, position)
            position -= read_size
            f.seek(position)
            data = f.read(read_size) + data
        text = data.decode(errors="replace")
    return "\n".join(text.splitlines()[-lines:])


def _write_run_metadata(output_dir: Path, metadata: Dict[str, object]) -> Path:
    """Write run metadata for background process tracking."""
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_path = output_dir / "run.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)
    return meta_path


def _is_simulation_complete(prt_tail_text: str) -> bool:
    return "End of simulation" in prt_tail_text or "End of Simulation" in prt_tail_text


def _send_email(to_email: str, subject: str, body: str) -> str:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_SENDER", username)
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    if not host or not sender:
        return "SMTP_HOST and SMTP_SENDER (or SMTP_USERNAME) must be set."

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as server:
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(msg)

    return "sent"


# ============================================================================
# Tool Functions
# ============================================================================


@tool("run_simulation", args_schema=RunSimulationInput)
def run_simulation(
    data_file: str,
    output_dir: Optional[str] = None,
    num_threads: int = 1,
    num_mpi_processes: int = 1,
    additional_args: Optional[str] = None,
    background: bool = True,
    ) -> str:
    """
    Run a reservoir simulation.
    Use background=False to wait for completion and get a full error report (return code, stdout, stderr, PRT errors and tail) when the run fails.
    """
    try:
        data_file_path = _resolve_data_file_path(data_file)
        logging.getLogger(__name__).debug(
            "run_simulation: requested data_file=%s -> resolved=%s", data_file, data_file_path
        )
        if not data_file_path.exists():
            return f"Error: DATA file not found: {data_file}. (In Docker, set OPM_PROJECT_ROOT to the sim_agent path in the container.)"

        # Determine output directory
        if output_dir is None:
            output_dir = data_file_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = ["flow", str(data_file_path)]

        if output_dir != data_file_path.parent:
            cmd.append(f"--output-dir={str(output_dir)}")

        if num_threads > 1:
            cmd.extend(["--threads-per-process", str(num_threads)])

        if additional_args:
            cmd.extend(additional_args.split())
        # When running in Docker, Flow 2025.x may report "Saturation Function End-point
        # Consistency" (SOGCR slightly negative) for decks that run fine on host. Set
        # OPM_FLOW_EXTRA_ARGS="--CheckSatfuncConsistency=0" to relax the check.
        extra = os.environ.get("OPM_FLOW_EXTRA_ARGS")
        if extra:
            cmd.extend(extra.split())

        # Wrap with mpirun when using multiple MPI processes
        if num_mpi_processes > 1:
            mpi_launcher = os.environ.get("OPM_MPI_LAUNCHER", "mpirun")
            cmd = [mpi_launcher, "-np", str(num_mpi_processes)] + cmd

        case_name = _find_case_name(data_file_path)

        # Run simulation
        if background:
            stdout_path = Path(output_dir) / f"{case_name}.stdout.log"
            stderr_path = Path(output_dir) / f"{case_name}.stderr.log"
            stdout_f = open(stdout_path, "w")
            stderr_f = open(stderr_path, "w")
            proc = subprocess.Popen(
                cmd,
                stdout=stdout_f,
                stderr=stderr_f,
                cwd=data_file_path.parent,
            )
            # Close in parent to avoid file descriptor leaks
            stdout_f.close()
            stderr_f.close()
            meta_path = _write_run_metadata(
                Path(output_dir),
                {
                    "pid": proc.pid,
                    "case_name": case_name,
                    "data_file": str(data_file_path),
                    "output_dir": str(output_dir),
                    "stdout_log": str(stdout_path),
                    "stderr_log": str(stderr_path),
                    "command": cmd,
                    "start_time": time.time(),
                },
            )
            # Check if the process exited immediately (e.g., bad args)
            return_code = proc.poll()
            if return_code is not None:
                stderr_tail = ""
                if stderr_path.exists():
                    with open(stderr_path, "r") as f:
                        stderr_tail = f.read()[-1000:]
                return f"""
✗ Simulation failed to start

Case: {case_name}
Return code: {return_code}
Output directory: {output_dir}
Stdout log: {stdout_path}
Stderr log: {stderr_path}
Run metadata: {meta_path}

Error output (tail):
{stderr_tail or "(empty)"}
"""
            return f"""
✓ Simulation started in background

Case: {case_name}
PID: {proc.pid}
Output directory: {output_dir}
Stdout log: {stdout_path}
Stderr log: {stderr_path}
Run metadata: {meta_path}

Check progress via the .PRT file.
"""

        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=data_file_path.parent,
        )
        elapsed_time = time.time() - start_time

        if result.returncode == 0:
            return f"""
✓ Simulation completed successfully

Case: {case_name}
Data file run: {data_file_path}
Runtime: {elapsed_time:.1f} seconds
Output directory: {output_dir}

You can ask the assistant to plot results or read summary files.
"""
        # Non-background run failed: build a full report with return code, stdout, stderr, and PRT
        report_lines = [
            "✗ Simulation failed",
            "",
            f"Case: {case_name}",
            f"Data file run: {data_file_path}",
            f"Return code: {result.returncode}",
            f"Runtime: {elapsed_time:.1f} seconds",
            f"Output directory: {output_dir}",
            "",
            "--- Stdout (last 2000 chars) ---",
            (result.stdout or "")[-2000:].strip() or "(empty)",
            "",
            "--- Stderr (last 2000 chars) ---",
            (result.stderr or "")[-2000:].strip() or "(empty)",
        ]
        # Parse PRT file for errors and tail (prefer the one matching this run's case name)
        preferred_prt = Path(output_dir) / f"{case_name}.PRT"
        prt_files = list(Path(output_dir).glob("*.PRT"))
        if preferred_prt.exists():
            prt_path = preferred_prt
        elif prt_files:
            prt_path = prt_files[0]
        else:
            prt_path = None
        if prt_path is not None:
            prt_status = _parse_prt_file(prt_path)
            report_lines.append("")
            report_lines.append("--- PRT file summary ---")
            report_lines.append(f"PRT file: {prt_path.name}")
            if prt_status.get("errors"):
                report_lines.append("Errors found in PRT:")
                for err in prt_status["errors"]:
                    report_lines.append(f"  {err}")
            if prt_status.get("warnings"):
                report_lines.append("Warnings in PRT:")
                for w in prt_status["warnings"][-10:]:
                    report_lines.append(f"  {w}")
            prt_tail = _read_tail(prt_path, lines=50)
            if prt_tail:
                report_lines.append("")
                report_lines.append("--- PRT tail (last 50 lines) ---")
                report_lines.append(prt_tail)
        else:
            report_lines.append("")
            report_lines.append("(No .PRT file found in output directory.)")
        return "\n".join(report_lines)
    except FileNotFoundError:
        return """
Error: OPM Flow not found in PATH

Please ensure OPM Flow is installed and accessible.
- Ubuntu: sudo apt install opm-simulators
- From source: https://opm-project.org
- Check installation: which flow
"""
    except Exception as e:
        return f"Error running simulation: {str(e)}"
    

@tool("monitor_simulation", args_schema=MonitorSimulationInput)
def monitor_simulation(
    output_dir: str,
    tail_lines: int = 80,
    use_llm_summary: bool = False,
    llm_model: Optional[str] = None,
) -> str:
    """
    Monitor the progress of a running OPM Flow simulation.
    """
    try:
        output_path = Path(output_dir)

        if not output_path.exists():
            return f"Error: Output directory not found: {output_dir}"

        # Find .PRT file
        prt_files = list(output_path.glob("*.PRT"))

        if not prt_files:
            return f"No .PRT file found in {output_dir}. Simulation may not have started."

        prt_file = prt_files[0]

        # Parse PRT file
        status = _parse_prt_file(prt_file)

        # Read tail
        prt_tail_text = _read_tail(prt_file, lines=tail_lines)

        # Format report
        report = ["=== Simulation Progress ===\n"]
        report.append(f"Status: {status['status']}")
        report.append(f"PRT file: {prt_file.name}")
        report.append(f"Tail lines: {tail_lines}\n")

        if status.get("message"):
            report.append(status["message"])

        report.append("\n--- PRT Tail ---")
        report.append(prt_tail_text or "(empty)")

        if use_llm_summary:
            if not os.getenv("NVIDIA_API_KEY"):
                report.append("\nLLM summary skipped: NVIDIA_API_KEY not set.")
            else:
                from simulator_agent.config import get_config
                from llm_provider import ChatOpenAI

                model = llm_model or get_config().get_llm_model(use_for="tool")
                llm = ChatOpenAI(model=model, max_tokens=512)
                prompt = (
                    "Summarize the following OPM Flow PRT tail. "
                    "Focus on whether the run is progressing, and mention any errors "
                    "or convergence issues. Keep it concise.\n\n"
                    f"{prt_tail_text}"
                )
                summary = llm.invoke(prompt).content.strip()
                report.append("\n--- LLM Summary ---")
                report.append(summary or "(empty)")

        return "\n".join(report)

    except Exception as e:
        return f"Error monitoring simulation: {str(e)}"
    

@tool("stop_simulation", args_schema=StopSimulationInput)
def stop_simulation(
    pid: int, output_dir: Optional[str] = None, force: bool = False
) -> str:
    """
    Stop a running OPM Flow simulation by PID.
    """
    try:
        signal = "-9" if force else "-15"
        result = subprocess.run(
            ["kill", signal, str(pid)], capture_output=True, text=True
        )
        status = "terminated" if result.returncode == 0 else "not_terminated"

        meta_path = None
        if output_dir:
            meta_path = Path(output_dir) / "run.json"
            if meta_path.exists():
                metadata = json.loads(meta_path.read_text())
                metadata["stop_time"] = time.time()
                metadata["stop_signal"] = "SIGKILL" if force else "SIGTERM"
                metadata["stop_status"] = status
                with open(meta_path, "w") as f:
                    json.dump(metadata, f, indent=2, sort_keys=True)

        if result.returncode != 0:
            return (
                "Failed to stop process.\n"
                f"PID: {pid}\n"
                f"Error: {result.stderr.strip() or '(empty)'}"
            )

        return (
            "Simulation stop requested.\n"
            f"PID: {pid}\n"
            f"Signal: {'SIGKILL' if force else 'SIGTERM'}\n"
            f"Run metadata: {meta_path or '(not provided)'}"
        )

    except Exception as e:
        return f"Error stopping simulation: {str(e)}"


@tool("notify_on_completion", args_schema=NotifyOnCompletionInput)
def notify_on_completion(
    output_dir: str,
    to_email: str,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    tail_lines: int = 80,
) -> str:
    """
    Send an email notification if the simulation has completed.
    """
    try:
        output_path = Path(output_dir)
        if not output_path.exists():
            return f"Error: Output directory not found: {output_dir}"

        prt_files = list(output_path.glob("*.PRT"))
        if not prt_files:
            return f"No .PRT file found in {output_dir}. Simulation may not have started."

        prt_file = prt_files[0]
        prt_tail_text = _read_tail(prt_file, lines=tail_lines)
        if not _is_simulation_complete(prt_tail_text):
            return "Simulation not completed yet. No email sent."

        email_subject = subject or "Simulation completed"
        email_body = body or (
            "Simulation completed.\n\n"
            f"Output directory: {output_dir}\n"
            f"PRT file: {prt_file.name}\n\n"
            "PRT tail:\n"
            f"{prt_tail_text}"
        )
        result = _send_email(to_email, email_subject, email_body)
        if result != "sent":
            return f"Email not sent: {result}"

        return f"Email sent to {to_email}"

    except Exception as e:
        return f"Error sending notification: {str(e)}"


def _resolve_metric_keywords(
    metric_request: str, manual_hint: Optional[str], available: set
) -> list:
    """Resolve metric_request (possibly comma-separated) to list of summary keywords present in available."""
    raw = [s.strip() for s in metric_request.split(",") if s.strip()]
    keywords = []
    for request in raw:
        keyword = None
        if request in available:
            keyword = request
        if not keyword and manual_hint:
            candidates = re.findall(r"\b[A-Z]{3,6}\b", manual_hint)
            for candidate in candidates:
                if candidate in available and candidate not in keywords:
                    keyword = candidate
                    break
        if keyword and keyword not in keywords:
            keywords.append(keyword)
    return keywords


@tool("plot_summary_metric", args_schema=PlotSummaryMetricInput)
def plot_summary_metric(
    output_dir: str,
    metric_request: str,
    manual_hint: Optional[str] = None,
    save_path: Optional[str] = None,
) -> str:
    """
    Plot one or more summary metrics from OPM Flow outputs on the same plot.
    Pass comma-separated keywords for multiple metrics (e.g. FOPT, FWPT).
    """
    try:
        output_path = Path(output_dir)
        if not output_path.exists():
            return f"Error: Output directory not found: {output_dir}"

        smspec_files = list(output_path.glob("*.SMSPEC"))
        if not smspec_files:
            return f"Error: No .SMSPEC file found in {output_dir}"

        # Import locally to avoid hard dependency if plotting isn't used
        import matplotlib.pyplot as plt  # noqa: WPS433
        from ...results_skill.scripts.ecl_reader import EclReader

        reader = EclReader(str(smspec_files[0]))
        available = set(reader.list_smry_keys())

        keywords = _resolve_metric_keywords(metric_request, manual_hint, available)
        if not keywords:
            sample = ", ".join(sorted(list(available))[:25])
            return (
                "Error: Requested metric(s) not found in summary keys. "
                f"Request: {metric_request}\n"
                f"Sample keys: {sample}\n"
                "Tip: Use comma-separated keywords (e.g. FOPT, FWPT) for multiple metrics; "
                "or use simulator_manual retriever and pass manual_hint."
            )

        smry = reader.read_smry_vectors(keywords)
        time_len = len(smry[keywords[0]])
        time_values, time_axis_label = _smry_time_values(smry, time_len)

        plt.figure(figsize=(10, 6))
        for keyword in keywords:
            metric_values = smry[keyword]
            if len(metric_values) != time_len:
                continue
            line_color = _summary_metric_color(keyword)
            plt.plot(time_values, metric_values, label=keyword, color=line_color)
        plt.xlabel(time_axis_label)
        plt.ylabel(", ".join(keywords) if len(keywords) > 1 else keywords[0])
        plt.title("Summary metric: " + keywords[0] if len(keywords) == 1 else "Summary metrics: " + ", ".join(keywords))
        plt.legend()

        name_part = "_".join(keywords)
        save_path = save_path or str(output_path / f"plot_{name_part}.png")
        save_path = str(Path(save_path).resolve())
        # Ensure parent directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()

        return f"Plot saved to: {save_path}"

    except Exception as e:
        return f"Error plotting summary metric: {str(e)}"


def _summary_metric_color(keyword: str) -> str:
    """Return line color for summary metric: green=oil, blue=water, red=gas. ECL convention: FO/FOPT/FOPR=oil, FW/FWPT/FWPR=water, FG/FGPT/FGPR=gas."""
    k = keyword.upper()
    if k.startswith("FO") or k.startswith("WO") or "OPT" in k or "OPR" in k or "OIR" in k or "OIT" in k:
        return "green"
    if (
        k.startswith("FW")
        or k.startswith("WW")
        or "WPT" in k
        or "WPR" in k
        or "WCT" in k
        or "WIR" in k
        or "WIT" in k
    ):
        return "blue"
    if k.startswith("FG") or k.startswith("WG") or "GPT" in k or "GPR" in k or "GOR" in k or "VIR" in k or "VIT" in k:
        return "red"
    return "gray"


def _smry_time_values(smry, length: int):
    """Get time axis from summary dict (EclReader.read_smry_vectors); return (time_values, time_axis_label). Prefer TIME (days), then dates(), else step index."""
    # 1) Prefer summary vector "TIME" (simulation time in days) — same length as other summary vectors
    try:
        if "TIME" in smry.keys():
            t = smry["TIME"]
            if t is not None and len(t) == length:
                return list(t), "Time (days)"
    except Exception:
        pass
    # 2) Try dates() / get_dates() for calendar date x-axis
    for attr in ("dates", "get_dates", "time"):
        if hasattr(smry, attr):
            fn = getattr(smry, attr)
            if callable(fn):
                try:
                    time_values = fn()
                    if time_values is not None and len(time_values) == length:
                        return list(time_values), "Date"
                except Exception:
                    continue
            else:
                time_values = fn
                if time_values is not None and len(time_values) == length:
                    return list(time_values), "Date"
                break
    # 3) Fallback: report step index
    return list(range(length)), "Time step"


def _resolve_compare_case_paths(case_paths_str: str) -> tuple[list[Path], list[str]]:
    """Resolve comma-separated DATA file paths to (list of .SMSPEC Paths, list of stems)."""
    smspec_files = []
    stems = []
    for raw in case_paths_str.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if not raw.upper().endswith(".DATA"):
            raise ValueError(
                f"case_paths entries must be paths to .DATA files (simulation must have been run), got: {raw}"
            )
        resolved = _resolve_data_file_path(raw)
        if not resolved.exists():
            raise FileNotFoundError(f"DATA file not found: {raw} (resolved: {resolved})")
        out_dir = resolved.parent
        stem = resolved.stem
        smspec_path = out_dir / f"{stem}.SMSPEC"
        if not smspec_path.exists():
            raise FileNotFoundError(
                f".SMSPEC not found for {stem} at {smspec_path}. Run the simulation for that case first."
            )
        smspec_files.append(smspec_path)
        stems.append(stem)
    return smspec_files, stems


@tool("plot_compare_summary_metric", args_schema=PlotCompareSummaryMetricInput)
def plot_compare_summary_metric(
    output_dir: str,
    metric_request: str,
    case_stems: Optional[str] = None,
    case_paths: Optional[str] = None,
    save_path: Optional[str] = None,
) -> str:
    """
    Plot a summary metric for two or more cases on the same axes for comparison.
    Use case_paths when comparing cases from different directories (e.g. two DATA file paths).
    """
    try:
        output_path = Path(output_dir)
        if not output_path.exists():
            return f"Error: Output directory not found: {output_dir}"

        if case_paths and case_paths.strip():
            try:
                smspec_files, stems = _resolve_compare_case_paths(case_paths.strip())
            except (FileNotFoundError, ValueError) as e:
                return f"Error: {e}"
            requested_stems = stems
            # Use first case's output dir for saving if given output_dir does not exist (e.g. host path)
            if not output_path.exists() and smspec_files:
                output_path = smspec_files[0].parent
        elif case_stems and case_stems.strip():
            requested_stems = [s.strip() for s in case_stems.split(",") if s.strip()]
            smspec_files = []
            for stem in requested_stems:
                f = output_path / f"{stem}.SMSPEC"
                if f.exists():
                    smspec_files.append(f)
            stems = [f.stem for f in smspec_files]
            if not smspec_files:
                return (
                    "Error: No case .SMSPEC files found. "
                    "For comparison, run both the baseline and the modified case in the same output directory."
                )
        else:
            requested_stems = []
            smspec_files = sorted(output_path.glob("*.SMSPEC"))
            if not smspec_files:
                return f"Error: No .SMSPEC file found in {output_dir}"
            stems = [f.stem for f in smspec_files]

        import matplotlib.pyplot as plt  # noqa: WPS433
        from ...results_skill.scripts.ecl_reader import EclReader

        request = metric_request.strip().upper()
        series = []  # (stem, time_values, metric_values, time_label)
        keyword = None

        for smspec_file, stem in zip(smspec_files, stems):
            reader = EclReader(str(smspec_file))
            available = set(reader.list_smry_keys())
            if keyword is None:
                if request in available:
                    keyword = request
                else:
                    return (
                        f"Error: Metric '{metric_request}' not found in case {stem}. "
                        f"Sample keys: {', '.join(sorted(available)[:15])}"
                    )
            elif keyword not in available:
                return (
                    f"Error: Metric '{keyword}' not in case {stem}. "
                    f"Sample keys: {', '.join(sorted(available)[:15])}"
                )
            smry = reader.read_smry_vectors([keyword])
            metric_values = smry[keyword]
            time_values, time_label = _smry_time_values(smry, len(metric_values))
            series.append((stem, time_values, metric_values, time_label))

        if not series:
            return "Error: No series to plot."

        time_axis_label = series[0][3]
        line_color = _summary_metric_color(keyword)
        # Different linestyles per case so multiple series are distinguishable (same metric color)
        linestyles = ["-", "--", "-.", ":"]  # solid, dashed, dashdot, dotted
        plt.figure(figsize=(10, 6))
        for i, (stem, time_values, metric_values, _) in enumerate(series):
            ls = linestyles[i % len(linestyles)]
            plt.plot(time_values, metric_values, label=stem, color=line_color, linestyle=ls)
        plt.xlabel(time_axis_label)
        plt.ylabel(keyword)
        plt.title(f"Comparison: {keyword}")
        plt.legend()
        plt.grid(True, alpha=0.3)

        save_path = save_path or str(output_path / f"plot_compare_{keyword}.png")
        save_path = str(Path(save_path).resolve())
        # Ensure parent directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()

        if case_stems and len(requested_stems) >= 2 and len(smspec_files) == 1:
            return (
                f"Comparison plot saved to: {save_path}\n"
                f"(Only one case found: {stems[0]}. Run the baseline case in this directory to compare both.)"
            )
        return f"Comparison plot saved to: {save_path}"

    except Exception as e:
        return f"Error plotting comparison: {str(e)}"
