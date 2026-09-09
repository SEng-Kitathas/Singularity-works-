from __future__ import annotations

"""Frozen wider-egress v0.2.6.1: ShellExecuteExW process-lifecycle currentness sibling.

This is a materially distinct NON-NETWORK launch API from the already-qualified
CreateProcessW / CREATE_BREAKAWAY_FROM_JOB path. It does not claim that Windows
uses an out-of-process shell broker; the evidence ceiling is the exact
ShellExecuteExW launch path only.

The same frozen in-memory C# helper is used for positive and protected roots. It
calls ShellExecuteExW with verb=open, SEE_MASK_NOCLOSEPROCESS | SEE_MASK_FLAG_NO_UI,
and an exact 30-second system PowerShell child. It obtains the returned process
handle, resolves a PID, closes the handle, and returns the PID through the root
exit code.

Positive validity requires launch success, returned child alive after root exit,
and explicit cleanup. Protected validity requires the exact AppContainer +
immediate Job / zero-capability receipt. If protected ShellExecuteExW launches and
the returned child survives after run_zero_network_process returns and closes the
Forge Job, that is bounded bypass evidence for this launch path. If launch succeeds
but the child is absent after return, that is bounded containment evidence. If the
protected ShellExecuteExW call itself fails after a valid positive control, that is
bounded protected-path denial only; it is not attributed specifically to the Job.


v0.2.6.1 changes no launch or observation behavior from frozen v0.2.6.
It rebinds only to the compatible control pointer-repair generation 3b17cb3... /
CHECKPOINT defeaca5.... Helper source/DLL, ShellExecuteExW flags, positive/protected
commands, PID/liveness supervision, cleanup, classifications, non-network scope and
claim ceiling remain unchanged.

SHELLEXECUTEEX_PATH != PROVEN_OUT_OF_PROCESS_BROKER
PROTECTED_SHELLEXECUTEEX_DENIAL != JOB_SPECIFIC_DENIAL
SHELLEXECUTEEX_CONTAINMENT != ALL_PROCESS_TREE_ESCAPE_RESISTANCE
NON_NETWORK_RESULT != NETWORK_EGRESS_RESULT
"""

import base64
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
EXPECTED_CONTROL_HEAD = "3b17cb3ab64606b98244c979bf8cf4b023323aeb"
EXPECTED_CONTROL_CHECKPOINT = "defeaca590c0d62eb9c32584f1b745dce1c56fcaf0949cad0daf2ba2aaa99f06"
GEN14_CHECKPOINT = "checkpoint-app-live-0014-43aa7feac7e8"
PARENT_ATTEMPT_ID = "attempt-egress-wider-v0-2-6-shellexecuteex-process-lifecycle-first"
ATTEMPT_ID = "attempt-egress-wider-v0-2-6-1-shellexecuteex-process-lifecycle-currentness-first"
HELPER_SOURCE_SHA256 = "312d666b624bd182a4c201090cd5ecd9da5996ab96fbc5df4c799a3b7496e28d"
HELPER_DLL_SHA256 = "8922a45ce1814a86edbed007a6e444f0f42556b3e3e5a67f30b16552c98892b4"
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
ERROR_INVALID_PARAMETER = 87

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "source"
HELPER_SOURCE = PROJECT_ROOT / "state" / "attempt_artifacts" / "EGRESS_WIDER_V0_2_6_SHELLEXECUTEEX_HELPER_LIBRARY_20260909.cs"
HELPER_DLL = PROJECT_ROOT / "state" / "attempt_artifacts" / "EGRESS_WIDER_V0_2_6_SHELLEXECUTEEX_HELPER_LIBRARY_20260909.dll"
sys.path.insert(0, str(SOURCE_ROOT))

