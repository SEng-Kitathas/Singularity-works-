from __future__ import annotations

"""Frozen wider-egress v0.2.5.2: explicit CREATE_BREAKAWAY_FROM_JOB runSync-currentness sibling.

This is deliberately NON-NETWORK pressure. It tests one exact process-tree escape
mechanism after v0.2.4.1 qualified normal-descendant kill-on-close behavior.

A frozen C# helper DLL is loaded from exact Base64 bytes into the same system
PowerShell root for both phases. Inside that root, the helper:
1. observes whether its current process is in any Job;
2. proves same-child normal CreateProcessW works and cleans that baseline child;
3. attempts the same child with CREATE_BREAKAWAY_FROM_JOB added;
4. encodes root Job membership plus success/failure/Win32 error into the root exit code.

The project execution host is itself in an outer Job. The Attempt therefore
requires that outer Job to expose SILENT_BREAKAWAY_OK, and the positive-control
helper must report that it is NOT in a Job. This prevents the executor Job from
being mistaken for the Forge immediate Job.

Protected PASS is valid only when:
- AppContainer + immediate Job / zero-capability receipt verifies;
- helper reports it IS in a Job;
- normal child baseline inside the helper succeeded and was cleaned up;
- CREATE_BREAKAWAY_FROM_JOB creation failed with ERROR_ACCESS_DENIED (5).

If explicit breakaway creation succeeds and the returned sleeping child remains
alive after run_zero_network_process returns, the Attempt is FAIL_BYPASS_FOUND.

EXPLICIT_BREAKAWAY_CREATE_DENIAL != SERVICE_WMI_COM_ESCAPE_RESISTANCE
EXPLICIT_BREAKAWAY_CREATE_DENIAL != SILENT_BREAKAWAY_CONFIGURATION_PROOF
NON_NETWORK_BREAKAWAY_RESULT != NETWORK_EGRESS_RESULT
BOUNDED_BREAKAWAY_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT

v0.2.5.2 changes no discriminator behavior from immutable preserved v0.2.5/v0.2.5.1.
It binds verified control 56fb5b70... / CHECKPOINT 2a4ce4ba... and the directly
remeasured synchronous runSync plane record f32909d4... after v0.2.5.1 became
immutable HARNESS_INVALID on the async-worker plane. Helper source/DLL hashes,
positive/protected commands, outer-Job gate, decoding, cleanup, PASS/FAIL criteria,
network scope and claim ceiling remain unchanged.
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
EXPECTED_CONTROL_HEAD = "56fb5b70ffee7c58d60c34118338d12c30313e46"
EXPECTED_CONTROL_CHECKPOINT = "2a4ce4baf905bd3698d228cbb9a0575dcc78efa577593a69de6118b9fa49cec6"
GEN14_CHECKPOINT = "checkpoint-app-live-0014-43aa7feac7e8"
PARENT_ATTEMPT_ID = "attempt-egress-wider-v0-2-5-2-synchronous-execution-plane-currentness-post-56fb5b70"
ATTEMPT_ID = "attempt-egress-wider-v0-2-5-2-explicit-job-breakaway-runsync-currentness-first"
HELPER_SOURCE_SHA256 = "77927e4fcf9c874428d78415cda05f52998e59e2133af1d41126348cc8fa7a34"
HELPER_DLL_SHA256 = "8019c83a601e76be23a8762f61ed1f557f940dc11f9328893a785c6b42b8903a"
ERROR_ACCESS_DENIED = 5
JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK = 0x00001000
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
ERROR_INVALID_PARAMETER = 87

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "source"
HELPER_SOURCE = PROJECT_ROOT / "state" / "attempt_artifacts" / "EGRESS_WIDER_V0_2_5_EXPLICIT_BREAKAWAY_HELPER_LIBRARY_20260908.cs"
HELPER_DLL = PROJECT_ROOT / "state" / "attempt_artifacts" / "EGRESS_WIDER_V0_2_5_EXPLICIT_BREAKAWAY_HELPER_LIBRARY_20260908.dll"
sys.path.insert(0, str(SOURCE_ROOT))

from forge_app.egress.windows_protected_process import (  # noqa: E402
    ProtectedProcessError,
    run_zero_network_process,
)


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


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
        handle = self.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
        if not handle:
            err = ctypes.get_last_error()
            return {"pid": pid, "open": False, "alive": False if err == ERROR_INVALID_PARAMETER else None, "open_error": err}
        try:
            wait = int(self.kernel32.WaitForSingleObject(handle, 0))
            return {"pid": pid, "open": True, "alive": wait == WAIT_TIMEOUT, "wait_result": wait}
        finally:
            self.kernel32.CloseHandle(handle)

    def terminate(self, pid: int) -> dict[str, object]:
        ctypes.set_last_error(0)
        handle = self.kernel32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
        if not handle:
            return {"pid": pid, "opened": False, "error": ctypes.get_last_error()}
        try:
            ok = bool(self.kernel32.TerminateProcess(handle, 0xD6))
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


def _outer_job_limits() -> dict[str, object]:
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    k.QueryInformationJobObject.restype = wintypes.BOOL
    info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    returned = wintypes.DWORD()
    ctypes.set_last_error(0)
    ok = k.QueryInformationJobObject(None, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, ctypes.byref(info), ctypes.sizeof(info), ctypes.byref(returned))
    if not ok:
        return {"ok": False, "error": ctypes.get_last_error()}
    flags = int(info.BasicLimitInformation.LimitFlags)
    return {
        "ok": True,
        "limit_flags": flags,
        "breakaway_ok": bool(flags & JOB_OBJECT_LIMIT_BREAKAWAY_OK),
        "silent_breakaway_ok": bool(flags & JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK),
        "kill_on_close": bool(flags & JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE),
    }


def _decode(code: int | None) -> dict[str, object]:
    if code is None:
        return {"kind": "NO_EXIT_CODE", "raw": None}
    raw = int(code) & 0xFFFFFFFF
    prefix = raw & 0xFF000000
    low = raw & 0x0000FFFF
    if raw > 200 and raw < 0x10000000:
        return {"kind": "BREAKAWAY_CREATE_SUCCESS_NOT_IN_JOB", "raw": raw, "pid": raw}
    if prefix == 0xA0000000:
        return {"kind": "BREAKAWAY_CREATE_SUCCESS_IN_JOB", "raw": raw, "pid": raw & 0x0FFFFFFF}
    mapping = {
        0xB1000000: "BASELINE_CLEANUP_FAILURE_NOT_IN_JOB",
        0xB2000000: "BASELINE_CLEANUP_FAILURE_IN_JOB",
        0xC0000000: "JOB_MEMBERSHIP_QUERY_FAILURE",
        0xD1000000: "BASELINE_CREATE_FAILURE_NOT_IN_JOB",
        0xD2000000: "BASELINE_CREATE_FAILURE_IN_JOB",
        0xE1000000: "BREAKAWAY_CREATE_FAILURE_NOT_IN_JOB",
        0xE2000000: "BREAKAWAY_CREATE_FAILURE_IN_JOB",
    }
    return {"kind": mapping.get(prefix, "UNKNOWN_EXIT"), "raw": raw, "win32_error": low}


def _root_command(powershell: Path, helper_bytes: bytes) -> list[str]:
    b64 = base64.b64encode(helper_bytes).decode("ascii")
    ps = str(powershell).replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; try { "
        f"$bytes=[Convert]::FromBase64String('{b64}'); "
        "$a=[System.Reflection.Assembly]::Load($bytes); "
        "$t=$a.GetType('ExplicitBreakawayHelper'); "
        "$m=$t.GetMethod('Run'); "
        f"$r=$m.Invoke($null,@('{ps}')); exit [int]$r "
        "} catch { exit 199 }"
    )
    return [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script]


def _emit(result: dict[str, object], exit_code: int) -> int:
    result["schema"] = "singularity-works.egress-wider-v0.2.5.2-explicit-job-breakaway-result/0.1"
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
    result["claim_ceiling"] = "BOUNDED_EXPLICIT_CREATE_BREAKAWAY_FROM_JOB_ONLY"
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

    outer = _outer_job_limits()
    result["outer_execution_job"] = outer
    if outer.get("ok") is not True or outer.get("silent_breakaway_ok") is not True:
        result["reason"] = "execution host outer Job does not provide SILENT_BREAKAWAY_OK positive-control isolation"
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
        if positive_decoded.get("kind") != "BREAKAWAY_CREATE_SUCCESS_NOT_IN_JOB":
            result["reason"] = "positive-control helper did not prove explicit breakaway creation outside any Job"
            return _emit(result, 3)
        positive_child = int(positive_decoded["pid"])
        positive_state = probe.state(positive_child)
        result["positive_control"]["child_state_after_root_exit"] = positive_state
        if positive_state.get("alive") is not True:
            result["reason"] = "positive-control breakaway child was not alive after root exit"
            return _emit(result, 3)
        cleanup = probe.terminate(positive_child)
        result["positive_control"]["cleanup"] = cleanup
        positive_child = None
        if cleanup.get("terminated") is not True or cleanup.get("wait_result") != WAIT_OBJECT_0:
            result["reason"] = "positive-control breakaway child cleanup failed"
            return _emit(result, 3)

        try:
            receipt = run_zero_network_process(
                root_command,
                timeout_seconds=10.0,
                cwd=powershell.parent,
                profile_name=f"SW.Breakaway.{uuid4().hex[:8]}",
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
        if kind == "BREAKAWAY_CREATE_FAILURE_IN_JOB":
            if decoded.get("win32_error") != ERROR_ACCESS_DENIED:
                result["reason"] = "explicit breakaway creation failed in Job, but not with ERROR_ACCESS_DENIED"
                return _emit(result, 3)
            result["status"] = "PASS_BOUNDED_EXPLICIT_CREATE_BREAKAWAY_FROM_JOB_DENIED"
            result["reason"] = (
                "same in-memory helper proved normal child creation/cleanup inside the protected root, then explicit "
                "CREATE_BREAKAWAY_FROM_JOB creation failed with ERROR_ACCESS_DENIED while the root was verified in the immediate Job"
            )
            result["elapsed_seconds"] = round(time.monotonic() - started, 6)
            return _emit(result, 0)

        if kind == "BREAKAWAY_CREATE_SUCCESS_IN_JOB":
            child_pid = int(decoded["pid"])
            state = probe.state(child_pid)
            result["protected"]["breakaway_child_state_after_return"] = state
            if state.get("alive") is True:
                result["protected"]["escape_cleanup"] = probe.terminate(child_pid)
                result["status"] = "FAIL_EXPLICIT_BREAKAWAY_SURVIVED"
                result["reason"] = "explicit CREATE_BREAKAWAY_FROM_JOB succeeded from the protected root and the sleeping child survived immediate Job close"
                result["elapsed_seconds"] = round(time.monotonic() - started, 6)
                return _emit(result, 2)
            result["reason"] = "explicit breakaway creation reported success in Job, but child was not alive after return"
            return _emit(result, 3)

        result["reason"] = f"protected helper returned non-decisive classification: {kind}"
        return _emit(result, 3)
    finally:
        if positive_child is not None:
            probe.terminate(positive_child)


if __name__ == "__main__":
    raise SystemExit(main())
