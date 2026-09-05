from __future__ import annotations

"""Windows protected-process primitive for OS/process egress Attempt 0.

The primitive deliberately proves only a bounded launch boundary:
- zero-capability AppContainer process token;
- immediate Job Object membership;
- no inherited handles;
- suspended fail-closed setup before first instruction executes;
- Job-close process-tree teardown.

It does not integrate existing renderer/session launch sites and does not confer
Connection Gate, network, semantic, or provider authority.
"""

from dataclasses import asdict, dataclass
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Sequence
from uuid import uuid4


PROFILE_PATTERN = re.compile(r"^[A-Za-z0-9._ -]{1,64}$")
PROFILE_PREFIX = "SingularityWorks.EgressAttempt0"

# Process creation / wait.
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
INFINITE = 0xFFFFFFFF
STILL_ACTIVE = 259

# Job Object.
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JobObjectExtendedLimitInformation = 9

# Security / token.
TOKEN_QUERY = 0x0008
TokenIsAppContainer = 29

# PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES =
# ProcThreadAttributeValue(9, FALSE, TRUE, FALSE).
PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES = 0x00020009

ERROR_INSUFFICIENT_BUFFER = 122
ERROR_ALREADY_EXISTS = 183
HRESULT_FROM_WIN32_ERROR_ALREADY_EXISTS = 0x800700B7


class ProtectedProcessError(RuntimeError):
    """Fail-closed protected-process setup or lifecycle failure."""


@dataclass(frozen=True)
class ProtectedProcessReceipt:
    schema: str
    command_sha256: str
    executable: str
    profile_name: str
    profile_created: bool
    pid: int
    parent_was_in_job: bool
    appcontainer_verified: bool
    immediate_job_verified: bool
    capability_count: int
    inherited_handles: bool
    environment_inherited: bool
    timed_out: bool
    job_close_terminated_process: bool
    exit_code: int | None
    elapsed_seconds: float
    authority: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class _STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_ubyte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class _STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [
        ("StartupInfo", _STARTUPINFOW),
        ("lpAttributeList", ctypes.c_void_p),
    ]


class _PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


class _SECURITY_CAPABILITIES(ctypes.Structure):
    _fields_ = [
        ("AppContainerSid", ctypes.c_void_p),
        ("Capabilities", ctypes.c_void_p),
        ("CapabilityCount", wintypes.DWORD),
        ("Reserved", wintypes.DWORD),
    ]


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


def _hex_hresult(value: int) -> int:
    return ctypes.c_ulong(value).value


