from __future__ import annotations
# complexity_justified: integrated forge operator surface — three-wing HUD
# Architecture: Glass Cockpit Principle — make the invisible visible.
# Layout: TOP BAR | [LEFT WING] | [CENTER] | [RIGHT WING] | BOTTOM EVENTS
# Isomorphisms:
#   EICAS (Warning/Caution/Advisory) → FAIL/WARN/PASS gate matrix
#   Avionics T-scan → Verdict dominates, warrant supplements, stats secondary
#   NASA Open MCT telemetry limits → gate severity thresholds
#   ARINC 661 declutter → FULL/COMPACT/STATUS modes
#   btop ANSI 24-bit color system (Apache-2.0) → theme tokens
#   ALCI cognitive priority stack → warrant before stats before events

from dataclasses import dataclass, field
import ctypes
import os
import shutil
import sys
import textwrap
import time


# ===========================================================================
# ANSI color/effect tokens  (btop-inspired Apache-2.0 pattern, clean impl)
# ===========================================================================

_VT = os.name != "nt" or True  # overridden at runtime

def _esc(code: str) -> str:
    return f"\x1b[{code}"

class _C:
    """24-bit ANSI color helpers — all strings so they compose cleanly."""
    RESET   = _esc("0m")
    BOLD    = _esc("1m")
    DIM     = _esc("2m")
    ITALIC  = _esc("3m")

    # Forge semantic palette  (Liquid-Aero / ALCI inspired)
    BG_VOID       = _esc("48;2;3;1;8m")      # #030108
    BG_GLASS      = _esc("48;2;10;6;18m")    # #0A0612
    FG_PRIMARY    = _esc("38;2;240;234;255m") # #F0EAFF Pale Orchid
    FG_SECONDARY  = _esc("38;2;192;185;229m") # #C0B9E5
    FG_DIM        = _esc("38;2;139;127;168m") # #8B7FA8
    FG_ACCENT     = _esc("38;2;167;139;250m") # #A78BFA

    # EICAS-style status colors
    RED     = _esc("38;2;239;68;68m")    # #EF4444
    AMBER   = _esc("38;2;245;158;11m")  # #F59E0B
    GREEN   = _esc("38;2;16;185;129m")  # #10B981
    CYAN    = _esc("38;2;59;130;246m")  # #3B82F6
    MAGENTA = _esc("38;2;167;139;250m") # #A78BFA (same as accent)
    WHITE   = _esc("38;2;255;255;255m")

    # Background accents for status cells
    BG_RED    = _esc("48;2;127;29;29m")  # deep red
    BG_AMBER  = _esc("48;2;120;53;15m")  # deep amber
    BG_GREEN  = _esc("48;2;6;78;59m")    # deep green
    BG_CYAN   = _esc("48;2;23;37;84m")   # deep blue

    # Trust tier corona colors (ALCI spec)
    T1 = _esc("38;2;74;58;140m")   # #4A3A8C indigo
    T2 = _esc("38;2;140;122;58m")  # #8C7A3A amber
    T3 = _esc("38;2;140;74;58m")   # #8C4A3A orange-red
    T4 = _esc("38;2;140;42;42m")   # #8C2A2A red

    # Compound derivation rule colors
    RULE_R1 = _esc("38;2;139;92;246m")  # violet — injection+trust
    RULE_R2 = _esc("38;2;236;72;153m")  # pink   — trust+network (SSRF)
    RULE_R3 = _esc("38;2;239;68;68m")   # red    — critical 3-hop
    RULE_R4 = _esc("38;2;251;146;60m")  # orange — memory+taint


def _c(color: str, text: str, reset: bool = True) -> str:
    """Wrap text in color if VT is enabled."""
    if not _VT:
        return text
    tail = _C.RESET if reset else ""
    return f"{color}{text}{tail}"


def _colored_verdict(status: str) -> str:
    s = status.upper()
    if s == "RED":
        return _c(_C.BG_RED + _C.WHITE + _C.BOLD, f" ✗ {s} ", False) + _C.RESET
    if s in ("AMBER", "YELLOW"):
        return _c(_C.BG_AMBER + _C.WHITE + _C.BOLD, f" ~ {s} ", False) + _C.RESET
    if s == "GREEN":
        return _c(_C.BG_GREEN + _C.WHITE + _C.BOLD, f" ✓ {s} ", False) + _C.RESET
    return _c(_C.FG_DIM, f" ? {s} ")


