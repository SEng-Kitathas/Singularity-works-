from __future__ import annotations

"""Frozen hostile discriminators for OS/process egress enforcement Attempt 0.

IMPORTANT: this file is committed/pushed before its first execution.
No test contacts an external network endpoint. Loopback listeners are owned by the
test parent and exist only to detect protected-domain bypass.
"""

import os
from pathlib import Path
import shutil
import socket
import threading
import unittest
from uuid import uuid4

from forge_app.egress.windows_protected_process import run_zero_network_process


WINDOWS = os.name == "nt"


def _system_executable(name: str) -> Path:
    found = shutil.which(name)
    if not found:
        raise unittest.SkipTest(f"required Windows executable not found: {name}")
    path = Path(found).resolve()
    if not path.is_absolute() or not path.exists():
        raise unittest.SkipTest(f"resolved executable unavailable: {name}: {path}")
    return path


def _profile_name(label: str) -> str:
    return f"SingularityWorks.EgressAttempt0.{label}.{uuid4().hex[:8]}"


class _LocalHttpListener:
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(4)
        self.sock.settimeout(3.0)
        self.port = int(self.sock.getsockname()[1])
        self.accepted = threading.Event()
        self.error: BaseException | None = None
        self.thread = threading.Thread(target=self._serve_once, daemon=True)

    def _serve_once(self) -> None:
        try:
            conn, _ = self.sock.accept()
        except socket.timeout:
            return
        except OSError as exc:
            self.error = exc
            return
        self.accepted.set()
        try:
            conn.settimeout(1.0)
            try:
                conn.recv(4096)
            except (socket.timeout, OSError):
                pass
            try:
                conn.sendall(b"HTTP/1.1 204 No Content\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            except OSError:
                pass
        finally:
            conn.close()

    def __enter__(self) -> "_LocalHttpListener":
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.thread.join(timeout=4.0)
        self.sock.close()
        if self.thread.is_alive():
            raise AssertionError("local listener thread did not terminate")
        if self.error is not None:
            raise AssertionError(f"local listener error: {self.error}")


@unittest.skipUnless(WINDOWS, "Windows-only AppContainer/Job enforcement attempt")
class OsProcessEgressEnforcementV01Tests(unittest.TestCase):
    def test_d0_zero_capability_appcontainer_and_immediate_job_are_observed(self) -> None:
        cmd = _system_executable("cmd.exe")
        receipt = run_zero_network_process(
            [str(cmd), "/d", "/c", "exit 0"],
            timeout_seconds=5.0,
            cwd=cmd.parent,
            profile_name=_profile_name("D0"),
        )
        self.assertTrue(receipt.appcontainer_verified)
        self.assertTrue(receipt.immediate_job_verified)
        self.assertEqual(receipt.capability_count, 0)
        self.assertFalse(receipt.inherited_handles)
        self.assertFalse(receipt.timed_out)
        self.assertEqual(receipt.exit_code, 0)
        self.assertEqual(receipt.authority, "NONE")

    def test_d1_protected_root_cannot_connect_to_parent_loopback_listener(self) -> None:
        curl = _system_executable("curl.exe")
        with _LocalHttpListener() as listener:
            receipt = run_zero_network_process(
                [
                    str(curl),
                    "--noproxy",
                    "*",
                    "--connect-timeout",
                    "1",
                    "--max-time",
                    "2",
                    "--silent",
                    "--show-error",
                    f"http://127.0.0.1:{listener.port}/",
                    "--output",
                    "NUL",
                ],
                timeout_seconds=5.0,
                cwd=curl.parent,
                profile_name=_profile_name("D1"),
            )
        self.assertTrue(receipt.appcontainer_verified)
        self.assertTrue(receipt.immediate_job_verified)
        self.assertFalse(listener.accepted.is_set(), "protected root reached parent loopback listener")
        self.assertIn(
            receipt.exit_code,
            (7, 28),
            "expected curl connect/timeout failure; another exit code does not prove network denial",
        )

    def test_d2_protected_descendant_cannot_connect_to_parent_loopback_listener(self) -> None:
        cmd = _system_executable("cmd.exe")
        curl = _system_executable("curl.exe")
        child_command = (
            f'"{curl}" --noproxy * --connect-timeout 1 --max-time 2 --silent --show-error '
            f'http://127.0.0.1:{{port}}/ --output NUL'
        )
        with _LocalHttpListener() as listener:
            receipt = run_zero_network_process(
                [str(cmd), "/d", "/s", "/c", child_command.format(port=listener.port)],
                timeout_seconds=5.0,
                cwd=cmd.parent,
                profile_name=_profile_name("D2"),
            )
        self.assertTrue(receipt.appcontainer_verified)
        self.assertTrue(receipt.immediate_job_verified)
        self.assertFalse(listener.accepted.is_set(), "protected descendant reached parent loopback listener")
        self.assertIn(
            receipt.exit_code,
            (7, 28),
            "expected descendant curl connect/timeout failure; another exit code does not prove network denial",
        )

    def test_d3_job_close_terminates_timed_out_protected_process(self) -> None:
        powershell = _system_executable("powershell.exe")
        receipt = run_zero_network_process(
            [
                str(powershell),
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Start-Sleep -Seconds 30",
            ],
            timeout_seconds=0.5,
            cwd=powershell.parent,
            profile_name=_profile_name("D3"),
        )
        self.assertTrue(receipt.appcontainer_verified)
        self.assertTrue(receipt.immediate_job_verified)
        self.assertTrue(receipt.timed_out)
        self.assertTrue(receipt.job_close_terminated_process)


if __name__ == "__main__":
    unittest.main()
