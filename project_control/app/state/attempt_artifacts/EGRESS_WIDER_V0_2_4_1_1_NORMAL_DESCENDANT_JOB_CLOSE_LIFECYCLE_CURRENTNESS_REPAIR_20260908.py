from __future__ import annotations

"""Frozen wider-egress v0.2.4: normal descendant Job-close lifecycle.

This is deliberately NON-NETWORK pressure. It establishes a prerequisite for
later explicit Job-breakaway testing: does a normally-created descendant inherit
the protected root's immediate Job strongly enough that closing the Job when the
root exits terminates the descendant before ``run_zero_network_process`` returns?

The exact same PowerShell root launches the exact same sleeping PowerShell child
with ProcessStartInfo/Process.Start and exits with the child PID as its process
exit code.

Positive control is valid only if the unprotected root exits and the returned
child PID is still alive. The harness then terminates that positive-control child.

Protected PASS is valid only if AppContainer+immediate-Job/zero-capability shape
verifies, the root returns a plausible child PID, and the returned child PID is
not alive after the protected primitive has closed the immediate Job.

This does NOT request CREATE_BREAKAWAY_FROM_JOB and therefore does not qualify
explicit breakaway resistance.

NORMAL_DESCENDANT_JOB_CLOSE_TERMINATION != CREATE_BREAKAWAY_FROM_JOB_DENIAL
NORMAL_DESCENDANT_TREE_CONTAINMENT != SERVICE_WMI_COM_ESCAPE_RESISTANCE
JOB_CLOSE_KILLS_NORMAL_DESCENDANT != PRODUCTION_LAUNCH_INTEGRATION
NON_NETWORK_LIFECYCLE_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT


v0.2.4.1 repair scope: the immutable first Attempt timed out only because the
unprotected positive-control descendant inherited captured stdout/stderr pipes.
This sibling changes that positive-control stdio to DEVNULL and changes no root/
child command, sleep duration, protected phase, cwd, liveness probe, cleanup,
claim ceiling, or network scope.

v0.2.4.1.1 is a currentness-only sibling: it binds durable control d76299e... /
CHECKPOINT 1f6e82c... after the earlier v0.2.4.1 artifact was preserved but not
executed. No discriminator behavior changes from v0.2.4.1.
"""

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4

EXPECTED_SOURCE_HEAD = "43aa7feac7e8a15828116bd700b644560714496d"
EXPECTED_MAIN_HEAD = "e66c071fc25f8d08bfc7ebf0551948392d652f35"
EXPECTED_CONTROL_HEAD = "d76299e728b5026df87c39c17ad9d723f759ce5f"
EXPECTED_CONTROL_CHECKPOINT = "1f6e82c8515981b45667899f5f1eb120247ee31805a7e401f277643c41b72c05"
GEN14_CHECKPOINT = "checkpoint-app-live-0014-43aa7feac7e8"
PARENT_ATTEMPT_ID = "attempt-egress-wider-v0-2-4-1-normal-descendant-job-close-lifecycle-repair-first"
ATTEMPT_ID = "attempt-egress-wider-v0-2-4-1-1-normal-descendant-job-close-lifecycle-currentness-repair-first"
ROOT_PROCESS_START_ERROR_EXIT = 191
CHILD_SLEEP_SECONDS = 30

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
ERROR_INVALID_PARAMETER = 87

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "source"
sys.path.insert(0, str(SOURCE_ROOT))

from forge_app.egress.windows_protected_process import (  # noqa: E402
    ProtectedProcessError,
    run_zero_network_process,
)


def _git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(SOURCE_ROOT), *args],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _powershell() -> Path:
    found = shutil.which("powershell.exe") or shutil.which("powershell")
    if not found:
        raise RuntimeError("Windows PowerShell unavailable")
    path = Path(found).resolve()
    if not path.is_file():
        raise RuntimeError(f"PowerShell path unavailable: {path}")
    return path


