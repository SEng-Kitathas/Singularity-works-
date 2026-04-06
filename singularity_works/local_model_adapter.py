"""
Singularity Works — Local Model Adapter v1.0

Wraps LM Studio's OpenAI-compatible endpoint for the two active models:

  REASONER  mradermacher/Qwen3.5-35B-A3B-Claude-4.6-Opus-Reasoning-Distilled
            qwen35moe arch | Q4_K_M | 21.2 GB | 35B total / A3B active
            → deep security reasoning, isomorphism mapping, finding validation

  CODER     Melvin56/Qwen2.5-Coder-7B-Instruct-abliterated
            qwen2 arch | Q4_K_M | 4.7 GB
            → fast code review, PoC generation, remediation synthesis

Auto-discovers the loaded model IDs from /v1/models — never hardcodes stale
model strings that drift as LM Studio renames files.

CLI:
    python3 -m singularity_works.local_model_adapter health
    python3 -m singularity_works.local_model_adapter ask reasoner "what is SSRF?"
"""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Model identity — match by substring against /v1/models ids
# ---------------------------------------------------------------------------

class Models:
    # Substring fingerprints that identify each model in LM Studio's id field
    REASONER_FINGERPRINT = "qwen3.5-35b"    # matches the 35B-A3B MoE model
    CODER_FINGERPRINT    = "qwen2.5-coder"  # matches the 7B instruct model

    # Fallback explicit ids (used if auto-detect fails)
    REASONER_DEFAULT = "qwen3.5-35b-a3b-claude-4.6-opus-reasoning-distilled-i1"
    CODER_DEFAULT    = "qwen2.5-coder-7b-instruct-abliterated"

    # Role aliases accepted by complete()
    ALIASES = {
        "reasoner": REASONER_FINGERPRINT,
        "deep":     REASONER_FINGERPRINT,
        "35b":      REASONER_FINGERPRINT,
        "coder":    CODER_FINGERPRINT,
        "fast":     CODER_FINGERPRINT,
        "7b":       CODER_FINGERPRINT,
    }


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class CompletionResult:
    model: str
    content: str
    prompt_tokens: int    = 0
    completion_tokens: int = 0
    latency_ms: float     = 0.0
    error: str            = ""

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.content)


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class LocalModelAdapter:
    """
    Thin, dependency-free wrapper around LM Studio /v1/chat/completions.
    Auto-discovers actual model IDs from /v1/models on first use.
    Never raises — always returns CompletionResult (error field set on failure).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        timeout_s: int = 180,
        max_tokens: int = 2048,
        temperature: float = 0.15,
    ) -> None:
        self.base_url    = base_url.rstrip("/")
        self.timeout_s   = timeout_s
        self.max_tokens  = max_tokens
        self.temperature = temperature
        self._id_cache: dict[str, str] = {}   # fingerprint → resolved id

    # ── Model ID resolution ──────────────────────────────────────────────────

    def _resolve_id(self, name: str) -> str:
        """
        Map a role alias / fingerprint / explicit id → the id LM Studio actually uses.
        Queries /v1/models and matches by substring. Caches the result.
        """
        # Expand alias
        fingerprint = Models.ALIASES.get(name.lower(), name.lower())

        if fingerprint in self._id_cache:
            return self._id_cache[fingerprint]

        # Query /v1/models
        try:
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
                loaded_ids: list[str] = [m["id"] for m in data.get("data", [])]
        except Exception:
            loaded_ids = []

        # Find best match by substring
        for lid in loaded_ids:
            if fingerprint in lid.lower():
                self._id_cache[fingerprint] = lid
                return lid

        # Fallback: use the fingerprint as-is (LM Studio might accept it)
        fallback = (
            Models.REASONER_DEFAULT if fingerprint == Models.REASONER_FINGERPRINT
            else Models.CODER_DEFAULT if fingerprint == Models.CODER_FINGERPRINT
            else fingerprint
        )
        self._id_cache[fingerprint] = fallback
        return fallback

    # ── Core completion ──────────────────────────────────────────────────────

    def complete(
        self,
        model: str,
        prompt: str,
        *,
        system: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> CompletionResult:
        """
        Call LM Studio. Returns CompletionResult — never raises.
        `model` can be: "reasoner", "coder", "35b", "7b", or any partial id.
        """
        model_id = self._resolve_id(model)
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model":       model_id,
            "messages":    messages,
            "max_tokens":  max_tokens  or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            "stream":      False,
        }

        t0 = time.monotonic()
        try:
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw   = json.loads(resp.read())
                text  = raw["choices"][0]["message"]["content"]
                usage = raw.get("usage", {})
                return CompletionResult(
                    model=model_id,
                    content=text,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    latency_ms=(time.monotonic() - t0) * 1000,
                )
        except urllib.error.URLError as e:
            return CompletionResult(model=model_id, content="",
                error=f"LM Studio unreachable ({self.base_url}): {e.reason}",
                latency_ms=(time.monotonic() - t0) * 1000)
        except Exception as e:
            return CompletionResult(model=model_id, content="",
                error=str(e), latency_ms=(time.monotonic() - t0) * 1000)

    # ── Health check ─────────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        """
        Returns: {ok, url, loaded_models, resolved_ids, errors, ping_ms}
        """
        result: dict[str, Any] = {
            "ok": False, "url": self.base_url,
            "loaded_models": [], "resolved_ids": {}, "errors": [], "ping_ms": {},
        }
        # Step 1: list models
        try:
            req = urllib.request.Request(f"{self.base_url}/models",
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
                result["loaded_models"] = [m["id"] for m in data.get("data", [])]
        except Exception as e:
            result["errors"].append(
                f"Cannot reach {self.base_url}/models — start LM Studio and load both models. ({e})")
            return result

        # Step 2: resolve + ping each role
        for role, fp in [("reasoner", Models.REASONER_FINGERPRINT),
                         ("coder",    Models.CODER_FINGERPRINT)]:
            rid = self._resolve_id(fp)
            result["resolved_ids"][role] = rid
            cr = self.complete(fp, "Say OK", max_tokens=4, temperature=0.0)
            if cr.error:
                result["errors"].append(f"{role} ({rid}): {cr.error}")
            else:
                result["ping_ms"][role] = round(cr.latency_ms)

        result["ok"] = len(result["errors"]) == 0
        return result

    # ── Forge-specific wrappers ───────────────────────────────────────────────

    def review_code(self, code: str, context: str = "") -> CompletionResult:
        """CODER: fast security review pass."""
        sys = ("You are a security code reviewer. Be precise and concise. "
               "Report ONLY real vulnerabilities as: ISSUE: <type> at line <N>: <desc>. "
               "If clean: CLEAN")
        prompt = (f"{context}\n\n```\n{code}\n```" if context else f"```\n{code}\n```")
        return self.complete("coder", prompt, system=sys, temperature=0.05)

    def validate_finding(self, finding: str, code_ctx: str) -> CompletionResult:
        """REASONER: deep validation — real vuln or false positive?"""
        sys = ("You are a senior security researcher validating a SAST finding. "
               "Answer: (1) Real or false positive? (2) Exploitability? (3) Best remediation. "
               "Max 150 words. Be direct.")
        prompt = f"Finding: {finding}\n\nCode:\n```\n{code_ctx[:2000]}\n```"
        return self.complete("reasoner", prompt, system=sys, temperature=0.2)

    def generate_poc(self, vuln_type: str, code: str) -> CompletionResult:
        """CODER: write minimal PoC reproduction steps."""
        sys = "Write numbered PoC reproduction steps only. No preamble. 4-6 steps."
        prompt = f"Vulnerability: {vuln_type}\n\n```\n{code[:1500]}\n```"
        return self.complete("coder", prompt, system=sys, temperature=0.05)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_singleton: LocalModelAdapter | None = None

def get_adapter(base_url: str = "http://localhost:1234/v1") -> LocalModelAdapter:
    global _singleton
    if _singleton is None or _singleton.base_url != base_url:
        _singleton = LocalModelAdapter(base_url=base_url)
    return _singleton


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse, sys

    ap = argparse.ArgumentParser(description="Singularity Works — Local Model Adapter")
    sub = ap.add_subparsers(dest="cmd")

    hc = sub.add_parser("health", help="Check LM Studio + model connectivity")
    hc.add_argument("--url", default="http://localhost:1234/v1")

    ask = sub.add_parser("ask", help="Prompt a model")
    ask.add_argument("model", help="reasoner | coder | 35b | 7b")
    ask.add_argument("prompt")
    ask.add_argument("--url", default="http://localhost:1234/v1")
    ask.add_argument("--tokens", type=int, default=512)

    args = ap.parse_args()

    if args.cmd == "health":
        a = LocalModelAdapter(args.url)
        r = a.health_check()
        print(f"\nLM Studio — {args.url}")
        print(f"Status: {'OK' if r['ok'] else 'FAILED'}")
        print(f"Loaded models ({len(r['loaded_models'])}):")
        for m in r["loaded_models"]:
            print(f"  {m}")
        print("Resolved IDs:")
        for role, rid in r["resolved_ids"].items():
            ms = r["ping_ms"].get(role, "err")
            print(f"  {role:10s} → {rid}  [{ms}ms]")
        if r["errors"]:
            print("Errors:")
            for e in r["errors"]:
                print(f"  ✗ {e}")

    elif args.cmd == "ask":
        a = LocalModelAdapter(args.url)
        cr = a.complete(args.model, args.prompt, max_tokens=args.tokens)
        if cr.error:
            print(f"Error: {cr.error}", file=sys.stderr)
            sys.exit(1)
        print(cr.content)
        print(f"\n[{cr.model} | {cr.latency_ms:.0f}ms | {cr.completion_tokens} tokens]")

    else:
        ap.print_help()