def _gate_icon(status: str) -> str:
    s = status.lower()
    if s == "fail":
        return _c(_C.RED + _C.BOLD, "✗")
    if s == "warn":
        return _c(_C.AMBER, "~")
    if s == "pass":
        return _c(_C.GREEN, "✓")
    return _c(_C.FG_DIM, "?")


# ===========================================================================
# HudSnapshot — data contract
# ===========================================================================

@dataclass
class TaintChainRecord:
    source_type: str  = "USER_INPUT"
    source_line: int  = 0
    sink_type: str    = "UNKNOWN"
    sink_line: int    = 0
    hops: int         = 1
    directed: bool    = True


@dataclass
class GateRecord:
    gate_id: str
    family: str
    status: str       # pass | fail | warn
    message: str = ""


@dataclass
class CompoundRecord:
    rule: str         # R1 | R2 | R3 | R4
    fact_type: str    # compound_taint_injection | ssrf_confirmed | critical_compound_hazard | memory_corruption_via_taint


@dataclass
class HudSnapshot:
    # Identity
    app_name: str     = "Singularity Works"
    version: str      = "v1.36"
    mode: str         = "idle"
    provider: str     = "n/a"
    session_id: str   = "n/a"
    project_tag: str  = "default"
    branch: str       = "main"
    uptime_s: float   = 0.0

    # Primary verdict
    verdict: str      = "green"     # red | amber | green
    warrant_coverage: float = 0.0
    warranted_claims: int = 0
    total_claims: int = 0

    # Phase / pipeline state
    phase: str        = "boot"
    requirement: str  = "n/a"
    radical: str      = "n/a"
    validator: str    = "n/a"
    progress_label: str = "overall"
    progress_value: float = 0.0

    # Gate fabric
    gates: list[GateRecord] = field(default_factory=list)
    counts: dict[str, int]  = field(default_factory=dict)  # pass/warn/fail/residual

    # Directed taint chains (from FactBus taint_chain facts)
    taint_chains: list[TaintChainRecord] = field(default_factory=list)

    # Compound derivations (from fixed-point loop R1-R4)
    compound: list[CompoundRecord] = field(default_factory=list)

    # Warrant text for primary claim
    primary_warrant: str = ""

    # General stats and events
    stats: dict[str, str]  = field(default_factory=dict)
    risks: list[str]       = field(default_factory=list)
    warnings: list[str]    = field(default_factory=list)
    events: list[str]      = field(default_factory=list)

    # Display mode: "full" | "compact" | "status"
    display_mode: str = "full"


# ===========================================================================
# Windows VT enable
# ===========================================================================

STD_OUTPUT_HANDLE = -11
ENABLE_PROCESSED_OUTPUT = 0x0001
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004


def _enable_vt_windows() -> bool:
    if os.name != "nt":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        if handle == 0:
            return False
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return False
        new_mode = mode.value | ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return kernel32.SetConsoleMode(handle, new_mode) != 0
    except Exception:
        return False


# ===========================================================================
# ConsoleHUD — three-wing cockpit renderer
# ===========================================================================