from forge_app.egress.windows_protected_process import (  # noqa: E402
    ProtectedProcessError,
    run_zero_network_process,
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
        self.kernel32.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
        self.kernel32.IsProcessInJob.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL

    def observe(self, pid: int) -> dict[str, object]:
        ctypes.set_last_error(0)
        handle = self.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
        if not handle:
            err = ctypes.get_last_error()
            return {"pid": pid, "open": False, "alive": False if err == ERROR_INVALID_PARAMETER else None, "open_error": err, "in_any_job": None}
        try:
            wait = int(self.kernel32.WaitForSingleObject(handle, 0))
            in_job = wintypes.BOOL()
            ctypes.set_last_error(0)
            qok = bool(self.kernel32.IsProcessInJob(handle, None, ctypes.byref(in_job)))
            return {
                "pid": pid,
                "open": True,
                "alive": wait == WAIT_TIMEOUT,
                "wait_result": wait,
                "job_query_ok": qok,
                "in_any_job": bool(in_job.value) if qok else None,
                "job_query_error": 0 if qok else ctypes.get_last_error(),
            }
        finally:
            self.kernel32.CloseHandle(handle)

    def terminate(self, pid: int) -> dict[str, object]:
        ctypes.set_last_error(0)
        handle = self.kernel32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
        if not handle:
            return {"pid": pid, "opened": False, "error": ctypes.get_last_error()}
        try:
            ok = bool(self.kernel32.TerminateProcess(handle, 0xD7))
            wait = int(self.kernel32.WaitForSingleObject(handle, 3000)) if ok else None
            return {"pid": pid, "opened": True, "terminated": ok, "wait_result": wait}
        finally:
            self.kernel32.CloseHandle(handle)


def _git(args: list[str]) -> str:
    result = subprocess.run(["git", "-C", str(SOURCE_ROOT), *args], capture_output=True, text=True, timeout=10, check=False)
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


def _decode(code: int | None) -> dict[str, object]:
    if code is None:
        return {"kind": "NO_EXIT_CODE", "raw": None}
    raw = int(code) & 0xFFFFFFFF
    if 200 < raw < 0x10000000:
        return {"kind": "SHELLEXECUTEEX_SUCCESS", "raw": raw, "pid": raw}
    prefix = raw & 0xFF000000
    if prefix == 0xE3000000:
        return {"kind": "SHELLEXECUTEEX_FAILURE", "raw": raw, "win32_error": raw & 0xFFFF}
    if raw == 0xE4000000:
        return {"kind": "SHELLEXECUTEEX_NO_PROCESS_HANDLE", "raw": raw}
    if prefix == 0xE5000000:
        return {"kind": "SHELLEXECUTEEX_GET_PID_FAILURE", "raw": raw, "win32_error": raw & 0xFFFF}
    if raw == 199:
        return {"kind": "HELPER_LOAD_OR_REFLECTION_FAILURE", "raw": raw}
    return {"kind": "UNKNOWN_EXIT", "raw": raw}


def _root_command(powershell: Path, helper_bytes: bytes) -> list[str]:
    b64 = base64.b64encode(helper_bytes).decode("ascii")
    ps = str(powershell).replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; try { "
        f"$bytes=[Convert]::FromBase64String('{b64}'); "
        "$a=[System.Reflection.Assembly]::Load($bytes); "
        "$t=$a.GetType('ShellExecuteExHelper'); "
        "$m=$t.GetMethod('Run'); "
        f"$r=$m.Invoke($null,@('{ps}')); exit [int]$r "
        "} catch { exit 199 }"
    )
    return [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script]


def _emit(result: dict[str, object], exit_code: int) -> int:
    result["schema"] = "singularity-works.egress-wider-v0.2.6.1-shellexecuteex-process-lifecycle-result/0.1"
    result["attempt_id"] = ATTEMPT_ID
    result["parent_attempt_id"] = PARENT_ATTEMPT_ID
    result["artifact_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["source_head"] = EXPECTED_SOURCE_HEAD
    result["main_head"] = EXPECTED_MAIN_HEAD
    result["gen14_checkpoint"] = GEN14_CHECKPOINT
    result["durable_control_head"] = EXPECTED_CONTROL_HEAD
    result["durable_control_checkpoint"] = EXPECTED_CONTROL_CHECKPOINT
    result["helper_source_sha256"] = HELPER_SOURCE_SHA256
    result["helper_dll_sha256"] = HELPER_DLL_SHA256
    result["authority"] = "NONE_BY_CONTENT"
    result["network_activity_intended"] = False
    result["claim_ceiling"] = "BOUNDED_SHELLEXECUTEEX_PROCESS_LIFECYCLE_ONLY"
    result["runtime_law_earned"] = False
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


def main() -> int:
    started = time.monotonic()
    result: dict[str, object] = {"status": "HARNESS_INVALID", "positive_control": None, "protected": None}
    if os.name != "nt":
        result["reason"] = "Windows-only discriminator"
        return _emit(result, 3)

    try:
        head = _git(["rev-parse", "HEAD"])
        dirty = _git(["status", "--short"])
    except Exception as exc:
        result["reason"] = f"source currentness preflight failed: {type(exc).__name__}: {exc}"
        return _emit(result, 3)
    result["source_preflight"] = {"head": head, "clean": dirty == ""}
    if head != EXPECTED_SOURCE_HEAD or dirty:
        result["reason"] = "source currentness mismatch"
        return _emit(result, 3)

    if not HELPER_SOURCE.is_file() or hashlib.sha256(HELPER_SOURCE.read_bytes()).hexdigest() != HELPER_SOURCE_SHA256:
        result["reason"] = "helper source hash mismatch"
        return _emit(result, 3)
    if not HELPER_DLL.is_file():
        result["reason"] = "helper DLL missing"
        return _emit(result, 3)
    helper_bytes = HELPER_DLL.read_bytes()
    if hashlib.sha256(helper_bytes).hexdigest() != HELPER_DLL_SHA256:
        result["reason"] = "helper DLL hash mismatch"
        return _emit(result, 3)

    try:
        powershell = _powershell()
    except Exception as exc:
        result["reason"] = f"tool preflight failed: {type(exc).__name__}: {exc}"
        return _emit(result, 3)

    root_command = _root_command(powershell, helper_bytes)
    result["root_command_sha256"] = hashlib.sha256(subprocess.list2cmdline(root_command).encode("utf-8")).hexdigest()
    result["root_command_chars"] = len(subprocess.list2cmdline(root_command))
    probe = ProcessProbe()
    positive_child: int | None = None

    try:
        positive = subprocess.run(root_command, cwd=powershell.parent, capture_output=True, text=True, timeout=10, check=False)
        positive_decoded = _decode(positive.returncode)
        result["positive_control"] = {"root_exit_code": positive.returncode, "decoded": positive_decoded, "stderr_nonempty": bool(positive.stderr)}
        if positive_decoded.get("kind") != "SHELLEXECUTEEX_SUCCESS":
            result["reason"] = "positive-control ShellExecuteExW did not return a supervised child PID"
            return _emit(result, 3)
        positive_child = int(positive_decoded["pid"])
        positive_state = probe.observe(positive_child)
        result["positive_control"]["child_state_after_root_exit"] = positive_state
        if positive_state.get("alive") is not True:
            result["reason"] = "positive-control ShellExecuteExW child was not alive after root exit"
            return _emit(result, 3)
        cleanup = probe.terminate(positive_child)
        result["positive_control"]["cleanup"] = cleanup
        positive_child = None
        if cleanup.get("terminated") is not True or cleanup.get("wait_result") != WAIT_OBJECT_0:
            result["reason"] = "positive-control ShellExecuteExW child cleanup failed"
            return _emit(result, 3)

        try:
            receipt = run_zero_network_process(
                root_command,
                timeout_seconds=10.0,
                cwd=powershell.parent,
                profile_name=f"SW.ShellExec.{uuid4().hex[:8]}",
            )
        except ProtectedProcessError as exc:
            result["reason"] = f"protected root lifecycle failed: {type(exc).__name__}: {exc}"
            return _emit(result, 3)

        receipt_dict = receipt.as_dict()
        receipt_dict["executable"] = "<LOCAL_POWERSHELL_PATH>"
        receipt_dict["profile_name"] = "<EPHEMERAL_APPCONTAINER_PROFILE>"
        decoded = _decode(receipt.exit_code)
        result["protected"] = {"receipt": receipt_dict, "decoded": decoded}
        if not (
            receipt.appcontainer_verified
            and receipt.immediate_job_verified
            and receipt.capability_count == 0
            and receipt.inherited_handles is False
            and receipt.timed_out is False
        ):
            result["reason"] = "protected receipt shape invalid"
            return _emit(result, 3)

        kind = decoded.get("kind")
        if kind == "SHELLEXECUTEEX_FAILURE":
            result["status"] = "PASS_BOUNDED_PROTECTED_SHELLEXECUTEEX_DENIED"
            result["reason"] = "positive ShellExecuteExW lifecycle succeeded, while protected ShellExecuteExW returned failure under the verified AppContainer+immediate-Job boundary"
            result["elapsed_seconds"] = round(time.monotonic() - started, 6)
            return _emit(result, 0)

        if kind == "SHELLEXECUTEEX_SUCCESS":
            child_pid = int(decoded["pid"])
            state = probe.observe(child_pid)
            result["protected"]["child_state_after_protected_return"] = state
            if state.get("alive") is True:
                result["protected"]["escape_cleanup"] = probe.terminate(child_pid)
                result["status"] = "FAIL_SHELLEXECUTEEX_CHILD_SURVIVED_FORGE_JOB_CLOSE"
                result["reason"] = "protected ShellExecuteExW returned a child PID that remained alive after run_zero_network_process closed the immediate Forge Job"
                result["elapsed_seconds"] = round(time.monotonic() - started, 6)
                return _emit(result, 2)
            if state.get("alive") is False:
                result["status"] = "PASS_BOUNDED_SHELLEXECUTEEX_CHILD_NOT_ALIVE_AFTER_FORGE_JOB_CLOSE"
                result["reason"] = "protected ShellExecuteExW launched a supervised child PID that was no longer alive after run_zero_network_process closed the immediate Forge Job"
                result["elapsed_seconds"] = round(time.monotonic() - started, 6)
                return _emit(result, 0)
            result["reason"] = "protected ShellExecuteExW child liveness was indeterminate"
            return _emit(result, 3)

        result["reason"] = f"protected ShellExecuteExW returned non-decisive classification: {kind}"
        return _emit(result, 3)
    finally:
        if positive_child is not None:
            probe.terminate(positive_child)


if __name__ == "__main__":
    raise SystemExit(main())