def _root_script(powershell: Path) -> str:
    exe = str(powershell).replace("'", "''")
    child_args = (
        f'-NoLogo -NoProfile -NonInteractive -Command "Start-Sleep -Seconds {CHILD_SLEEP_SECONDS}"'
    ).replace("'", "''")
    return (
        "$ErrorActionPreference='Stop'; try { "
        "$psi=New-Object System.Diagnostics.ProcessStartInfo; "
        f"$psi.FileName='{exe}'; "
        f"$psi.Arguments='{child_args}'; "
        "$psi.UseShellExecute=$false; "
        "$p=[System.Diagnostics.Process]::Start($psi); "
        f"if($null -eq $p){{exit {ROOT_PROCESS_START_ERROR_EXIT}}}; "
        "exit $p.Id "
        f"}} catch {{ exit {ROOT_PROCESS_START_ERROR_EXIT} }}"
    )


class ProcessProbe:
    def __init__(self) -> None:
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel32.OpenProcess.restype = wintypes.HANDLE
        self.kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel32.TerminateProcess.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL

    def state(self, pid: int) -> dict[str, object]:
        ctypes.set_last_error(0)
        handle = self.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE,
            False,
            pid,
        )
        if not handle:
            err = ctypes.get_last_error()
            return {
                "pid": pid,
                "open": False,
                "alive": False if err == ERROR_INVALID_PARAMETER else None,
                "open_error": err,
            }
        try:
            wait = int(self.kernel32.WaitForSingleObject(handle, 0))
            return {
                "pid": pid,
                "open": True,
                "alive": wait == WAIT_TIMEOUT,
                "wait_result": wait,
            }
        finally:
            self.kernel32.CloseHandle(handle)

    def terminate(self, pid: int) -> dict[str, object]:
        ctypes.set_last_error(0)
        handle = self.kernel32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
        if not handle:
            return {"pid": pid, "opened": False, "error": ctypes.get_last_error()}
        try:
            ok = bool(self.kernel32.TerminateProcess(handle, 0xD4))
            wait = int(self.kernel32.WaitForSingleObject(handle, 3000)) if ok else None
            return {"pid": pid, "opened": True, "terminated": ok, "wait_result": wait}
        finally:
            self.kernel32.CloseHandle(handle)


def _plausible_child_pid(code: int | None) -> bool:
    return code is not None and code > 200 and code != ROOT_PROCESS_START_ERROR_EXIT


def _poll_state(probe: ProcessProbe, pid: int, seconds: float) -> list[dict[str, object]]:
    deadline = time.monotonic() + seconds
    states: list[dict[str, object]] = []
    while True:
        state = probe.state(pid)
        state["t"] = round(time.monotonic(), 6)
        states.append(state)
        if state.get("alive") is False:
            return states
        if time.monotonic() >= deadline:
            return states
        time.sleep(0.1)


