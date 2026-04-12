from __future__ import annotations
# complexity_justified: interprocedural call graph with taint propagation,
# invariant collision detection, and initialization cycle analysis.
# Local analysis has a hard ceiling — vulnerabilities that exist at function
# boundaries are invisible without the call graph. This module crosses that
# boundary. It is the difference between "local correctness checker" and
# "architectural reasoner."
#
# Isomorphism (distributed systems): the call graph is a message-passing
# network; taint propagation is a distributed information-flow protocol.
# Each function is a node; each call site is an edge; taint tokens flow
# along edges like messages through a routing network.
#
# Isomorphism (control theory): the init-cycle detector is a feedback-loop
# detector on the initialization state machine. A cycle means the machine
# has no stable equilibrium — it deadlocks.
#
# Isomorphism (type theory): invariant collision is an unsound subtyping
# relation — function B claims to write the same attribute as function A
# but without A's precondition, so the type contract is violated.

import ast
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CallSite:
    """A call from one function to another, with argument provenance."""
    callee: str             # qualified name of the called function
    args_passed: list[str]  # variable names (or literals) passed as args
    line: int


@dataclass
class TaintSource:
    """A point where untrusted external data enters the function."""
    var_name: str
    source_type: str        # "request_input" | "env" | "file" | "db_result"
    line: int


@dataclass
class TaintSink:
    """A dangerous operation that consumes a function-local variable."""
    sink_type: str          # "db_query" | "shell" | "eval" | "file_write"
    var_name: str           # the variable consumed
    line: int


@dataclass
class WriteOp:
    """A write to an attribute/dict key via setattr or direct assignment."""
    target_attr: str        # e.g. "role" in setattr(obj, "role", val)
    source_var: str         # value being written
    guarded: bool           # is this write inside an if/whitelist check?
    line: int


@dataclass
class FunctionNode:
    """Everything the forge knows about one function from static analysis."""
    func_name: str
    class_name: str | None
    params: list[str]
    taint_sources: list[TaintSource] = field(default_factory=list)
    taint_sinks: list[TaintSink] = field(default_factory=list)
    calls: list[CallSite] = field(default_factory=list)
    writes: list[WriteOp] = field(default_factory=list)
    has_whitelist_check: bool = False
    checked_attrs: set[str] = field(default_factory=set)
    init_method_calls: list[str] = field(default_factory=list)
    line: int = 0


@dataclass
class TaintPath:
    """An interprocedural data-flow path from a taint source to a sink."""
    entry_func: str         # where taint enters
    taint_var: str          # which variable carries the taint
    sink_func: str          # where it reaches a dangerous sink
    sink_type: str          # what kind of sink
    sink_line: int
    call_chain: list[str]   # full path through function calls
    confidence: str = "high"

    def description(self) -> str:
        chain = " → ".join(self.call_chain)
        return (
            f"Interprocedural taint: '{self.taint_var}' from "
            f"'{self.entry_func}' reaches {self.sink_type} sink in "
            f"'{self.sink_func}' (line {self.sink_line}) via [{chain}]"
        )


@dataclass
class InvariantViolation:
    """A bypass of a function-enforced invariant by another function."""
    enforcing_func: str     # function that guards writes to target_attr
    bypass_func: str        # function that writes without the guard
    target_attr: str
    bypass_line: int
    description: str


@dataclass
class InitCycle:
    """A circular initialization dependency between classes."""
    cycle: list[str]        # class names forming the cycle
    description: str