class ConsoleHUD:
    def __init__(self, use_alt_screen: bool = True) -> None:
        self.use_alt_screen = use_alt_screen
        self.vt_enabled = _enable_vt_windows()
        self._active = False
        global _VT
        _VT = self.vt_enabled

    def __enter__(self) -> "ConsoleHUD":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self._active:
            return
        self._active = True
        if self.vt_enabled and self.use_alt_screen:
            sys.stdout.write("\x1b[?1049h\x1b[?25l")
            sys.stdout.flush()

    def stop(self) -> None:
        if not self._active:
            return
        if self.vt_enabled and self.use_alt_screen:
            sys.stdout.write(_C.RESET + "\x1b[?25h\x1b[?1049l")
            sys.stdout.flush()
        self._active = False

    def render(self, snap: HudSnapshot) -> None:
        cols, rows = shutil.get_terminal_size(fallback=(120, 40))
        cols = max(60, cols)
        rows = max(20, rows)

        if snap.display_mode == "status":
            body = self._render_status_bar(snap, cols)
        elif snap.display_mode == "compact" or cols < 100:
            body = self._render_compact(snap, cols, rows)
        else:
            body = self._render_full(snap, cols, rows)

        if self.vt_enabled:
            sys.stdout.write("\x1b[H\x1b[2J" + body)
        else:
            sys.stdout.write("\n" + body + "\n")
        sys.stdout.flush()

    # ── Renderers ────────────────────────────────────────────────────────────

    def _render_status_bar(self, snap: HudSnapshot, cols: int) -> str:
        """Single-line status — ARINC 661 minimal mode."""
        p = snap.counts.get("pass", 0)
        w = snap.counts.get("warn", 0)
        f = snap.counts.get("fail", 0)
        parts = [
            _c(_C.FG_ACCENT + _C.BOLD, f"SW {snap.version}"),
            _colored_verdict(snap.verdict),
            _c(_C.GREEN, f"✓{p}") + " " + _c(_C.AMBER, f"~{w}") + " " + _c(_C.RED, f"✗{f}"),
            _c(_C.FG_SECONDARY, f"WC:{snap.warranted_claims}/{snap.total_claims}"),
            _c(_C.FG_DIM, f"chains:{len(snap.taint_chains)}"),
            _c(_C.FG_DIM, f"up:{int(snap.uptime_s)}s"),
        ]
        return " │ ".join(parts) + _C.RESET + "\n"

    def _render_compact(self, snap: HudSnapshot, cols: int, rows: int) -> str:
        """Compact two-column mode for narrower terminals."""
        lines: list[str] = []
        lines.append(self._top_bar(snap, cols))
        lines.append(_c(_C.FG_DIM, "─" * cols))

        # Verdict block
        lines.append(f"  VERDICT    {_colored_verdict(snap.verdict)}")
        lines.append(f"  WARRANT    {_c(_C.FG_SECONDARY, f'{snap.warranted_claims}/{snap.total_claims} claims covered')}")
        if snap.primary_warrant:
            for wline in textwrap.wrap(snap.primary_warrant, cols - 13)[:3]:
                lines.append(f"             {_c(_C.FG_DIM, wline)}")

        lines.append(_c(_C.FG_DIM, "─" * cols))
        lines.append(_c(_C.FG_ACCENT, "  GATE MATRIX"))
        for gate in snap.gates[:12]:
            icon = _gate_icon(gate.status)
            fam  = _c(_C.FG_SECONDARY, f"{gate.family:22s}")
            msg  = _c(_C.FG_DIM, gate.message[:cols - 30]) if gate.message else ""
            lines.append(f"  {icon} {fam} {msg}")

        if snap.taint_chains:
            lines.append(_c(_C.FG_DIM, "─" * cols))
            lines.append(_c(_C.CYAN, "  TAINT CHAINS"))
            for tc in snap.taint_chains[:4]:
                lines.append(self._taint_chain_line(tc, cols - 4, indent=4))

        lines.append(_c(_C.FG_DIM, "─" * cols))
        for item in snap.events[-5:]:
            lines.append(f"  {_c(_C.FG_DIM, item[:cols - 4])}")

        return "\n".join(lines) + _C.RESET + "\n"

    def _render_full(self, snap: HudSnapshot, cols: int, rows: int) -> str:
        """Full three-wing cockpit layout.

        ┌─ TOP BAR ──────────────────────────────────────────────────────┐
        │ LEFT WING (gate matrix)  │ CENTER (verdict+warrant) │ RIGHT     │
        ├──────────────────────────┼─────────────────────────┼───────────┤
        │                          │                         │           │
        └─ EVENTS ───────────────────────────────────────────────────────┘
        """
        lines: list[str] = []

        # ── TOP BAR ──────────────────────────────────────────────────────────
        lines.append(self._top_bar(snap, cols))
        lines.append(_c(_C.FG_DIM, "═" * cols))

        # ── Column widths  (Left 30%, Center 40%, Right 30%)
        left_w   = max(28, int(cols * 0.30))
        right_w  = max(28, int(cols * 0.28))
        center_w = max(24, cols - left_w - right_w - 4)  # 4 separators

        # ── Build three columns independently ────────────────────────────────
        left_col   = self._left_wing(snap, left_w)
        center_col = self._center_panel(snap, center_w)
        right_col  = self._right_wing(snap, right_w)

        # ── Column headers ────────────────────────────────────────────────────
        lh = _c(_C.FG_ACCENT + _C.BOLD, f"{'GATE MATRIX':^{left_w}}")
        ch = _c(_C.FG_ACCENT + _C.BOLD, f"{'VERDICT  ·  WARRANT':^{center_w}}")
        rh = _c(_C.FG_ACCENT + _C.BOLD, f"{'CHAINS  &  COMPOUND':^{right_w}}")
        lines.append(f"{lh} │ {ch} │ {rh}")
        lines.append(_c(_C.FG_DIM, f"{'─'*left_w}─┼─{'─'*center_w}─┼─{'─'*right_w}"))

        # ── Stitch columns together ───────────────────────────────────────────
        body_rows = max(len(left_col), len(center_col), len(right_col))
        # Pad each column to same height
        left_col   += [" " * left_w]   * (body_rows - len(left_col))
        center_col += [" " * center_w] * (body_rows - len(center_col))
        right_col  += [" " * right_w]  * (body_rows - len(right_col))

        sep = _c(_C.FG_DIM, " │ ")
        for a, b, c_ in zip(left_col, center_col, right_col):
            # Truncate each cell to its column width (visual width, ignoring escapes)
            lines.append(f"{a}{sep}{b}{sep}{c_}")

        # ── BOTTOM: divider + events ──────────────────────────────────────────
        lines.append(_c(_C.FG_DIM, "═" * cols))
        lines.append(self._events_bar(snap, cols))

        return "\n".join(lines) + _C.RESET + "\n"

    # ── TOP BAR ──────────────────────────────────────────────────────────────

    def _top_bar(self, snap: HudSnapshot, cols: int) -> str:
        """
        ■ SW v1.36  │  VERDICT: ■ RED  │  WC: 32/32  │  ✗3 ~1 ✓45  │  up:12s
        """
        p = snap.counts.get("pass",     0)
        w = snap.counts.get("warn",     0)
        f = snap.counts.get("fail",     0)
        r = snap.counts.get("residual", 0)

        compound_str = ""
        if snap.compound:
            rules = " ".join(
                _c(getattr(_C, f"RULE_{cr.rule}"), cr.rule)
                for cr in snap.compound[:4]
            )
            compound_str = f" │ COMPOUND: {rules}"

        parts = [
            _c(_C.MAGENTA + _C.BOLD, f"■ {snap.app_name} {snap.version}"),
            f"VERDICT: {_colored_verdict(snap.verdict)}",
            _c(_C.FG_SECONDARY, f"WC: {snap.warranted_claims}/{snap.total_claims}"),
            _c(_C.RED,   f"✗{f}") + " " +
            _c(_C.AMBER, f"~{w}") + " " +
            _c(_C.GREEN, f"✓{p}") +
            (_c(_C.FG_DIM, f" r{r}") if r else ""),
            _c(_C.FG_DIM, f"chains:{len(snap.taint_chains)}"),
            _c(_C.FG_DIM, f"up:{int(snap.uptime_s)}s"),
        ]
        bar = " │ ".join(parts) + compound_str
        # Pad/crop to cols
        raw_len = len(self._strip_esc(bar))
        if raw_len < cols:
            bar += " " * (cols - raw_len)
        return bar

    # ── LEFT WING: gate matrix ────────────────────────────────────────────────

    def _left_wing(self, snap: HudSnapshot, width: int) -> list[str]:
        rows: list[str] = []
        # Phase / radical header
        rows.append(_c(_C.FG_SECONDARY, self._crop(f"PHASE    {snap.phase}", width)))
        rows.append(_c(_C.FG_DIM,       self._crop(f"REQ      {snap.requirement}", width)))
        rows.append(_c(_C.FG_DIM,       self._crop(f"RADICAL  {snap.radical}", width)))
        rows.append(_c(_C.FG_DIM,       self._crop(f"PROGRESS {snap.progress_label}", width)))
        # Progress bar
        rows.append(self._progress_bar(snap.progress_value, width))
        rows.append("")

        # Gate matrix  (EICAS-style — fail rows highlighted)
        rows.append(_c(_C.FG_DIM, self._crop("─ GATES ─" + "─" * width, width)))

        # Failures first (most critical), then warns, then pass summary
        fails  = [g for g in snap.gates if g.status == "fail"]
        warns  = [g for g in snap.gates if g.status == "warn"]
        passes = [g for g in snap.gates if g.status == "pass"]

        for gate in fails[:8]:
            rows.append(self._gate_row(gate, width, highlight=True))
        for gate in warns[:5]:
            rows.append(self._gate_row(gate, width, highlight=False))
        if passes:
            rows.append(_c(_C.GREEN + _C.DIM,
                self._crop(f"  ✓ {len(passes)} gates pass", width)))

        # Residuals summary
        r = snap.counts.get("residual", 0)
        if r:
            rows.append(_c(_C.FG_DIM, self._crop(f"  ~ {r} residual obligations", width)))

        return rows

    def _gate_row(self, gate: GateRecord, width: int, highlight: bool) -> str:
        icon = _gate_icon(gate.status)
        # Gate family (truncated)
        max_fam = min(20, width - 6)
        fam = self._crop(gate.family, max_fam)
        if highlight:
            # Red background for fail rows — avionics warning style
            fam_colored = _c(_C.RED, fam)
        else:
            fam_colored = _c(_C.AMBER, fam)
        msg = ""
        if gate.message and width > 35:
            msg = _c(_C.FG_DIM, " " + self._crop(gate.message, width - max_fam - 6))
        return f"  {icon} {fam_colored}{msg}"

    # ── CENTER PANEL: verdict + warrant ──────────────────────────────────────

    def _center_panel(self, snap: HudSnapshot, width: int) -> list[str]:
        rows: list[str] = []

        # Big verdict display
        verdict_block = _colored_verdict(snap.verdict)
        rows.append(f"  {verdict_block}")
        rows.append("")

        # Warrant coverage meter
        cov = snap.warranted_claims
        tot = snap.total_claims
        pct = (cov / tot * 100) if tot else 0
        cov_bar = self._warrant_meter(pct, width - 4)
        rows.append(f"  {_c(_C.FG_SECONDARY, 'WARRANT COVERAGE')}")
        rows.append(f"  {cov_bar}  {_c(_C.FG_ACCENT, f'{cov}/{tot}')}")
        rows.append("")

        # Primary warrant text (Holofont principle: text floats above substrate)
        if snap.primary_warrant:
            rows.append(_c(_C.FG_SECONDARY, self._crop("  PRIMARY CLAIM:", width)))
            for wline in textwrap.wrap(snap.primary_warrant, width - 4)[:5]:
                rows.append(f"  {_c(_C.FG_PRIMARY, wline)}")
            rows.append("")

        # Stats block
        if snap.stats:
            rows.append(_c(_C.FG_DIM, self._crop("  ─ METRICS ─" + "─" * width, width)))
            for key, val in list(snap.stats.items())[:8]:
                k = _c(_C.FG_SECONDARY, self._crop(f"  {key.upper()}", 16))
                v = _c(_C.FG_PRIMARY, self._crop(str(val), width - 20))
                rows.append(f"{k}  {v}")

        # Risks
        if snap.risks:
            rows.append("")
            rows.append(_c(_C.RED, "  ⚠ RISKS"))
            for risk in snap.risks[:4]:
                rows.append(f"  {_c(_C.RED + _C.DIM, '! ')}{_c(_C.FG_SECONDARY, self._crop(risk, width - 5))}")

        return rows

    # ── RIGHT WING: taint chains + compound derivations ───────────────────────

    def _right_wing(self, snap: HudSnapshot, width: int) -> list[str]:
        rows: list[str] = []

        # Directed taint chains
        rows.append(_c(_C.CYAN, self._crop("  TAINT CHAINS", width)))
        if snap.taint_chains:
            for tc in snap.taint_chains[:6]:
                rows.append(self._taint_chain_line(tc, width, indent=2))
        else:
            rows.append(_c(_C.FG_DIM, "  (none detected)"))
        rows.append("")

        # Compound derivation rules  (R1-R4 from fixed-point loop)
        rows.append(_c(_C.MAGENTA, self._crop("  COMPOUND DERIVATION", width)))
        if snap.compound:
            rule_labels = {
                "R1": ("compound_taint",  _C.RULE_R1, "injection + trust"),
                "R2": ("ssrf_confirmed",  _C.RULE_R2, "trust + network"),
                "R3": ("critical_hazard", _C.RULE_R3, "injection+trust+sink (3-hop)"),
                "R4": ("memory_taint",    _C.RULE_R4, "memory + trust"),
            }
            shown = set()
            for cr in snap.compound:
                if cr.rule in shown:
                    continue
                shown.add(cr.rule)
                label, color, desc = rule_labels.get(cr.rule, (cr.rule, _C.FG_DIM, ""))
                icon = _c(color + _C.BOLD, f"[{cr.rule}]")
                dstr = _c(_C.FG_SECONDARY, self._crop(desc, width - 8))
                rows.append(f"  {icon} {dstr}")
        else:
            rows.append(_c(_C.FG_DIM, "  (no compound chains)"))
        rows.append("")

        # Phase / branch / session meta
        rows.append(_c(_C.FG_DIM, self._crop("  ─ META ─" + "─" * width, width)))
        rows.append(_c(_C.FG_DIM, self._crop(f"  branch   {snap.branch}", width)))
        rows.append(_c(_C.FG_DIM, self._crop(f"  session  {snap.session_id}", width)))
        rows.append(_c(_C.FG_DIM, self._crop(f"  provider {snap.provider}", width)))
        rows.append(_c(_C.FG_DIM, self._crop(f"  project  {snap.project_tag}", width)))

        # Warnings
        if snap.warnings:
            rows.append("")
            for warn in snap.warnings[:3]:
                rows.append(f"  {_c(_C.AMBER, '? ')}{_c(_C.FG_DIM, self._crop(warn, width - 5))}")

        return rows

    # ── EVENTS BAR (bottom) ───────────────────────────────────────────────────

    def _events_bar(self, snap: HudSnapshot, cols: int) -> str:
        lines = [_c(_C.FG_ACCENT, "EVENTS")]
        for item in snap.events[-6:]:
            ts_marker = _c(_C.FG_DIM, "·")
            lines.append(f" {ts_marker} {_c(_C.FG_DIM, self._crop(item, cols - 5))}")
        return "\n".join(lines)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _progress_bar(self, value: float, width: int) -> str:
        value = max(0.0, min(1.0, value))
        inner = max(4, width - 2)
        fill  = int(inner * value)
        pct   = int(value * 100)
        bar_fill  = _c(_C.CYAN,   "█" * fill)
        bar_empty = _c(_C.FG_DIM, "░" * (inner - fill))
        pct_str   = _c(_C.FG_SECONDARY, f"{pct:3d}%")
        return f"[{bar_fill}{bar_empty}] {pct_str}"

    def _warrant_meter(self, pct: float, width: int) -> str:
        """Compact warrant coverage meter with color graduation."""
        inner = max(4, width - 6)
        fill  = int(inner * pct / 100)
        if pct >= 90:
            color = _C.GREEN
        elif pct >= 60:
            color = _C.AMBER
        else:
            color = _C.RED
        bar_fill  = _c(color, "▓" * fill)
        bar_empty = _c(_C.FG_DIM, "░" * (inner - fill))
        return f"[{bar_fill}{bar_empty}]"

    def _taint_chain_line(self, tc: TaintChainRecord, width: int, indent: int = 0) -> str:
        """
        Display: USER_INPUT:L3 ──▶ NETWORK:L7 (1 hop, directed)
        """
        arrow = _c(_C.CYAN, " ──▶ ")
        src = _c(_C.MAGENTA, f"{tc.source_type}:L{tc.source_line}")
        snk = _c(_C.RED,     f"{tc.sink_type}:L{tc.sink_line}")
        meta = _c(_C.FG_DIM, f" ({tc.hops} hop{'s' if tc.hops > 1 else ''})")
        directed_marker = _c(_C.GREEN, " ✓") if tc.directed else _c(_C.AMBER, " ~")
        pad = " " * indent
        return f"{pad}{src}{arrow}{snk}{meta}{directed_marker}"

    @staticmethod
    def _strip_esc(s: str) -> str:
        """Remove ANSI escape sequences for length measurement."""
        import re
        return re.sub(r'\x1b\[[0-9;]*m', '', s)

    @staticmethod
    def _crop(text: str, width: int) -> str:
        if len(text) <= width:
            return text
        return text[:max(0, width - 3)] + "..."