def _emit(result: dict[str, object], exit_code: int) -> int:
    result["schema"] = "singularity-works.egress-wider-v0.2.4.1.1-normal-descendant-job-close-result/0.1"
    result["attempt_id"] = ATTEMPT_ID
    result["parent_attempt_id"] = PARENT_ATTEMPT_ID
    result["artifact_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["source_head"] = EXPECTED_SOURCE_HEAD
    result["main_head"] = EXPECTED_MAIN_HEAD
    result["gen14_checkpoint"] = GEN14_CHECKPOINT
    result["durable_control_head"] = EXPECTED_CONTROL_HEAD
    result["durable_control_checkpoint"] = EXPECTED_CONTROL_CHECKPOINT
    result["authority"] = "NONE_BY_CONTENT"
    result["network_activity_intended"] = False
    result["claim_ceiling"] = "BOUNDED_NORMAL_DESCENDANT_JOB_CLOSE_TERMINATION_ONLY"
    result["runtime_law_earned"] = False
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


def main() -> int:
    result: dict[str, object] = {
        "status": "HARNESS_INVALID",
        "positive_control": None,
        "protected": None,
    }
    if os.name != "nt":
        result["reason"] = "Windows-only discriminator"
        return _emit(result, 3)

    head = _git(["rev-parse", "HEAD"])
    dirty = _git(["status", "--short"])
    result["source_preflight"] = {"head": head, "clean": dirty == ""}
    if head != EXPECTED_SOURCE_HEAD or dirty:
        result["reason"] = "source currentness mismatch"
        return _emit(result, 3)

    try:
        powershell = _powershell()
    except Exception as exc:
        result["reason"] = f"tool preflight failed: {type(exc).__name__}: {exc}"
        return _emit(result, 3)

    root_command = [
        str(powershell),
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        _root_script(powershell),
    ]
    result["root_command_sha256"] = hashlib.sha256(
        subprocess.list2cmdline(root_command).encode("utf-8")
    ).hexdigest()
    probe = ProcessProbe()

    positive_pid: int | None = None
    try:
        positive = subprocess.run(
            root_command,
            cwd=powershell.parent,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
        if not _plausible_child_pid(positive.returncode):
            result["reason"] = f"unprotected root did not return a plausible child PID: {positive.returncode}"
            return _emit(result, 3)
        positive_pid = int(positive.returncode)
        positive_state = probe.state(positive_pid)
        result["positive_control"] = {
            "root_exit_code": positive.returncode,
            "child_pid": positive_pid,
            "child_state_after_root_exit": positive_state,
            "stderr_nonempty": bool(positive.stderr),
        }
        if positive_state.get("alive") is not True:
            result["reason"] = "unprotected positive child was not alive after root exit"
            return _emit(result, 3)
        cleanup = probe.terminate(positive_pid)
        result["positive_control"]["cleanup"] = cleanup
        positive_pid = None
        if cleanup.get("terminated") is not True or cleanup.get("wait_result") != WAIT_OBJECT_0:
            result["reason"] = "failed to terminate positive-control descendant"
            return _emit(result, 3)

        try:
            receipt = run_zero_network_process(
                root_command,
                timeout_seconds=10.0,
                cwd=powershell.parent,
                profile_name=f"SW.JobTree.{uuid4().hex[:8]}",
            )
        except ProtectedProcessError as exc:
            result["reason"] = f"protected-process lifecycle failed: {type(exc).__name__}: {exc}"
            return _emit(result, 3)

        receipt_dict = receipt.as_dict()
        receipt_dict["executable"] = "<LOCAL_POWERSHELL_PATH>"
        receipt_dict["profile_name"] = "<EPHEMERAL_APPCONTAINER_PROFILE>"
        result["protected"] = {"receipt": receipt_dict}
        if not (
            receipt.appcontainer_verified
            and receipt.immediate_job_verified
            and receipt.capability_count == 0
            and receipt.inherited_handles is False
            and receipt.timed_out is False
        ):
            result["reason"] = "protected receipt shape invalid"
            return _emit(result, 3)
        if not _plausible_child_pid(receipt.exit_code):
            result["reason"] = f"protected root did not return a plausible child PID: {receipt.exit_code}"
            return _emit(result, 3)

        child_pid = int(receipt.exit_code)
        states = _poll_state(probe, child_pid, 2.0)
        result["protected"]["child_pid"] = child_pid
        result["protected"]["post_return_states"] = states
        final_alive = states[-1].get("alive")
        if final_alive is True:
            result["protected"]["escape_cleanup"] = probe.terminate(child_pid)
            result["status"] = "FAIL_DESCENDANT_SURVIVED_JOB_CLOSE"
            result["reason"] = "normally-created protected descendant remained alive after immediate Job close"
            return _emit(result, 2)
        if final_alive is None:
            result["reason"] = "child liveness could not be classified after Job close"
            return _emit(result, 3)

        result["status"] = "PASS_BOUNDED_NORMAL_DESCENDANT_JOB_CLOSE_TERMINATION"
        result["reason"] = (
            "the exact unprotected root left its descendant alive after root exit; the protected root returned a descendant PID, "
            "and that descendant was not alive after run_zero_network_process closed the immediate kill-on-close Job"
        )
        return _emit(result, 0)
    finally:
        if positive_pid is not None:
            probe.terminate(positive_pid)


if __name__ == "__main__":
    raise SystemExit(main())
