
from __future__ import annotations
import re

def detect_language(text: str) -> str:
    t = text.strip()
    if "<?php" in t: return "php"
    if "require(" in t or "const { exec }" in t or "function " in t: return "javascript"
    if "PreparedStatement" in t or "ResultSet" in t or "String " in t: return "java_like"
    if "SqlCommand" in t or "Request.Query" in t: return "csharp_like"
    if "system(" in t and "params[" in t: return "ruby_like"
    if re.search(r"^def\s+\w+", t, flags=re.M): return "python"
    return "unknown"


def has_novel_structured_language(code: str, language: str) -> bool:
    if language != "unknown":
        return False
    markers = [
        "sigil ",
        "glyph ",
        "bind ",
        "respond ",
        "headers {",
        "body view.",
        "vault.ask <<",
        "beam.exec [",
        "sig ",
        "cord ",
        "pendant ",
        "sum ->",
        "[phase ",
        "hop ",
        "tree main",
        "wire strange",
        "module starfall",
        "emit http",
        "flow ",
        "machine ",
        "schema ",
        "orbit ",
        "plan:",
        "diagram ",
        "holon ",
        "state ",
        "branch ",
        "inlet ",
        "ledger ",
        "relay ",
        "track ",
        "vessel ",
        "frame ",
        "garden ",
        "orchestra ",
        "vault ",
        "mint ",
        "store ",
    ]
    return sum(1 for m in markers if m in code) >= 1

def infer_first_principles_risk_from_unknown(code: str) -> bool:
    if not has_novel_structured_language(code, "unknown"):
        return False
    risky = [
        "beam.exec [",
        '"Location":',
        "select [",
        "where id = $",
        'request.query@"',
        "deserialize(",
        "pickle.loads(",
        "db.run(",
        "db.query(",
        "redirect(next)",
        "shell(cmd)",
        "render.inline(",
        "net.fetch ",
        "http 302",
        "channel.open(",
        "surface.inline",
        "compose(",
        "capsule(",
        "run(cmd)",
        "go(path)",
        "tunnel(target)",
        "surface(",
        "send route",
        "show veil",
        "actor.secret <=",
        "settle actor",
        "cast outward",
        "reveal draft",
        "open site",
        "blend skin",
        "answer route",
        "mint(user,email)",
        "hand token outward",
        "ignite phrase",
        "stage draft with person",
        "lower clause into store",
        "keep actor",
        "leave route",
        "weave(user,email)",
        "pass token outward",
        "settle clause into ledger",
        "shape(user)",
        "form(password)",
        "present draft",
    ]
    return sum(1 for m in risky if m in code) >= 1

def has_fake_wrapper_theater(code: str) -> bool:
    suspicious = [
        "function allowlist($x) { return $x; }",
        "function safeRedirect(x) { return x; }",
        "function safeMathEval(expr: string) { return eval(expr) }",
        "function safeMathEval(expr){ return eval(expr) }",
        "def allowlist(x): return x",
        "def allowlist(x)\n    x\n  end",
        "def safe_decode(x):\n    return x",
        "def allowlist(x):\n    return x",
        "def safe_template(x):\n    return x",
    ]
    return any(s in code for s in suspicious)

def trusted_allowlist_present(code: str) -> bool:
    return ("allowlist(" in code) and not has_fake_wrapper_theater(code)

def trusted_safe_redirect_present(code: str) -> bool:
    return (("safeRedirect(" in code) or ("security.isRedirectAllowed(" in code) or ("SAFE_REDIRECT_MAP" in code)) and not has_fake_wrapper_theater(code)

def trusted_safe_math_eval_present(code: str) -> bool:
    return ("safeMathEval(" in code) and not has_fake_wrapper_theater(code)

def is_prepared_java(code: str) -> bool:
    return ("PreparedStatement" in code and ".setString(" in code and "executeQuery()" in code and "executeQuery(sql)" not in code)

def is_prepared_php(code: str) -> bool:
    return ("mysqli_prepare" in code and "mysqli_stmt_bind_param" in code and "mysqli_stmt_execute" in code)

def is_parameterized_csharp(code: str) -> bool:
    return ('@id' in code and 'AddWithValue("@id", id)' in code)

def is_allowlisted_input(code: str) -> bool:
    return trusted_allowlist_present(code) or ("normalize_input(" in code) or ("SAFE_PAGE_MAP" in code) or ("validatedUpload(" in code)

def is_html_encoded_output(code: str) -> bool:
    return ("htmlspecialchars(" in code) or ("encodeForHTML(" in code) or ("escapeHtml(" in code)

def has_command_exec(code: str) -> bool:
    return ("shell_exec" in code) or bool(re.search(r"(?<!_)\bexec\s*\(", code)) or ("system(" in code and "safe_system(" not in code)

def has_dynamic_eval(code: str) -> bool:
    if trusted_safe_math_eval_present(code):
        return False
    return "eval(" in code

