from __future__ import annotations

"""Frozen wider-egress v0.2.7.1: WMI Win32_Process.Create reserved-PID repair.

This is a materially distinct NON-NETWORK, service-mediated process-creation path.
The root PowerShell binds the local WMI Win32_Process class and invokes Create on a
30-second sleeping system PowerShell child. Success returns the child PID through a
high-nibble encoded exit code; WMI bind/invocation/return failures are separately
encoded.

The Python supervisor records child liveness, any-Job membership and Toolhelp parent
PID/executable. A positive launch is valid only if WMI Create succeeds, the child is
alive after root exit, and cleanup succeeds. Parent identity is evidence: a WMI
service host parent (for example WmiPrvSE.exe) can support service-mediated lineage;
it is not assumed in advance.

Protected execution uses the exact zero-capability AppContainer + immediate Forge
Job primitive. A protected WMI bind/invocation failure is bounded denial at that
observed WMI stage only. If WMI Create succeeds, child survival after protected
return/Forge Job close is bounded bypass evidence for this WMI creation path; child
absence is bounded containment evidence.


v0.2.7.1 repairs only the frozen PowerShell local variable used after a successful
WMI Create return: reserved automatic `$PID` becomes non-reserved `$childPid`, and
the success encoder references `$childPid`. Control/lineage/schema bindings update to
the fresh-clone-verified v0.2.7 harness checkpoint. All WMI paths, child command,
failure encodings, Python lineage/liveness/cleanup, protected primitive, non-network
scope and claim ceiling remain unchanged.

WMI_PROCESS_CREATE != ALL_COM_RPC_PROCESS_CREATION
WMI_BIND_DENIAL != JOB_SPECIFIC_DENIAL
WMI_CHILD_PARENT_IDENTITY != GENERAL_SERVICE_BROKER_LAW
NON_NETWORK_RESULT != NETWORK_EGRESS_RESULT
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
EXPECTED_CONTROL_HEAD = "8da21c41eac3cc2153970341b2259f4148bf6845"
EXPECTED_CONTROL_CHECKPOINT = "0753ee643f38a2f911e1a5fe315be811d1c62d7f979a54bb3b59589f2c9c9456"
GEN14_CHECKPOINT = "checkpoint-app-live-0014-43aa7feac7e8"
PARENT_ATTEMPT_ID = "attempt-egress-wider-v0-2-7-wmi-harness-invalid-diagnosis"
ATTEMPT_ID = "attempt-egress-wider-v0-2-7-1-wmi-win32-process-create-pid-repair-first"
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
ERROR_INVALID_PARAMETER = 87
TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "source"
sys.path.insert(0, str(SOURCE_ROOT))

from forge_app.egress.windows_protected_process import (  # noqa: E402
    ProtectedProcessError,
    run_zero_network_process,
)


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
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
        self.kernel32.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
        self.kernel32.IsProcessInJob.restype = wintypes.BOOL
        self.kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self.kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        self.kernel32.Process32FirstW.restype = wintypes.BOOL
        self.kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        self.kernel32.Process32NextW.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL

    def lineage(self, pid: int) -> dict[str, object]:
        ctypes.set_last_error(0)
        snap = self.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if not snap or snap == INVALID_HANDLE_VALUE:
            return {"snapshot_ok": False, "error": ctypes.get_last_error(), "pid": pid}
        entries: dict[int, tuple[int, str]] = {}
        try:
            pe = PROCESSENTRY32W()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            ok = bool(self.kernel32.Process32FirstW(snap, ctypes.byref(pe)))
            while ok:
                entries[int(pe.th32ProcessID)] = (int(pe.th32ParentProcessID), str(pe.szExeFile))
                ok = bool(self.kernel32.Process32NextW(snap, ctypes.byref(pe)))
        finally:
            self.kernel32.CloseHandle(snap)
        row = entries.get(pid)
        if row is None:
            return {"snapshot_ok": True, "pid": pid, "present": False, "parent_pid": None, "parent_exe": None, "exe": None}
        ppid, exe = row
        parent = entries.get(ppid)
        return {"snapshot_ok": True, "pid": pid, "present": True, "exe": exe, "parent_pid": ppid, "parent_exe": parent[1] if parent else None}

    def observe(self, pid: int) -> dict[str, object]:
        lineage = self.lineage(pid)
        ctypes.set_last_error(0)
        handle = self.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
        if not handle:
            err = ctypes.get_last_error()
            return {"pid": pid, "open": False, "alive": False if err == ERROR_INVALID_PARAMETER else None, "open_error": err, "in_any_job": None, "lineage": lineage}
        try:
            wait = int(self.kernel32.WaitForSingleObject(handle, 0))
            in_job = wintypes.BOOL()
            ctypes.set_last_error(0)
            qok = bool(self.kernel32.IsProcessInJob(handle, None, ctypes.byref(in_job)))
            return {"pid": pid, "open": True, "alive": wait == WAIT_TIMEOUT, "wait_result": wait, "job_query_ok": qok, "in_any_job": bool(in_job.value) if qok else None, "job_query_error": 0 if qok else ctypes.get_last_error(), "lineage": lineage}
        finally:
            self.kernel32.CloseHandle(handle)

    def terminate(self, pid: int) -> dict[str, object]:
        ctypes.set_last_error(0)
        handle = self.kernel32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
        if not handle:
            return {"pid": pid, "opened": False, "error": ctypes.get_last_error()}
        try:
            ok = bool(self.kernel32.TerminateProcess(handle, 0xD8))
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


def _root_command(powershell: Path) -> list[str]:
    ps = str(powershell).replace("'", "''")
    child = f'"{str(powershell)}" -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -Command "Start-Sleep -Seconds 30"'.replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; "
        "try { $c=[wmiclass]'\\\\.\\root\\cimv2:Win32_Process' } "
        "catch { $h=[uint32]$_.Exception.HResult; exit [int](0x20000000 -bor ($h -band 0xFFFF)) }; "
        f"$cmd='{child}'; "
        "try { $r=$c.Create($cmd) } "
        "catch { $h=[uint32]$_.Exception.HResult; exit [int](0x30000000 -bor ($h -band 0xFFFF)) }; "
        "if($null -eq $r){ exit [int]0x50000000 }; "
        "$rv=[uint32]$r.ReturnValue; if($rv -ne 0){ exit [int](0x40000000 -bor ($rv -band 0xFFFF)) }; "
        "$childPid=[uint32]$r.ProcessId; if($childPid -eq 0){ exit [int]0x50000001 }; "
        "exit [int](0x10000000 -bor ($childPid -band 0x0FFFFFFF))"
    )
    return [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script]


def _decode(code: int | None) -> dict[str, object]:
    if code is None:
        return {"kind": "NO_EXIT_CODE", "raw": None}
    raw = int(code) & 0xFFFFFFFF
    prefix = raw & 0xF0000000
    if prefix == 0x10000000:
        return {"kind": "WMI_CREATE_SUCCESS", "raw": raw, "pid": raw & 0x0FFFFFFF}
    if prefix == 0x20000000:
        return {"kind": "WMI_CLASS_BIND_FAILURE", "raw": raw, "hresult_low16": raw & 0xFFFF}
    if prefix == 0x30000000:
        return {"kind": "WMI_CREATE_INVOCATION_EXCEPTION", "raw": raw, "hresult_low16": raw & 0xFFFF}
    if prefix == 0x40000000:
        return {"kind": "WMI_CREATE_RETURN_FAILURE", "raw": raw, "wmi_return_value": raw & 0xFFFF}
    if raw == 0x50000000:
        return {"kind": "WMI_CREATE_NULL_RESULT", "raw": raw}
    if raw == 0x50000001:
        return {"kind": "WMI_CREATE_ZERO_PID", "raw": raw}
    return {"kind": "UNKNOWN_EXIT", "raw": raw}


def _emit(result: dict[str, object], exit_code: int) -> int:
    result["schema"] = "singularity-works.egress-wider-v0.2.7.1-wmi-win32-process-create-result/0.1"
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
    result["claim_ceiling"] = "BOUNDED_WMI_WIN32_PROCESS_CREATE_LIFECYCLE_ONLY"
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
    try:
        powershell = _powershell()
    except Exception as exc:
        result["reason"] = f"tool preflight failed: {type(exc).__name__}: {exc}"
        return _emit(result, 3)

    root_command = _root_command(powershell)
    result["root_command_sha256"] = hashlib.sha256(subprocess.list2cmdline(root_command).encode("utf-8")).hexdigest()
    result["root_command_chars"] = len(subprocess.list2cmdline(root_command))
    probe = ProcessProbe()
    positive_child: int | None = None

    try:
        positive = subprocess.run(root_command, cwd=powershell.parent, capture_output=True, text=True, timeout=10, check=False)
        pdec = _decode(positive.returncode)
        result["positive_control"] = {"root_exit_code": positive.returncode, "decoded": pdec, "stderr_nonempty": bool(positive.stderr)}
        if pdec.get("kind") != "WMI_CREATE_SUCCESS":
            result["reason"] = "positive-control WMI Win32_Process.Create did not return a child PID"
            return _emit(result, 3)
        positive_child = int(pdec["pid"])
        pstate = probe.observe(positive_child)
        result["positive_control"]["child_state_after_root_exit"] = pstate
        if pstate.get("alive") is not True:
            result["reason"] = "positive-control WMI child was not alive after root exit"
            return _emit(result, 3)
        cleanup = probe.terminate(positive_child)
        result["positive_control"]["cleanup"] = cleanup
        positive_child = None
        if cleanup.get("terminated") is not True or cleanup.get("wait_result") != WAIT_OBJECT_0:
            result["reason"] = "positive-control WMI child cleanup failed"
            return _emit(result, 3)

        try:
            receipt = run_zero_network_process(root_command, timeout_seconds=10.0, cwd=powershell.parent, profile_name=f"SW.WMI.{uuid4().hex[:8]}")
        except ProtectedProcessError as exc:
            result["reason"] = f"protected root lifecycle failed: {type(exc).__name__}: {exc}"
            return _emit(result, 3)
        rd = receipt.as_dict()
        rd["executable"] = "<LOCAL_POWERSHELL_PATH>"
        rd["profile_name"] = "<EPHEMERAL_APPCONTAINER_PROFILE>"
        dec = _decode(receipt.exit_code)
        result["protected"] = {"receipt": rd, "decoded": dec}
        if not (receipt.appcontainer_verified and receipt.immediate_job_verified and receipt.capability_count == 0 and receipt.inherited_handles is False and receipt.timed_out is False):
            result["reason"] = "protected receipt shape invalid"
            return _emit(result, 3)

        kind = dec.get("kind")
        if kind in {"WMI_CLASS_BIND_FAILURE", "WMI_CREATE_INVOCATION_EXCEPTION", "WMI_CREATE_RETURN_FAILURE", "WMI_CREATE_NULL_RESULT", "WMI_CREATE_ZERO_PID"}:
            result["status"] = "PASS_BOUNDED_PROTECTED_WMI_PROCESS_CREATE_PATH_DENIED"
            result["reason"] = f"positive WMI process creation succeeded, while protected path stopped at {kind} under the verified AppContainer+immediate-Job boundary"
            result["elapsed_seconds"] = round(time.monotonic() - started, 6)
            return _emit(result, 0)

        if kind == "WMI_CREATE_SUCCESS":
            child_pid = int(dec["pid"])
            state = probe.observe(child_pid)
            result["protected"]["child_state_after_protected_return"] = state
            if state.get("alive") is True:
                result["protected"]["escape_cleanup"] = probe.terminate(child_pid)
                result["status"] = "FAIL_WMI_CREATED_CHILD_SURVIVED_FORGE_JOB_CLOSE"
                result["reason"] = "protected WMI Win32_Process.Create returned a child PID that remained alive after run_zero_network_process closed the immediate Forge Job"
                result["elapsed_seconds"] = round(time.monotonic() - started, 6)
                return _emit(result, 2)
            if state.get("alive") is False:
                result["status"] = "PASS_BOUNDED_WMI_CREATED_CHILD_NOT_ALIVE_AFTER_FORGE_JOB_CLOSE"
                result["reason"] = "protected WMI Win32_Process.Create returned a child PID that was no longer alive after run_zero_network_process closed the immediate Forge Job"
                result["elapsed_seconds"] = round(time.monotonic() - started, 6)
                return _emit(result, 0)
            result["reason"] = "protected WMI child liveness indeterminate"
            return _emit(result, 3)

        result["reason"] = f"protected WMI path returned non-decisive classification: {kind}"
        return _emit(result, 3)
    finally:
        if positive_child is not None:
            probe.terminate(positive_child)


if __name__ == "__main__":
    raise SystemExit(main())