def _command_identity(command: Sequence[str]) -> str:
    raw = json.dumps(
        [str(x) for x in command],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _default_profile_name() -> str:
    return f"{PROFILE_PREFIX}.{uuid4().hex[:20]}"


def _validate_profile_name(name: str) -> str:
    if not PROFILE_PATTERN.fullmatch(name):
        raise ValueError(
            "AppContainer profile name must be 1-64 characters from [-_. A-Za-z0-9]"
        )
    return name


def _validate_command(command: Sequence[str]) -> tuple[str, ...]:
    if not command:
        raise ValueError("command is required")
    values = tuple(str(x) for x in command)
    executable = Path(values[0])
    if not executable.is_absolute():
        raise ValueError("protected executable path must be absolute")
    if not executable.exists() or not executable.is_file():
        raise ValueError(f"protected executable does not exist: {executable}")
    return values


class _WinApi:
    def __init__(self) -> None:
        if os.name != "nt":
            raise ProtectedProcessError("Windows protected process requires os.name == 'nt'")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        self.userenv = ctypes.WinDLL("userenv", use_last_error=True)
        self._bind()

    def _bind(self) -> None:
        k = self.kernel32
        a = self.advapi32
        u = self.userenv

        k.InitializeProcThreadAttributeList.argtypes = [
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        k.InitializeProcThreadAttributeList.restype = wintypes.BOOL
        k.UpdateProcThreadAttribute.argtypes = [
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        k.UpdateProcThreadAttribute.restype = wintypes.BOOL
        k.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
        k.DeleteProcThreadAttributeList.restype = None

        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        k.SetInformationJobObject.restype = wintypes.BOOL
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.AssignProcessToJobObject.restype = wintypes.BOOL
        k.IsProcessInJob.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.BOOL),
        ]
        k.IsProcessInJob.restype = wintypes.BOOL
        k.GetCurrentProcess.argtypes = []
        k.GetCurrentProcess.restype = wintypes.HANDLE

        k.CreateProcessW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPWSTR,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.BOOL,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.LPCWSTR,
            ctypes.POINTER(_STARTUPINFOW),
            ctypes.POINTER(_PROCESS_INFORMATION),
        ]
        k.CreateProcessW.restype = wintypes.BOOL
        k.ResumeThread.argtypes = [wintypes.HANDLE]
        k.ResumeThread.restype = wintypes.DWORD
        k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.WaitForSingleObject.restype = wintypes.DWORD
        k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k.GetExitCodeProcess.restype = wintypes.BOOL
        k.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        k.TerminateProcess.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL

        a.OpenProcessToken.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.HANDLE),
        ]
        a.OpenProcessToken.restype = wintypes.BOOL
        a.GetTokenInformation.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        a.GetTokenInformation.restype = wintypes.BOOL
        a.FreeSid.argtypes = [ctypes.c_void_p]
        a.FreeSid.restype = ctypes.c_void_p

        u.CreateAppContainerProfile.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        u.CreateAppContainerProfile.restype = ctypes.c_long
        u.DeriveAppContainerSidFromAppContainerName.argtypes = [
            wintypes.LPCWSTR,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        u.DeriveAppContainerSidFromAppContainerName.restype = ctypes.c_long
        u.DeleteAppContainerProfile.argtypes = [wintypes.LPCWSTR]
        u.DeleteAppContainerProfile.restype = ctypes.c_long

    def win_error(self, label: str) -> ProtectedProcessError:
        return ProtectedProcessError(f"{label}: {ctypes.WinError(ctypes.get_last_error())}")

    def close_handle(self, handle: wintypes.HANDLE | None) -> None:
        if handle:
            self.kernel32.CloseHandle(handle)

    def current_process_in_job(self) -> bool:
        value = wintypes.BOOL()
        ok = self.kernel32.IsProcessInJob(
            self.kernel32.GetCurrentProcess(), None, ctypes.byref(value)
        )
        if not ok:
            raise self.win_error("IsProcessInJob(current)")
        return bool(value.value)

    def process_in_job(self, process: wintypes.HANDLE, job: wintypes.HANDLE) -> bool:
        value = wintypes.BOOL()
        ok = self.kernel32.IsProcessInJob(process, job, ctypes.byref(value))
        if not ok:
            raise self.win_error("IsProcessInJob(child)")
        return bool(value.value)

    def process_is_appcontainer(self, process: wintypes.HANDLE) -> bool:
        token = wintypes.HANDLE()
        if not self.advapi32.OpenProcessToken(process, TOKEN_QUERY, ctypes.byref(token)):
            raise self.win_error("OpenProcessToken(child)")
        try:
            value = wintypes.DWORD()
            needed = wintypes.DWORD()
            ok = self.advapi32.GetTokenInformation(
                token,
                TokenIsAppContainer,
                ctypes.byref(value),
                ctypes.sizeof(value),
                ctypes.byref(needed),
            )
            if not ok:
                raise self.win_error("GetTokenInformation(TokenIsAppContainer)")
            return bool(value.value)
        finally:
            self.close_handle(token)


class _AppContainerProfile:
    def __init__(self, api: _WinApi, name: str) -> None:
        self.api = api
        self.name = _validate_profile_name(name)
        self.sid = ctypes.c_void_p()
        self.created = False

    def open(self) -> None:
        hr = self.api.userenv.CreateAppContainerProfile(
            self.name,
            self.name,
            "Singularity Works OS/process egress Attempt 0",
            None,
            0,
            ctypes.byref(self.sid),
        )
        code = _hex_hresult(hr)
        if code == 0:
            self.created = True
            return
        if code != HRESULT_FROM_WIN32_ERROR_ALREADY_EXISTS:
            raise ProtectedProcessError(
                f"CreateAppContainerProfile({self.name}) failed HRESULT=0x{code:08X}"
            )
        hr = self.api.userenv.DeriveAppContainerSidFromAppContainerName(
            self.name, ctypes.byref(self.sid)
        )
        code = _hex_hresult(hr)
        if code != 0:
            raise ProtectedProcessError(
                f"DeriveAppContainerSidFromAppContainerName({self.name}) failed HRESULT=0x{code:08X}"
            )

    def close(self) -> None:
        if self.sid:
            self.api.advapi32.FreeSid(self.sid)
            self.sid = ctypes.c_void_p()
        if self.created:
            hr = self.api.userenv.DeleteAppContainerProfile(self.name)
            code = _hex_hresult(hr)
            if code != 0:
                raise ProtectedProcessError(
                    f"DeleteAppContainerProfile({self.name}) failed HRESULT=0x{code:08X}"
                )
            self.created = False


class _AttributeList:
    def __init__(self, api: _WinApi, appcontainer_sid: ctypes.c_void_p) -> None:
        self.api = api
        self.buffer: ctypes.Array[ctypes.c_char] | None = None
        self.ptr = ctypes.c_void_p()
        self.initialized = False
        self.security_capabilities = _SECURITY_CAPABILITIES(
            AppContainerSid=appcontainer_sid,
            Capabilities=None,
            CapabilityCount=0,
            Reserved=0,
        )

    def open(self) -> None:
        size = ctypes.c_size_t()
        ctypes.set_last_error(0)
        self.api.kernel32.InitializeProcThreadAttributeList(
            None, 1, 0, ctypes.byref(size)
        )
        err = ctypes.get_last_error()
        if err != ERROR_INSUFFICIENT_BUFFER or size.value <= 0:
            raise ProtectedProcessError(
                f"InitializeProcThreadAttributeList(size) unexpected error={err} size={size.value}"
            )
        self.buffer = ctypes.create_string_buffer(size.value)
        self.ptr = ctypes.cast(self.buffer, ctypes.c_void_p)
        if not self.api.kernel32.InitializeProcThreadAttributeList(
            self.ptr, 1, 0, ctypes.byref(size)
        ):
            raise self.api.win_error("InitializeProcThreadAttributeList")
        self.initialized = True
        if not self.api.kernel32.UpdateProcThreadAttribute(
            self.ptr,
            0,
            PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,
            ctypes.byref(self.security_capabilities),
            ctypes.sizeof(self.security_capabilities),
            None,
            None,
        ):
            raise self.api.win_error(
                "UpdateProcThreadAttribute(PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES)"
            )

    def close(self) -> None:
        if self.ptr and self.initialized:
            self.api.kernel32.DeleteProcThreadAttributeList(self.ptr)
        self.initialized = False
        self.ptr = ctypes.c_void_p()
        self.buffer = None


def _create_kill_on_close_job(api: _WinApi) -> wintypes.HANDLE:
    job = api.kernel32.CreateJobObjectW(None, None)
    if not job:
        raise api.win_error("CreateJobObjectW")
    info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not api.kernel32.SetInformationJobObject(
        job,
        JobObjectExtendedLimitInformation,
        ctypes.byref(info),
        ctypes.sizeof(info),
    ):
        api.close_handle(job)
        raise api.win_error("SetInformationJobObject(KILL_ON_JOB_CLOSE)")
    return job


def _get_exit_code(api: _WinApi, process: wintypes.HANDLE) -> int:
    value = wintypes.DWORD()
    if not api.kernel32.GetExitCodeProcess(process, ctypes.byref(value)):
        raise api.win_error("GetExitCodeProcess")
    return int(value.value)


def run_zero_network_process(
    command: Sequence[str],
    *,
    timeout_seconds: float = 10.0,
    cwd: str | Path | None = None,
    profile_name: str | None = None,
    no_window: bool = True,
) -> ProtectedProcessReceipt:
    """Launch one process in a zero-capability AppContainer + immediate Job.

    The child is created suspended and is never resumed unless both AppContainer
    token state and immediate Job membership are observed. The Job handle remains
    open for the execution lifetime and is closed before profile cleanup.
    """

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be > 0")
    values = _validate_command(command)
    executable = str(Path(values[0]).resolve())
    profile_name = _validate_profile_name(profile_name or _default_profile_name())
    if cwd is not None:
        cwd_path = Path(cwd)
        if not cwd_path.is_absolute():
            raise ValueError("cwd must be absolute when provided")
        if not cwd_path.exists() or not cwd_path.is_dir():
            raise ValueError(f"cwd does not exist: {cwd_path}")
        cwd_value: str | None = str(cwd_path)
    else:
        cwd_value = None

    api = _WinApi()
    parent_was_in_job = api.current_process_in_job()
    profile = _AppContainerProfile(api, profile_name)
    attrs: _AttributeList | None = None
    job: wintypes.HANDLE | None = None
    pi = _PROCESS_INFORMATION()
    process_created = False
    started_at = time.monotonic()
    result: ProtectedProcessReceipt | None = None

    try:
        profile.open()
        attrs = _AttributeList(api, profile.sid)
        attrs.open()
        job = _create_kill_on_close_job(api)

        startup = _STARTUPINFOEXW()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.lpAttributeList = attrs.ptr
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(values))
        creation_flags = EXTENDED_STARTUPINFO_PRESENT | CREATE_SUSPENDED
        if no_window:
            creation_flags |= CREATE_NO_WINDOW

        ok = api.kernel32.CreateProcessW(
            executable,
            command_line,
            None,
            None,
            False,
            creation_flags,
            None,
            cwd_value,
            ctypes.cast(ctypes.byref(startup), ctypes.POINTER(_STARTUPINFOW)),
            ctypes.byref(pi),
        )
        if not ok:
            raise api.win_error("CreateProcessW(AppContainer suspended)")
        process_created = True

        appcontainer_verified = api.process_is_appcontainer(pi.hProcess)
        if not appcontainer_verified:
            raise ProtectedProcessError(
                "child token did not report TokenIsAppContainer; refusing to resume"
            )

        if not api.kernel32.AssignProcessToJobObject(job, pi.hProcess):
            raise api.win_error("AssignProcessToJobObject(immediate nested job)")
        immediate_job_verified = api.process_in_job(pi.hProcess, job)
        if not immediate_job_verified:
            raise ProtectedProcessError(
                "child is not observed in immediate Job; refusing to resume"
            )

        previous_suspend_count = api.kernel32.ResumeThread(pi.hThread)
        if previous_suspend_count == 0xFFFFFFFF:
            raise api.win_error("ResumeThread")

        wait_ms = min(int(timeout_seconds * 1000), 0xFFFFFFFE)
        wait_result = api.kernel32.WaitForSingleObject(pi.hProcess, wait_ms)
        timed_out = wait_result == WAIT_TIMEOUT
        if wait_result not in (WAIT_OBJECT_0, WAIT_TIMEOUT):
            raise api.win_error(f"WaitForSingleObject unexpected={wait_result}")

        job_close_terminated = False
        if timed_out:
            # Closing the last immediate Job handle is the kill boundary.
            api.close_handle(job)
            job = None
            post_close = api.kernel32.WaitForSingleObject(pi.hProcess, 2000)
            job_close_terminated = post_close == WAIT_OBJECT_0
            if not job_close_terminated:
                api.kernel32.TerminateProcess(pi.hProcess, 0xE0)
                api.kernel32.WaitForSingleObject(pi.hProcess, 2000)
                raise ProtectedProcessError(
                    "timed-out protected process survived immediate Job close"
                )

        exit_code = _get_exit_code(api, pi.hProcess)
        if exit_code == STILL_ACTIVE:
            exit_value: int | None = None
        else:
            exit_value = exit_code

        result = ProtectedProcessReceipt(
            schema="singularity-protected-process/0.1",
            command_sha256=_command_identity(values),
            executable=executable,
            profile_name=profile_name,
            profile_created=profile.created,
            pid=int(pi.dwProcessId),
            parent_was_in_job=parent_was_in_job,
            appcontainer_verified=appcontainer_verified,
            immediate_job_verified=immediate_job_verified,
            capability_count=0,
            inherited_handles=False,
            environment_inherited=True,
            timed_out=timed_out,
            job_close_terminated_process=job_close_terminated,
            exit_code=exit_value,
            elapsed_seconds=max(0.0, time.monotonic() - started_at),
            authority="NONE",
        )
    except BaseException:
        # Fail closed: if process creation succeeded but setup did not reach a safe
        # resume boundary, kill the suspended/running child before re-raising.
        if process_created and pi.hProcess:
            api.kernel32.TerminateProcess(pi.hProcess, 0xEF)
            api.kernel32.WaitForSingleObject(pi.hProcess, 2000)
        raise
    finally:
        if job:
            api.close_handle(job)
            job = None
        if pi.hThread:
            api.close_handle(pi.hThread)
            pi.hThread = None
        if pi.hProcess:
            api.close_handle(pi.hProcess)
            pi.hProcess = None
        if attrs is not None:
            attrs.close()
        profile.close()

    if result is None:
        raise ProtectedProcessError("protected process completed without receipt")
    return result
