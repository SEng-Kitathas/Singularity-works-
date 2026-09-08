from __future__ import annotations

"""Frozen wider-egress v0.2.3: descendant proxy/environment loopback indirection.

This discriminator tests a materially distinct residual seam: the protected root
receipt reports environment inheritance. The exact same PowerShell root launches
a descendant curl command with NO explicit proxy argument. Parent process
environment variables select a parent-owned HTTP proxy on loopback; the target is
a second parent-owned loopback HTTP listener.

Positive control is valid only when descendant curl reaches the proxy listener
and does not reach the direct target listener. The protected phase is valid only
when the root confirms the unique environment marker and ALL_PROXY value before
Process.Start, the AppContainer+Job receipt verifies, and no harness sentinel is
returned.

All endpoints are 127.0.0.1. No DNS lookup, Internet endpoint, provider call,
system proxy mutation, registry mutation, hosts-file mutation, OAuth credential,
or machine-wide firewall change is used.

PROXY_ENV_LOOPBACK_NONDELIVERY != GENERAL_PROXY_DENIAL
PROXY_ENV_LOOPBACK_NONDELIVERY != INTERNET_EGRESS_DENIAL
ENVIRONMENT_INHERITED != ENVIRONMENT_MEDIATED_BYPASS
LOCAL_PROXY_RESULT != SYSTEM_PROXY_CONFIGURATION_RESULT
WIDER_ATTEMPT_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
from uuid import uuid4

EXPECTED_SOURCE_HEAD = "43aa7feac7e8a15828116bd700b644560714496d"
EXPECTED_MAIN_HEAD = "e66c071fc25f8d08bfc7ebf0551948392d652f35"
EXPECTED_CONTROL_HEAD = "f59a32946cea1af64e427a4d9db64a7075f691dd"
EXPECTED_CONTROL_CHECKPOINT = "64f1804e9d6ec64b1638cacbf25bd8963ad967958a1f2847e4d3a352c887a589"
GEN14_CHECKPOINT = "checkpoint-app-live-0014-43aa7feac7e8"
PARENT_ATTEMPT_ID = "attempt-egress-wider-v0-2-2-descendant-dns-helper-loopback-bounded-admission"
ATTEMPT_ID = "attempt-egress-wider-v0-2-3-descendant-proxy-env-loopback-first"
ENV_MARKER = "SW_PROXY_ENV_V023_EXACT"
ENV_MISSING_EXIT = 192
ROOT_PROCESS_START_ERROR_EXIT = 191
CURL_CONNECT_FAILURE_EXITS = {7, 28}

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


def _curl() -> Path:
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    for candidate in [system_root / "System32" / "curl.exe", system_root / "Sysnative" / "curl.exe"]:
        if candidate.is_file():
            return candidate.resolve()
    found = shutil.which("curl.exe") or shutil.which("curl")
    if not found:
        raise RuntimeError("curl unavailable")
    return Path(found).resolve()


class HttpSink:
    def __init__(self, sock: socket.socket, label: str) -> None:
        self.sock = sock
        self.label = label
        self.stop = threading.Event()
        self.thread: threading.Thread | None = None
        self.lock = threading.Lock()
        self.observations: list[dict[str, object]] = []
        self.errors: list[str] = []

    def start(self) -> None:
        self.sock.listen(8)
        self.sock.settimeout(0.2)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        while not self.stop.is_set():
            try:
                conn, addr = self.sock.accept()
            except socket.timeout:
                continue
            except OSError as exc:
                if not self.stop.is_set():
                    self.errors.append(f"accept:{type(exc).__name__}:{exc}")
                return
            with conn:
                conn.settimeout(1.0)
                data = b""
                try:
                    while len(data) < 8192 and b"\r\n\r\n" not in data:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                except (socket.timeout, OSError) as exc:
                    self.errors.append(f"recv:{type(exc).__name__}:{exc}")
                response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK"
                try:
                    conn.sendall(response)
                except OSError as exc:
                    self.errors.append(f"send:{type(exc).__name__}:{exc}")
                first_line = data.split(b"\r\n", 1)[0].decode("latin-1", errors="replace") if data else ""
                obs = {
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "peer": [str(addr[0]), int(addr[1])],
                    "first_line": first_line,
                }
                with self.lock:
                    self.observations.append(obs)

    def snapshot(self) -> dict[str, object]:
        time.sleep(0.4)
        with self.lock:
            return {
                "label": self.label,
                "connection_count": len(self.observations),
                "observations": list(self.observations),
                "errors": list(self.errors),
            }

    def clear(self) -> None:
        with self.lock:
            self.observations.clear()
            self.errors.clear()

    def close(self) -> None:
        self.stop.set()
        try:
            self.sock.close()
        except OSError:
            pass
        if self.thread is not None:
            self.thread.join(timeout=1.0)


def _root_process_start_script(curl: Path, child_arguments: str, proxy_url: str) -> str:
    curl_text = str(curl).replace("'", "''")
    arg_text = child_arguments.replace("'", "''")
    proxy_text = proxy_url.replace("'", "''")
    marker_text = ENV_MARKER.replace("'", "''")
    return (
        "$ErrorActionPreference='Stop'; "
        f"if($env:SW_PROXY_ENV_MARKER -ne '{marker_text}'){{exit {ENV_MISSING_EXIT}}}; "
        f"if($env:ALL_PROXY -ne '{proxy_text}'){{exit {ENV_MISSING_EXIT}}}; "
        "try { "
        "$psi=New-Object System.Diagnostics.ProcessStartInfo; "
        f"$psi.FileName='{curl_text}'; "
        f"$psi.Arguments='{arg_text}'; "
        "$psi.UseShellExecute=$false; "
        "$p=[System.Diagnostics.Process]::Start($psi); "
        f"if($null -eq $p){{exit {ROOT_PROCESS_START_ERROR_EXIT}}}; "
        "$p.WaitForExit(); exit $p.ExitCode "
        f"}} catch {{ exit {ROOT_PROCESS_START_ERROR_EXIT} }}"
    )


def _emit(result: dict[str, object], exit_code: int) -> int:
    result["schema"] = "singularity-works.egress-wider-v0.2.3-descendant-proxy-env-loopback-result/0.1"
    result["attempt_id"] = ATTEMPT_ID
    result["parent_attempt_id"] = PARENT_ATTEMPT_ID
    result["source_head"] = EXPECTED_SOURCE_HEAD
    result["main_head"] = EXPECTED_MAIN_HEAD
    result["gen14_checkpoint"] = GEN14_CHECKPOINT
    result["durable_control_head"] = EXPECTED_CONTROL_HEAD
    result["durable_control_checkpoint"] = EXPECTED_CONTROL_CHECKPOINT
    result["artifact_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["authority"] = "NONE_BY_CONTENT"
    result["claim_ceiling"] = "BOUNDED_DESCENDANT_PROXY_ENV_LOOPBACK_ONLY"
    result["runtime_law_earned"] = False
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


def main() -> int:
    result: dict[str, object] = {
        "status": "HARNESS_INVALID",
        "positive_control": None,
        "protected": None,
        "network_scope": "PARENT_OWNED_LOOPBACK_PROXY_AND_TARGET_ONLY",
    }
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
        result["reason"] = "source currentness mismatch; execution refused"
        return _emit(result, 3)

    try:
        powershell = _powershell()
        curl = _curl()
    except Exception as exc:
        result["reason"] = f"tool preflight failed: {type(exc).__name__}: {exc}"
        return _emit(result, 3)

    proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    target_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_sock.bind(("127.0.0.1", 0))
    target_sock.bind(("127.0.0.1", 0))
    proxy_port = int(proxy_sock.getsockname()[1])
    target_port = int(target_sock.getsockname()[1])
    proxy_url = f"http://127.0.0.1:{proxy_port}"
    target_url = f"http://127.0.0.1:{target_port}/proxy-env-v023"
    result["proxy"] = {"host": "127.0.0.1", "port": proxy_port}
    result["target"] = {"host": "127.0.0.1", "port": target_port}

    proxy_sink = HttpSink(proxy_sock, "proxy")
    target_sink = HttpSink(target_sock, "target")
    proxy_sink.start()
    target_sink.start()

    child_arguments = f"--max-time 3 --silent --show-error --output NUL {target_url}"
    root_script = _root_process_start_script(curl, child_arguments, proxy_url)
    root_command = [
        str(powershell),
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        root_script,
    ]
    result["child_arguments_sha256"] = hashlib.sha256(child_arguments.encode("utf-8")).hexdigest()
    result["root_command_sha256"] = hashlib.sha256(subprocess.list2cmdline(root_command).encode("utf-8")).hexdigest()

    managed_keys = ["SW_PROXY_ENV_MARKER", "ALL_PROXY", "all_proxy", "http_proxy", "HTTP_PROXY", "NO_PROXY", "no_proxy"]
    old_env = {key: os.environ.get(key) for key in managed_keys}
    try:
        os.environ["SW_PROXY_ENV_MARKER"] = ENV_MARKER
        os.environ["ALL_PROXY"] = proxy_url
        os.environ["all_proxy"] = proxy_url
        os.environ["http_proxy"] = proxy_url
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["NO_PROXY"] = ""
        os.environ["no_proxy"] = ""

        positive = subprocess.run(
            root_command,
            cwd=powershell.parent,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        positive_proxy = proxy_sink.snapshot()
        positive_target = target_sink.snapshot()
        result["positive_control"] = {
            "root_exit_code": positive.returncode,
            "proxy": positive_proxy,
            "target": positive_target,
            "stderr_nonempty": bool(positive.stderr),
        }
        if positive.returncode != 0:
            result["reason"] = f"unprotected proxy-env positive control returned {positive.returncode}"
            return _emit(result, 3)
        if positive_proxy["connection_count"] < 1:
            result["reason"] = "unprotected curl did not use environment-selected proxy"
            return _emit(result, 3)
        if positive_target["connection_count"] != 0:
            result["reason"] = "unprotected curl reached direct target instead of proxy-only path"
            return _emit(result, 3)
        if positive_proxy["errors"] or positive_target["errors"]:
            result["reason"] = "positive-control listener error"
            return _emit(result, 3)

        proxy_sink.clear()
        target_sink.clear()

        try:
            receipt = run_zero_network_process(
                root_command,
                timeout_seconds=10.0,
                cwd=powershell.parent,
                profile_name=f"SW.ProxyEnv.{uuid4().hex[:8]}",
            )
        except ProtectedProcessError as exc:
            result["reason"] = f"protected-process lifecycle failed: {type(exc).__name__}: {exc}"
            return _emit(result, 3)

        protected_proxy = proxy_sink.snapshot()
        protected_target = target_sink.snapshot()
        receipt_dict = receipt.as_dict()
        receipt_dict["executable"] = "<LOCAL_POWERSHELL_PATH>"
        receipt_dict["profile_name"] = "<EPHEMERAL_APPCONTAINER_PROFILE>"
        result["protected"] = {
            "receipt": receipt_dict,
            "proxy": protected_proxy,
            "target": protected_target,
        }

        shape_ok = (
            receipt.appcontainer_verified
            and receipt.immediate_job_verified
            and receipt.capability_count == 0
            and receipt.inherited_handles is False
            and receipt.timed_out is False
        )
        if not shape_ok:
            result["reason"] = "protected receipt shape invalid"
            return _emit(result, 3)
        if receipt.exit_code == ENV_MISSING_EXIT:
            result["reason"] = "protected root did not inherit exact proxy environment marker/value"
            return _emit(result, 3)
        if receipt.exit_code == ROOT_PROCESS_START_ERROR_EXIT:
            result["reason"] = "protected descendant Process.Start failed"
            return _emit(result, 3)
        if protected_proxy["errors"] or protected_target["errors"]:
            result["reason"] = "protected listener error"
            return _emit(result, 3)
        if protected_proxy["connection_count"] > 0 or protected_target["connection_count"] > 0:
            result["status"] = "FAIL_BYPASS_FOUND"
            result["reason"] = "protected descendant reached parent-owned proxy or direct target listener"
            return _emit(result, 2)
        if receipt.exit_code not in CURL_CONNECT_FAILURE_EXITS:
            result["reason"] = f"protected descendant returned unclassified curl exit {receipt.exit_code}"
            return _emit(result, 3)

        result["status"] = "PASS_BOUNDED_DESCENDANT_PROXY_ENV_LOOPBACK_DENIAL"
        result["reason"] = (
            "unprotected descendant used inherited environment-selected proxy and reached the parent proxy listener; "
            "protected root inherited the exact marker/proxy value, launched the same descendant, and neither proxy nor direct target received a connection"
        )
        return _emit(result, 0)
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        proxy_sink.close()
        target_sink.close()


if __name__ == "__main__":
    raise SystemExit(main())