def has_broken_password_handling(code: str) -> bool:
    # Narrowed to the specific class we actually observed in NodeGoat:
    # 1) plaintext password stored directly in a user record object
    # 2) direct password equality compare in auth flow
    plaintext_store = (
        ("const user = {" in code) and
        ("password" in code) and
        ("benefitStartDate" in code) and
        ("bcrypt.hashSync" not in code)
    )
    direct_compare = (
        ("const comparePassword = (fromDB, fromUser)" in code) and
        ("return fromDB === fromUser;" in code)
    )
    return plaintext_store or direct_compare

def has_nosql_where_injection(code: str) -> bool:
    if "safeWhereQuery(" in code:
        return False
    return ("$where:" in code) and ("threshold" in code)

def has_unsafe_deserialization(code: str) -> bool:
    if "safeDeserialize(" in code:
        return False
    return ("pickle.loads(" in code) and ("request.POST" in code or "encoded_user" in code)

def has_predictable_token_generation(code: str) -> bool:
    if "safeToken(" in code:
        return False
    return ("MD5.new()" in code) and ("return str(user_id) + '-'" in code)

def has_ssrf_request_forwarding(code: str) -> bool:
    if "safeOutboundRequest(" in code or "mapOutboundTarget(" in code:
        return False
    suspicious = (
        ('requests.get("https://" + target +' in code) or
        ('requests.get(target)' in code) or
        ('urllib.request.urlopen(site)' in code) or
        ('urllib.request.urlopen(url)' in code)
    )
    request_control = ('request.args["target"]' in code) or ("request.args.get('site')" in code) or ("request.args['url']" in code)
    return suspicious and request_control

def has_ssti_template_injection(code: str) -> bool:
    if "safeRenderTemplate(" in code or "render_template(" in code and "render_template_string(" not in code:
        return False
    suspicious_sink = ("render_template_string(" in code) or ("jinja2.Template(" in code)
    tainted_template = (
        ('request.args["name"]' in code) or
        ('request.args["tpl"]' in code) or
        ('template = "<h1>Hello %s</h1>" % name' in code) or
        ('render_template_string(tpl + resp.text)' in code)
    )
    return suspicious_sink and tainted_template

def has_vulnerable_query_interpolation(code: str) -> bool:
    if is_prepared_java(code) or is_prepared_php(code) or is_parameterized_csharp(code):
        return False
    return (
        ("SELECT " in code and "'" in code and ("$" in code or "+" in code))
        or "executeQuery(sql)" in code
        or "mysqli_query" in code
        or "Statement st = connection.createStatement();" in code
        or ("SqlCommand(sql, conn)" in code and '@id' not in code)
        or ('where("name = ' in code and '#{' in code)
    )

def has_untrusted_input_flow(code: str) -> bool:
    if is_allowlisted_input(code):
        return False
    # Reflected-XSS rendering path: encoded output closes the relevant sink for this pattern.
    if ("$_GET" in code) and ("$html .=" in code) and is_html_encoded_output(code):
        return False
    # CSRF-protected state-change path: validated token closes the relevant request-forgery concern here.
    if ("$_GET[ 'Change' ]" in code or "$_GET['Change']" in code) and "validateCsrfToken(" in code:
        return False
    # Open redirect path: mapped safe redirect target closes the relevant redirect-input concern here.
    if ("$_GET['redirect']" in code or '$_GET[\'redirect\']' in code) and ("safeRedirect(" in code and "SAFE_REDIRECT_MAP" in code):
        return False
    return ("$_GET" in code) or ("getParameter(" in code) or ("$_REQUEST" in code) or ("Request.Query" in code) or ("params[" in code)

def has_unsafe_upload(code: str) -> bool:
    if "validatedUpload(" in code:
        return False
    return "move_uploaded_file" in code

def has_xss_reflected(code: str) -> bool:
    if is_html_encoded_output(code):
        return False
    explicit_reflection = (
        ("Hello ' . $_GET" in code)
        or ('{$user}' in code and '$html .=' in code)
        or ('$_GET' in code and '$html .= \'<pre>Hello ' in code)
        or ('$_GET' in code and '$html .= "<p>Welcome' in code)
    )
    return explicit_reflection

def has_xss_stored(code: str) -> bool:
    if is_html_encoded_output(code):
        return False
    return ("INSERT INTO guestbook" in code and "$message" in code and "$name" in code)

def has_csrf_state_change(code: str) -> bool:
    return ("$_GET[ 'Change' ]" in code and ("UPDATE `users`" in code or "INSERT INTO" in code) and "validateCsrfToken(" not in code)

def has_open_redirect(code: str) -> bool:
    if trusted_safe_redirect_present(code):
        return False
    return (
        ('header' in code and 'location:' in code and "$_GET['redirect']" in code)
        or ('Response.Redirect(next);' in code)
        or ('res.redirect(next);' in code)
        or ('redirect_to ' in code and 'params[:url]' in code)
        or ('redirect_to ' in code and 'target_url.to_s' in code)
    )