# ===========================================================================
# Snapshot builder from forge RunResult
# ===========================================================================

def snapshot_from_run_result(
    result: "Any",
    orchestrator: "Any | None" = None,
    *,
    app_name: str = "Singularity Works",
    version: str = "v1.36",
    branch: str = "main",
    uptime_s: float = 0.0,
    display_mode: str = "full",
) -> HudSnapshot:
    """
    Build a HudSnapshot from a forge RunResult + Orchestrator.
    Extracts warrant coverage, taint chains, compound derivations, gate records.
    """
    snap = HudSnapshot(
        app_name=app_name,
        version=version,
        branch=branch,
        uptime_s=uptime_s,
        display_mode=display_mode,
    )

    # ── Assurance ─────────────────────────────────────────────────────────────
    if result is not None and hasattr(result, "assurance"):
        assurance = result.assurance
        snap.verdict = getattr(assurance, "status", "green")
        d = assurance.to_dict() if hasattr(assurance, "to_dict") else {}
        snap.warrant_coverage  = d.get("warrant_coverage", 0.0)
        snap.warranted_claims  = d.get("warranted_claims", 0)
        snap.total_claims      = d.get("total_claims", 0)

        # Extract primary claim warrant text
        for claim in getattr(assurance, "claims", []):
            if getattr(claim, "claim_type", "") == "primary":
                snap.primary_warrant = getattr(claim, "warrant", "")
                break

    # ── Gate summary ─────────────────────────────────────────────────────────
    if result is not None and hasattr(result, "gate_summary"):
        gs = result.gate_summary
        snap.counts = gs.counts if hasattr(gs, "counts") else {}
        for gr in getattr(gs, "results", []):
            msg = ""
            findings = getattr(gr, "findings", [])
            if findings:
                msg = findings[0].message[:80] if hasattr(findings[0], "message") else ""
            snap.gates.append(GateRecord(
                gate_id=gr.gate_id,
                family=getattr(gr, "gate_family", "") or gr.gate_id.split(":")[0],
                status=gr.status,
                message=msg,
            ))

    # ── FactBus — taint chains + compound derivations ─────────────────────────
    if orchestrator is not None and hasattr(orchestrator, "facts"):
        bus = orchestrator.facts

        # Taint chains
        for fact in bus.by_type("taint_chain") if hasattr(bus, "by_type") else []:
            p = fact.payload or {}
            snap.taint_chains.append(TaintChainRecord(
                source_type=p.get("source_type", "USER_INPUT"),
                source_line=p.get("source_line", 0),
                sink_type=p.get("boundary_type", "UNKNOWN"),
                sink_line=p.get("sink_line", 0),
                hops=p.get("hops", 1),
                directed=p.get("directed", True),
            ))

        # Compound derivations (R1-R4 from fixed-point loop)
        compound_fact_types = {
            "compound_taint_injection":   "R1",
            "ssrf_confirmed":             "R2",
            "critical_compound_hazard":   "R3",
            "memory_corruption_via_taint":"R4",
        }
        for fact_type, rule in compound_fact_types.items():
            facts = bus.by_type(fact_type) if hasattr(bus, "by_type") else []
            if facts:
                snap.compound.append(CompoundRecord(rule=rule, fact_type=fact_type))

    return snap


