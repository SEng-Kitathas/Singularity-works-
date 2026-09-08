from __future__ import annotations

"""Frozen wider-egress discriminator: descendant DNS-helper loopback path.

Purpose
=======
Pressure a materially different path from generic UDP: a protected PowerShell root
launches the Windows nslookup helper with ProcessStartInfo/Process.Start and an
explicit parent-owned DNS server at 127.0.0.1:53. The same root/child command is
run first without containment and then through run_zero_network_process.

The parent DNS responder observes actual DNS query datagrams and returns a minimal
A response so the unprotected positive control can complete. Query receipt is the
decisive network signal. Child/root exit codes classify harness failures but do not
substitute for listener evidence.

Claim ceiling
=============
A PASS establishes only non-delivery for this exact descendant nslookup -> explicit
loopback DNS-server shape on this host/source/control combination.

DNS_HELPER_LOOPBACK_DENIAL != SYSTEM_RESOLVER_DENIAL
DNS_HELPER_LOOPBACK_DENIAL != INTERNET_DNS_DENIAL
DNS_HELPER_LOOPBACK_DENIAL != GENERAL_DESCENDANT_EGRESS_DENIAL
DNS_HELPER_RESULT != QUIC_OR_PROXY_RESULT
WIDER_ATTEMPT_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT

No Internet endpoint, provider, OAuth credential, source mutation, DNS-setting
change, hosts-file change, or machine-wide firewall mutation is part of this test.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
from uuid import uuid4

EXPECTED_SOURCE_HEAD = "43aa7feac7e8a15828116bd700b644560714496d"
EXPECTED_CONTROL_HEAD = "f59a32946cea1af64e427a4d9db64a7075f691dd"
EXPECTED_CONTROL_CHECKPOINT = "64f1804e9d6ec64b1638cacbf25bd8963ad967958a1f2847e4d3a352c887a589"
GEN14_CHECKPOINT = "checkpoint-app-live-0014-43aa7feac7e8"
PARENT_ATTEMPT_ID = "attempt-egress-wider-v0-2-1-3-descendant-udp-loopback-cwd-repair-first-result"
ATTEMPT_ID = "attempt-egress-wider-v0-2-2-descendant-dns-helper-loopback-first"
QNAME = "pcmmad-egress-dns-v022.test"
ROOT_PROCESS_START_ERROR_EXIT = 191
DNS_SERVER_HOST = "127.0.0.1"
DNS_SERVER_PORT = 53

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
        raise RuntimeError("Windows PowerShell is unavailable")
    path = Path(found).resolve()
    if not path.is_absolute() or not path.exists():
        raise RuntimeError("resolved PowerShell executable is unavailable")
    return path


def _nslookup() -> Path:
    found = shutil.which("nslookup.exe") or shutil.which("nslookup")
    if not found:
        raise RuntimeError("nslookup is unavailable")
    path = Path(found).resolve()
    if not path.is_absolute() or not path.exists():
        raise RuntimeError("resolved nslookup executable is unavailable")
    return path


def _root_process_start_script(executable: Path, child_arguments: str) -> str:
    executable_text = str(executable).replace("'", "''")
    argument_text = child_arguments.replace("'", "''")
    return (
        "$ErrorActionPreference='Stop'; try { "
        "$psi=New-Object System.Diagnostics.ProcessStartInfo; "
        f"$psi.FileName='{executable_text}'; "
        f"$psi.Arguments='{argument_text}'; "
        "$psi.UseShellExecute=$false; "
        "$p=[System.Diagnostics.Process]::Start($psi); "
        f"if($null -eq $p){{exit {ROOT_PROCESS_START_ERROR_EXIT}}}; "
        "$p.WaitForExit(); exit $p.ExitCode "
        f"}} catch {{ exit {ROOT_PROCESS_START_ERROR_EXIT} }}"
    )


def _question_end(packet: bytes) -> int:
    if len(packet) < 12:
        raise ValueError("DNS packet shorter than header")
    i = 12
    while True:
        if i >= len(packet):
            raise ValueError("unterminated DNS qname")
        n = packet[i]
        i += 1
        if n == 0:
            break
        if n & 0xC0:
            raise ValueError("compressed qname not expected in query")
        if i + n > len(packet):
            raise ValueError("DNS label exceeds packet")
        i += n
    if i + 4 > len(packet):
        raise ValueError("DNS question missing qtype/qclass")
    return i + 4


def _dns_response(query: bytes) -> bytes:
    end = _question_end(query)
    txid = query[:2]
    flags = b"\x81\x80"
    counts = struct.pack("!HHHH", 1, 1, 0, 0)
    question = query[12:end]
    answer = b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, 0, 4) + socket.inet_aton("127.0.0.1")
    return txid + flags + counts + question + answer


class DnsResponder:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.stop = threading.Event()
        self.thread: threading.Thread | None = None
        self.observations: list[dict[str, object]] = []
        self.errors: list[str] = []

    def start(self) -> None:
        self.stop.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        self.sock.settimeout(0.2)
        while not self.stop.is_set():
            try:
                data, address = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError as exc:
                if not self.stop.is_set():
                    self.errors.append(f"recv:{type(exc).__name__}:{exc}")
                return
            obs: dict[str, object] = {
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "peer": [str(address[0]), int(address[1])],
                "response_sent": False,
            }
            try:
                response = _dns_response(data)
                self.sock.sendto(response, address)
                obs["response_sent"] = True
                obs["response_sha256"] = hashlib.sha256(response).hexdigest()
            except Exception as exc:
                self.errors.append(f"response:{type(exc).__name__}:{exc}")
            self.observations.append(obs)

    def finish(self, grace_seconds: float = 0.4) -> dict[str, object]:
        time.sleep(grace_seconds)
        self.stop.set()
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        return {
            "received": bool(self.observations),
            "query_count": len(self.observations),
            "observations": list(self.observations),
            "errors": list(self.errors),
        }


def _emit(result: dict[str, object], exit_code: int) -> int:
    result["schema"] = "singularity-works.egress-wider-v0.2.2-descendant-dns-helper-loopback-result/0.1"
    result["attempt_id"] = ATTEMPT_ID
    result["parent_attempt_id"] = PARENT_ATTEMPT_ID
    result["source_head"] = EXPECTED_SOURCE_HEAD
    result["gen14_checkpoint"] = GEN14_CHECKPOINT
    result["durable_control_head"] = EXPECTED_CONTROL_HEAD
    result["durable_control_checkpoint"] = EXPECTED_CONTROL_CHECKPOINT
    result["artifact_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["authority"] = "NONE_BY_CONTENT"
    result["claim_ceiling"] = "BOUNDED_DESCENDANT_DNS_HELPER_LOOPBACK_ONLY"
    result["runtime_law_earned"] = False
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


def main() -> int:
    started = time.monotonic()
    result: dict[str, object] = {
        "status": "HARNESS_INVALID",
        "positive_control": None,
        "protected": None,
        "dns_server": {"host": DNS_SERVER_HOST, "port": DNS_SERVER_PORT},
        "qname": QNAME,
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
        result["reason"] = "source currentness mismatch; protected execution refused"
        return _emit(result, 3)

    try:
        powershell = _powershell()
        nslookup = _nslookup()
    except Exception as exc:
        result["reason"] = f"tool preflight failed: {type(exc).__name__}: {exc}"
        return _emit(result, 3)

    child_arguments = f"-timeout=1 -retry=1 {QNAME} {DNS_SERVER_HOST}"
    root_script = _root_process_start_script(nslookup, child_arguments)
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
    result["child_executable"] = "<LOCAL_NSLOOKUP_PATH>"

    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        listener.bind((DNS_SERVER_HOST, DNS_SERVER_PORT))
    except OSError as exc:
        listener.close()
        result["reason"] = f"parent DNS listener bind failed: {type(exc).__name__}: {exc}"
        return _emit(result, 3)

    try:
        positive_responder = DnsResponder(listener)
        positive_responder.start()
        positive = subprocess.run(
            root_command,
            cwd=powershell.parent,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        positive_dns = positive_responder.finish()
        result["positive_control"] = {
            "root_exit_code": positive.returncode,
            "dns": positive_dns,
            "stderr_nonempty": bool(positive.stderr),
        }
        if positive.returncode != 0:
            result["reason"] = f"unprotected nslookup positive control returned nonzero exit code {positive.returncode}"
            return _emit(result, 3)
        if not positive_dns["received"]:
            result["reason"] = "unprotected descendant nslookup produced no DNS query at parent-owned server"
            return _emit(result, 3)
        if positive_dns["errors"]:
            result["reason"] = "parent DNS responder encountered positive-control errors"
            return _emit(result, 3)

        protected_responder = DnsResponder(listener)
        protected_responder.start()
        try:
            receipt = run_zero_network_process(
                root_command,
                timeout_seconds=10.0,
                cwd=powershell.parent,
                profile_name=f"SingularityWorks.EgressDNSV022.{uuid4().hex[:8]}",
            )
        except ProtectedProcessError as exc:
            protected_dns = protected_responder.finish()
            result["protected"] = {"receipt": None, "dns": protected_dns}
            result["reason"] = f"protected-process setup/lifecycle failed: {type(exc).__name__}: {exc}"
            return _emit(result, 3)
        except Exception as exc:
            protected_dns = protected_responder.finish()
            result["protected"] = {"receipt": None, "dns": protected_dns}
            result["reason"] = f"unexpected protected-run failure: {type(exc).__name__}: {exc}"
            return _emit(result, 3)

        protected_dns = protected_responder.finish()
        receipt_dict = receipt.as_dict()
        receipt_dict["executable"] = "<LOCAL_POWERSHELL_PATH>"
        receipt_dict["profile_name"] = "<EPHEMERAL_APPCONTAINER_PROFILE>"
        result["protected"] = {"receipt": receipt_dict, "dns": protected_dns}

        receipt_shape_ok = (
            receipt.appcontainer_verified
            and receipt.immediate_job_verified
            and receipt.capability_count == 0
            and receipt.inherited_handles is False
            and receipt.timed_out is False
        )
        if not receipt_shape_ok:
            result["reason"] = "protected root receipt failed required AppContainer/Job/zero-capability shape"
            return _emit(result, 3)

        if protected_dns["received"]:
            result["status"] = "FAIL_BYPASS_FOUND"
            result["reason"] = "protected descendant nslookup delivered DNS query to parent-owned loopback DNS server"
            result["elapsed_seconds"] = round(time.monotonic() - started, 6)
            return _emit(result, 2)

        if receipt.exit_code == ROOT_PROCESS_START_ERROR_EXIT:
            result["reason"] = "protected root reported Process.Start harness failure"
            return _emit(result, 3)

        result["status"] = "PASS_BOUNDED_DESCENDANT_DNS_HELPER_LOOPBACK_DENIAL"
        result["reason"] = (
            "unprotected Process.Start descendant nslookup reached parent-owned DNS server and received a response; "
            "protected AppContainer+Job root produced no DNS query under the same root/child command shape"
        )
        result["elapsed_seconds"] = round(time.monotonic() - started, 6)
        return _emit(result, 0)
    finally:
        listener.close()


if __name__ == "__main__":
    raise SystemExit(main())