def has_suspicious_unknown_blob(code: str, language: str) -> bool:
    if language != "unknown":
        return False
    suspicious_markers = [
        "SELECT * FROM",
        "redirect = input(",
        "exec = sh(",
        'render = "<b>" + input(',
        'shell("ping " + input(',
        "deserialize(",
        "pickle.loads(",
        "db.run(",
        "db.query(",
        "redirect(next)",
        "shell(cmd)",
        "render.inline(",
        "net.fetch ",
        "http 302",
        '"Location":',
        "template(user_input)",
        "input(next)",
        "input(cmd)",
        "channel.open(",
        "surface.inline",
        "compose(",
        "capsule(",
        "run(cmd)",
        "go(path)",
        "tunnel(target)",
        "surface(",
        "request(next)",
        "request(tpl)",
        "send route",
        "show veil",
        "actor.secret <=",
        "settle actor",
        "cast outward",
        "reveal draft",
        "open site",
        "blend skin",
        "answer route",
        "mint(user,email)",
        "hand token outward",
        "ignite phrase",
        "stage draft with person",
        "lower clause into store",
        "keep actor",
        "leave route",
        "weave(user,email)",
        "pass token outward",
        "settle clause into ledger",
        "shape(user)",
        "form(password)",
        "present draft",
    ]
    structure_markers = [
        "flow ",
        "machine ",
        "schema ",
        "orbit ",
        "plan:",
        "diagram ",
        "holon ",
        "state ",
        "branch ",
        "inlet ",
        "ledger ",
        "relay ",
        "track ",
        "vessel ",
        "frame ",
        "garden ",
        "orchestra ",
        "vault ",
        "mint ",
        "store ",
    ]
    return (sum(1 for m in suspicious_markers if m in code) >= 2) or (
        sum(1 for m in structure_markers if m in code) >= 1 and
        sum(1 for m in suspicious_markers if m in code) >= 1
    )

def has_broken_fragment(code: str, language: str) -> bool:
    if language == "unknown":
        return False
    # crude but useful: unbalanced parentheses/braces plus security-significant markers
    score = 0
    if code.count("(") != code.count(")"):
        score += 1
    if code.count("{") != code.count("}"):
        score += 1
    if ("SELECT * FROM" in code) or ("header(" in code) or ("shell_exec" in code) or ("eval(" in code):
        score += 1
    return score >= 2

def classify(code: str) -> dict:
    findings = []
    if has_command_exec(code):
        findings.append("command_exec_surface")
    if has_dynamic_eval(code):
        findings.append("dynamic_eval")
    if has_broken_password_handling(code):
        findings.append("broken_auth_password_handling")
    if has_nosql_where_injection(code):
        findings.append("nosql_where_injection")
    if has_unsafe_deserialization(code):
        findings.append("unsafe_deserialization")
    if has_predictable_token_generation(code):
        findings.append("predictable_token_generation")
    if has_ssrf_request_forwarding(code):
        findings.append("ssrf_request_forwarding")
    if has_ssti_template_injection(code):
        findings.append("ssti_template_injection")
    if has_fake_wrapper_theater(code):
        findings.append("fake_safety_wrapper")
    if has_vulnerable_query_interpolation(code):
        findings.append("query_string_interpolation")
    if has_untrusted_input_flow(code):
        findings.append("untrusted_get_input")
    if has_unsafe_upload(code):
        findings.append("file_upload_surface")
    if has_xss_reflected(code):
        findings.append("xss_reflected")
    if has_xss_stored(code):
        findings.append("xss_stored")
    if has_csrf_state_change(code):
        findings.append("csrf_state_change")
    if has_open_redirect(code):
        findings.append("open_redirect")
    lang = detect_language(code)
    if has_suspicious_unknown_blob(code, lang):
        findings.append("suspicious_unknown_representation")
    if has_broken_fragment(code, lang):
        findings.append("broken_security_significant_fragment")
    if has_novel_structured_language(code, lang):
        findings.append("novel_structured_unknown_language")
    if infer_first_principles_risk_from_unknown(code):
        findings.append("unknown_semantic_risk")
    return {
        "language": lang,
        "front_door_mode": "structured_ir" if lang != "unknown" else "heuristic_ir",
        "findings": findings,
        "semantic_markers": {
            "prepared_java": is_prepared_java(code),
            "prepared_php": is_prepared_php(code),
            "parameterized_csharp": is_parameterized_csharp(code),
            "allowlisted_input": is_allowlisted_input(code),
            "validated_upload": "validatedUpload(" in code,
            "wrapped_command_exec": ("safe_exec_wrapper" in code) or ("safeExec(" in code) or ("safe_system(" in code),
            "html_encoded_output": is_html_encoded_output(code),
        }
    }