# ===========================================================================
# Demo / __main__
# ===========================================================================

if __name__ == "__main__":
    hud = ConsoleHUD()
    start = time.monotonic()

    # Simulate a realistic forge run result
    demo_gates = [
        GateRecord("genome:injection.nosql_injection:nosql",          "injection",        "fail",  "NoSQL injection: user-controlled value reaches .find()"),
        GateRecord("genome:injection.ssti_render_template:ssti",      "injection",        "fail",  "SSTI: render_template_string with user-controlled template"),
        GateRecord("genome:execution_safety.flask_debug:flask_debug",  "execution_safety", "fail",  "app.run(debug=True) exposes Werkzeug debugger (RCE)"),
        GateRecord("genome:crypto.no_hardcoded_secrets:credential",   "crypto",           "fail",  "Hardcoded credential 'SECRET_KEY' extractable from binary"),
        GateRecord("genome:serialize.no_yaml_unsafe_load:yaml",       "serialize",        "warn",  "yaml.load() without Loader — fires both capsules"),
        GateRecord("genome:network.bind_all_interfaces:bind",         "network",          "warn",  "Service bound to 0.0.0.0 — all interfaces exposed"),
        GateRecord("genome:auth.csrf_exempt:csrf",                    "auth",             "pass",  ""),
        GateRecord("genome:crypto.weak_rsa_key:rsa",                  "crypto",           "pass",  ""),
        GateRecord("genome:trust_boundary_validation.ssrf:ssrf",      "trust_boundary",   "pass",  ""),
        GateRecord("genome:query_integrity.parameterized:sqli",       "query_integrity",  "pass",  ""),
    ]

    demo_chains = [
        TaintChainRecord("USER_INPUT", 14, "NOSQL",   17, 1, True),
        TaintChainRecord("USER_INPUT", 18, "TEMPLATE", 20, 1, True),
        TaintChainRecord("USER_INPUT", 33, "NETWORK",  37, 2, True),
    ]

    demo_compound = [
        CompoundRecord("R1", "compound_taint_injection"),
        CompoundRecord("R3", "critical_compound_hazard"),
    ]

    with hud:
        for i in range(101):
            pct = i / 100.0
            snap = HudSnapshot(
                app_name="Singularity Works",
                version="v1.36",
                mode="dialectic",
                provider="qwen2.5-coder-7b",
                session_id="demo-42",
                project_tag="bug-bounty-engine",
                branch="main",
                uptime_s=time.monotonic() - start,
                verdict="red",
                warrant_coverage=1.0,
                warranted_claims=43,
                total_claims=43,
                primary_warrant=(
                    "FALSIFIED: 4 security findings require remediation. "
                    "NoSQL injection + SSTI + debug RCE + hardcoded secret detected. "
                    "4 gate families falsified. Runtime behavior unobserved."
                ),
                phase="qa-synthesis",
                requirement="Security audit — Flask endpoint",
                radical="TRUST+PARSE+BOUNDARY",
                validator="genome-gate-fabric v1.36",
                progress_label="analysis progress",
                progress_value=pct,
                gates=demo_gates,
                counts={"pass": 6, "warn": 2, "fail": 4, "residual": 3},
                taint_chains=demo_chains,
                compound=demo_compound,
                stats={
                    "capsules":   "79",
                    "strategies": "75",
                    "gate_iters": "3 (converged)",
                    "elapsed_ms": f"{80 + i}",
                },
                risks=[
                    "NoSQL injection — MongoDB $where bypass possible",
                    "SSTI — arbitrary code via {{7*7}} in template",
                    "Flask debug=True — RCE via Werkzeug PIN bypass",
                    "Hardcoded SECRET_KEY — extractable from binary",
                ],
                warnings=[
                    "yaml.load() fires two capsules (dedup pending)",
                    "0.0.0.0 bind — legitimate if behind proxy",
                ],
                events=[
                    f"[{i:03d}] genome bundle selected — 12 capsules active",
                    f"[{i:03d}] fixed-point iteration 1: 14 new facts",
                    f"[{i:03d}] fixed-point iteration 2: 3 new facts",
                    f"[{i:03d}] fixed-point iteration 3: converged",
                    f"[{i:03d}] R1 compound_taint_injection: fired",
                    f"[{i:03d}] R3 critical_compound_hazard: fired",
                    f"[{i:03d}] assurance rollup: warrant_coverage=1.0",
                ],
                display_mode="full",
            )
            hud.render(snap)
            time.sleep(0.05)
