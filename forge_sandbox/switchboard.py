
MAPPING = {
    "command_exec_surface": "replace_command_exec",
    "dynamic_eval": "replace_dynamic_eval",
    "broken_auth_password_handling": "repair_password_handling",
    "nosql_where_injection": "repair_nosql_where_query",
    "unsafe_deserialization": "repair_unsafe_deserialization",
    "predictable_token_generation": "repair_predictable_token_generation",
    "ssrf_request_forwarding": "repair_ssrf_request_forwarding",
    "ssti_template_injection": "repair_ssti_template_injection",
    "fake_safety_wrapper": "quarantine_fake_wrapper",
    "broken_security_significant_fragment": "quarantine_broken_fragment",
    "novel_structured_unknown_language": "quarantine_unknown_representation",
    "unknown_semantic_risk": "quarantine_unknown_representation",
    "query_string_interpolation": "parameterize_query",
    "untrusted_get_input": "sanitize_file_input",
    "file_upload_surface": "validate_uploaded_file",
    "xss_reflected": "encode_output",
    "xss_stored": "encode_output_and_parameterize",
    "csrf_state_change": "validate_csrf_and_parameterize",
    "open_redirect": "constrain_redirect_target",
    "suspicious_unknown_representation": "quarantine_unknown_representation",
}
def run_switchboard(facts):
    candidates=[]
    for fact in facts:
        finding=fact.get("payload",{}).get("finding","")
        if finding in MAPPING:
            candidates.append({"candidate_kind":"transform","route":"transformer","axiom":MAPPING[finding],"payload":{"source_fact":fact}})
    return {"autonomy_tier":"guarded" if candidates else "review","route":candidates[0]["route"] if candidates else "orchestration","candidates":candidates}
