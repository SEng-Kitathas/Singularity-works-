from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .genome_detection_common import _Detection

def build_iris_prompt(content: str, language: str, vulnerability_hint: str = "") -> str:
    """
    Build the IRIS-style taint spec inference prompt.
    The REASONER returns JSON: { sources, sinks, sanitizers, assessment }
    """
    return f"""You are a security-focused static analyzer. Analyze the following {language} code.

Your task: identify taint flow vectors for security vulnerability detection.

Respond ONLY with JSON in this exact format:
{{
  "sources": [
    {{"name": "function_or_param_name", "type": "user_input|env|file|network", "line_hint": 0}}
  ],
  "sinks": [
    {{"name": "function_or_call", "type": "exec|query|network|deserialize|path|template|reflect", "line_hint": 0}}
  ],
  "sanitizers": [
    {{"name": "function_or_pattern", "type": "escape|validate|parameterize|allowlist"}}
  ],
  "assessment": {{
    "vulnerability_classes": ["list of CWE-style names if any"],
    "confidence": "high|medium|low",
    "reasoning": "brief explanation"
  }}
}}

{"Focus on: " + vulnerability_hint if vulnerability_hint else ""}

CODE:
```{language}
{content[:3000]}
```"""


@dataclass

class DynamicCapsule:
    """
    A runtime-generated genome capsule from IRIS-mode LLM inference.
    Treated identically to a static genome capsule during gate evaluation.
    """
    artifact_id: str
    language: str
    sources: list[dict]
    sinks: list[dict]
    sanitizers: list[dict]
    vulnerability_classes: list[str]
    confidence: str
    reasoning: str

    def to_detections(self, content: str) -> list[_Detection]:
        """
        Convert IRIS-inferred specs into detections by checking
        whether sources reach sinks without sanitizers in the content.
        """
        import re as _re
        detections: list[_Detection] = []

        # Build sets from inferred specs
        source_names = {s["name"] for s in self.sources}
        sink_names = {s["name"] for s in self.sinks}
        sanitizer_names = {s["name"] for s in self.sanitizers}

        # For each sink, check if a source flows into it without sanitizer
        for sink in self.sinks:
            sink_name = sink["name"]
            sink_type = sink.get("type", "unknown")

            # Find the sink call in content
            pattern = _re.compile(
                r'\b' + _re.escape(sink_name) + r'\s*\(',
                _re.IGNORECASE
            )
            for m in pattern.finditer(content):
                # Look backward 500 chars for source signals
                context = content[max(0, m.start() - 500):m.start() + 200]
                has_source = any(src in context for src in source_names)
                has_sanitizer = any(san in context for san in sanitizer_names)

                if has_source and not has_sanitizer:
                    line = content[:m.start()].count("\n") + 1
                    detections.append(_Detection(
                        lineno=line,
                        message=(
                            f"[IRIS] Taint flow at line {line}: "
                            f"user-controlled source reaches {sink_type} sink '{sink_name}' "
                            f"without sanitization â€” {', '.join(self.vulnerability_classes[:2]) or 'potential vulnerability'}"
                        ),
                        evidence={
                            "rewrite_candidate": f"Validate/escape all inputs before passing to {sink_name}",
                            "confidence": self.confidence,
                            "iris_reasoning": self.reasoning[:200],
                            "inferred_sources": [s["name"] for s in self.sources],
                            "inferred_sinks": [sink_name],
                        },
                    ))
                    break  # one detection per sink

        return detections



def _parse_iris_response(raw: str) -> dict | None:
    """Parse the REASONER's IRIS JSON response, tolerating markdown fences."""
    import re as _re, json as _json
    # Strip markdown fences if present
    raw = _re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=_re.MULTILINE)
    raw = _re.sub(r"```$", "", raw.strip(), flags=_re.MULTILINE)
    try:
        return _json.loads(raw.strip())
    except Exception:
        return None



def iris_escalate(
    content: str,
    artifact_id: str,
    language: str,
    semantic_ir: "Any | None",
    lm_base_url: str = "http://localhost:1234/v1",
    model: str = "qwen3.5-35b",
    vulnerability_hint: str = "",
) -> DynamicCapsule | None:
    """
    IRIS-mode escalation: call the local REASONER to infer taint specs
    when the static IR confidence is low. Returns a DynamicCapsule
    or None if the LLM is unavailable or returns invalid output.

    Called by the orchestrator when ir.confidence == "low" and
    gate_summary has no high/critical findings.
    """
    import json as _json
    try:
        import urllib.request as _req
        prompt = build_iris_prompt(content, language, vulnerability_hint)
        payload = _json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.1,
        }).encode()
        headers = {"Content-Type": "application/json"}
        request = _req.Request(
            f"{lm_base_url}/chat/completions",
            data=payload,
            headers=headers,
            method="POST",
        )
        with _req.urlopen(request, timeout=15) as resp:
            data = _json.loads(resp.read())
        raw = data["choices"][0]["message"]["content"]
        parsed = _parse_iris_response(raw)
        if not parsed:
            return None

        assessment = parsed.get("assessment", {})
        return DynamicCapsule(
            artifact_id=artifact_id,
            language=language,
            sources=parsed.get("sources", []),
            sinks=parsed.get("sinks", []),
            sanitizers=parsed.get("sanitizers", []),
            vulnerability_classes=assessment.get("vulnerability_classes", []),
            confidence=assessment.get("confidence", "medium"),
            reasoning=assessment.get("reasoning", ""),
        )
    except Exception:
        # Never let escalation failure break the forge â€” it's best-effort
        return None



# ---------------------------------------------------------------------------
# JWT Algorithm Confusion Detection
# CWE-347: Improper Verification of Cryptographic Signature
# Pattern: jwt.decode(token, secret) without algorithms= parameter
#          or with algorithms=["none"] / algorithms=["HS256"] with asymmetric key
# ---------------------------------------------------------------------------


