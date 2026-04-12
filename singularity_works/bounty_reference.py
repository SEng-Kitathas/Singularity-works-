from __future__ import annotations
from typing import Any


_CVSS_MAP: dict[str, dict[str, Any]] = {
    # injection family
    "nosql_injection":              {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "sql_injection":                {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "ssti_render_template":         {"score": 10.0,"vector": "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", "severity": "CRITICAL"},
    "ldap_injection":               {"score": 9.1, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N", "severity": "CRITICAL"},
    "unsafe_xml_parse":             {"score": 9.1, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:H", "severity": "CRITICAL"},
    "nosql":                        {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    # execution
    "flask_debug":                  {"score": 10.0,"vector": "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", "severity": "CRITICAL"},
    "sqlite_load_extension":        {"score": 9.0, "vector": "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "dynamic_eval":                 {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "shell_injection":              {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "subprocess_shell_true_string": {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    # serialization / deserialization
    "unsafe_deserialization":       {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "yaml_load_no_loader":          {"score": 8.8, "vector": "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", "severity": "HIGH"},
    "marshal_loads":                {"score": 8.8, "vector": "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", "severity": "HIGH"},
    # network / SSRF
    "user_url_to_network":          {"score": 9.1, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:H", "severity": "CRITICAL"},
    "ssrf":                         {"score": 9.1, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:H", "severity": "CRITICAL"},
    "ssrf_confirmed":               {"score": 9.6, "vector": "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:H", "severity": "CRITICAL"},
    # auth
    "jwt_none_algorithm":           {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "jwt_algorithm_confusion":      {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "weak_jwt_secret":              {"score": 8.1, "vector": "AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "HIGH"},
    "unsigned_jwt":                 {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "csrf_exempt":                  {"score": 8.8, "vector": "AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H", "severity": "HIGH"},
    "cookie_missing_flags":         {"score": 6.1, "vector": "AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", "severity": "MEDIUM"},
    # crypto
    "credential_literal":           {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "hardcoded_secret":             {"score": 9.8, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "severity": "CRITICAL"},
    "weak_rsa_key":                 {"score": 7.5, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", "severity": "HIGH"},
    "weak_cipher":                  {"score": 7.5, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", "severity": "HIGH"},
    "unverified_ssl_context":       {"score": 7.4, "vector": "AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N", "severity": "HIGH"},
    "broken_ssl_tls_version":       {"score": 7.5, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", "severity": "HIGH"},
    # access control
    "missing_object_ownership":     {"score": 8.8, "vector": "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N", "severity": "HIGH"},
    "idor":                         {"score": 8.8, "vector": "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N", "severity": "HIGH"},
    "open_redirect":                {"score": 6.1, "vector": "AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", "severity": "MEDIUM"},
    "cors_wildcard":                {"score": 8.2, "vector": "AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:L/A:N", "severity": "HIGH"},
    # injection / misc
    "zip_slip":                     {"score": 8.1, "vector": "AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N", "severity": "HIGH"},
    "csv_injection":                {"score": 8.0, "vector": "AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:N", "severity": "HIGH"},
    "trojan_source":                {"score": 8.3, "vector": "AV:N/AC:H/PR:N/UI:R/S:C/C:H/I:H/A:N", "severity": "HIGH"},
    "http_request_smuggling":       {"score": 9.0, "vector": "AV:N/AC:H/PR:N/UI:N/S:C/C:H/I:H/A:N", "severity": "CRITICAL"},
    "decompression_bomb":           {"score": 7.5, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H", "severity": "HIGH"},
    "user_input_in_response_header":{"score": 6.1, "vector": "AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", "severity": "MEDIUM"},
    # default
    "_default":                     {"score": 5.0, "vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N", "severity": "MEDIUM"},
}


def _cvss_for_finding(finding_code: str, gate_family: str) -> dict[str, Any]:
    """Look up CVSS data by finding code or gate family."""
    code_lower = finding_code.lower().replace("-", "_")
    family_lower = gate_family.lower().replace("-", "_")
    for key, data in _CVSS_MAP.items():
        if key in code_lower or key in family_lower:
            return data
    return _CVSS_MAP["_default"]


# ---------------------------------------------------------------------------
# CWE mapping
# ---------------------------------------------------------------------------

_CWE_MAP: dict[str, str] = {
    "nosql":           "CWE-943: Improper Neutralization of Special Elements in Data Query Logic",
    "sql":             "CWE-89: Improper Neutralization of Special Elements used in an SQL Command",
    "ssti":            "CWE-1336: Improper Neutralization of Special Elements Used in a Template Engine",
    "ldap":            "CWE-90: Improper Neutralization of Special Elements used in an LDAP Query",
    "xxe":             "CWE-611: Improper Restriction of XML External Entity Reference",
    "eval":            "CWE-78: Improper Neutralization of Special Elements used in an OS Command",
    "shell":           "CWE-78: Improper Neutralization of Special Elements used in an OS Command",
    "subprocess":      "CWE-78: Improper Neutralization of Special Elements used in an OS Command",
    "deserialization": "CWE-502: Deserialization of Untrusted Data",
    "yaml":            "CWE-502: Deserialization of Untrusted Data",
    "ssrf":            "CWE-918: Server-Side Request Forgery (SSRF)",
    "jwt":             "CWE-347: Improper Verification of Cryptographic Signature",
    "hardcoded":       "CWE-798: Use of Hard-coded Credentials",
    "credential":      "CWE-798: Use of Hard-coded Credentials",
    "csrf":            "CWE-352: Cross-Site Request Forgery (CSRF)",
    "idor":            "CWE-639: Authorization Bypass Through User-Controlled Key",
    "ownership":       "CWE-639: Authorization Bypass Through User-Controlled Key",
    "redirect":        "CWE-601: URL Redirection to Untrusted Site ('Open Redirect')",
    "cors":            "CWE-942: Permissive Cross-domain Policy with Untrusted Domains",
    "cookie":          "CWE-614: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute",
    "rsa":             "CWE-326: Inadequate Encryption Strength",
    "cipher":          "CWE-327: Use of a Broken or Risky Cryptographic Algorithm",
    "tls":             "CWE-326: Inadequate Encryption Strength",
    "zip":             "CWE-22: Improper Limitation of a Pathname to a Restricted Directory",
    "path":            "CWE-22: Improper Limitation of a Pathname to a Restricted Directory",
    "csv":             "CWE-1236: Improper Neutralization of Formula Elements in a CSV File",
    "trojan":          "CWE-1007: Insufficient Visual Distinction of Homoglyphs",
    "smuggling":       "CWE-444: Inconsistent Interpretation of HTTP Requests ('HTTP Request Smuggling')",
    "decompression":   "CWE-409: Improper Handling of Highly Compressed Data (Data Amplification)",
    "debug":           "CWE-94: Improper Control of Generation of Code ('Code Injection')",
}


def _cwe_for(finding_code: str, message: str) -> str:
    text = (finding_code + " " + message).lower()
    for key, cwe in _CWE_MAP.items():
        if key in text:
            return cwe
    return "CWE-693: Protection Mechanism Failure"


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

