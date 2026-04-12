from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CvssReference:
    score: float
    vector: str
    severity: str


_CVSS_MAP: dict[str, CvssReference] = {
    'nosql_injection': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'sql_injection': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'ssti_render_template': CvssReference(score=10.0, vector='AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H', severity='CRITICAL'),
    'ldap_injection': CvssReference(score=9.1, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N', severity='CRITICAL'),
    'unsafe_xml_parse': CvssReference(score=9.1, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:H', severity='CRITICAL'),
    'nosql': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'flask_debug': CvssReference(score=10.0, vector='AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H', severity='CRITICAL'),
    'sqlite_load_extension': CvssReference(score=9.0, vector='AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'dynamic_eval': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'shell_injection': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'subprocess_shell_true_string': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'unsafe_deserialization': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'yaml_load_no_loader': CvssReference(score=8.8, vector='AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H', severity='HIGH'),
    'marshal_loads': CvssReference(score=8.8, vector='AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H', severity='HIGH'),
    'user_url_to_network': CvssReference(score=9.1, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:H', severity='CRITICAL'),
    'ssrf': CvssReference(score=9.1, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:H', severity='CRITICAL'),
    'ssrf_confirmed': CvssReference(score=9.6, vector='AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:H', severity='CRITICAL'),
    'jwt_none_algorithm': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'jwt_algorithm_confusion': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'weak_jwt_secret': CvssReference(score=8.1, vector='AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='HIGH'),
    'unsigned_jwt': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'csrf_exempt': CvssReference(score=8.8, vector='AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H', severity='HIGH'),
    'cookie_missing_flags': CvssReference(score=6.1, vector='AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N', severity='MEDIUM'),
    'credential_literal': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'hardcoded_secret': CvssReference(score=9.8, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H', severity='CRITICAL'),
    'weak_rsa_key': CvssReference(score=7.5, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N', severity='HIGH'),
    'weak_cipher': CvssReference(score=7.5, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N', severity='HIGH'),
    'unverified_ssl_context': CvssReference(score=7.4, vector='AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N', severity='HIGH'),
    'broken_ssl_tls_version': CvssReference(score=7.5, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N', severity='HIGH'),
    'missing_object_ownership': CvssReference(score=8.8, vector='AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N', severity='HIGH'),
    'idor': CvssReference(score=8.8, vector='AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N', severity='HIGH'),
    'open_redirect': CvssReference(score=6.1, vector='AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N', severity='MEDIUM'),
    'cors_wildcard': CvssReference(score=8.2, vector='AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:L/A:N', severity='HIGH'),
    'zip_slip': CvssReference(score=8.1, vector='AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N', severity='HIGH'),
    'csv_injection': CvssReference(score=8.0, vector='AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:N', severity='HIGH'),
    'trojan_source': CvssReference(score=8.3, vector='AV:N/AC:H/PR:N/UI:R/S:C/C:H/I:H/A:N', severity='HIGH'),
    'http_request_smuggling': CvssReference(score=9.0, vector='AV:N/AC:H/PR:N/UI:N/S:C/C:H/I:H/A:N', severity='CRITICAL'),
    'decompression_bomb': CvssReference(score=7.5, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H', severity='HIGH'),
    'user_input_in_response_header': CvssReference(score=6.1, vector='AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N', severity='MEDIUM'),
    '_default': CvssReference(score=5.0, vector='AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N', severity='MEDIUM'),
}


_CWE_MAP: dict[str, str] = {
    'nosql': 'CWE-943: Improper Neutralization of Special Elements in Data Query Logic',
    'sql': 'CWE-89: Improper Neutralization of Special Elements used in an SQL Command',
    'ssti': 'CWE-1336: Improper Neutralization of Special Elements Used in a Template Engine',
    'ldap': 'CWE-90: Improper Neutralization of Special Elements used in an LDAP Query',
    'xxe': 'CWE-611: Improper Restriction of XML External Entity Reference',
    'eval': 'CWE-78: Improper Neutralization of Special Elements used in an OS Command',
    'shell': 'CWE-78: Improper Neutralization of Special Elements used in an OS Command',
    'subprocess': 'CWE-78: Improper Neutralization of Special Elements used in an OS Command',
    'deserialization': 'CWE-502: Deserialization of Untrusted Data',
    'yaml': 'CWE-502: Deserialization of Untrusted Data',
    'ssrf': 'CWE-918: Server-Side Request Forgery (SSRF)',
    'jwt': 'CWE-347: Improper Verification of Cryptographic Signature',
    'hardcoded': 'CWE-798: Use of Hard-coded Credentials',
    'credential': 'CWE-798: Use of Hard-coded Credentials',
    'csrf': 'CWE-352: Cross-Site Request Forgery (CSRF)',
    'idor': 'CWE-639: Authorization Bypass Through User-Controlled Key',
    'ownership': 'CWE-639: Authorization Bypass Through User-Controlled Key',
    'redirect': "CWE-601: URL Redirection to Untrusted Site ('Open Redirect')",
    'cors': 'CWE-942: Permissive Cross-domain Policy with Untrusted Domains',
    'cookie': "CWE-614: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute",
    'rsa': 'CWE-326: Inadequate Encryption Strength',
    'cipher': 'CWE-327: Use of a Broken or Risky Cryptographic Algorithm',
    'tls': 'CWE-326: Inadequate Encryption Strength',
    'zip': 'CWE-22: Improper Limitation of a Pathname to a Restricted Directory',
    'path': 'CWE-22: Improper Limitation of a Pathname to a Restricted Directory',
    'csv': 'CWE-1236: Improper Neutralization of Formula Elements in a CSV File',
    'trojan': 'CWE-1007: Insufficient Visual Distinction of Homoglyphs',
    'smuggling': "CWE-444: Inconsistent Interpretation of HTTP Requests ('HTTP Request Smuggling')",
    'decompression': 'CWE-409: Improper Handling of Highly Compressed Data (Data Amplification)',
    'debug': "CWE-94: Improper Control of Generation of Code ('Code Injection')",
}
