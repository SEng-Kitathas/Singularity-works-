"""App-owned OS/process egress containment candidates.

This package does not mint Connection Gate, provider, semantic, or recovery authority.
Attempt 0 exposes only the bounded Windows protected-process primitive.
"""

from .windows_protected_process import (
    ProtectedProcessError,
    ProtectedProcessReceipt,
    run_zero_network_process,
)

__all__ = [
    "ProtectedProcessError",
    "ProtectedProcessReceipt",
    "run_zero_network_process",
]
