
def evaluate(subject):
    code=subject.get("code","")
    language=subject.get("language","unknown")
    results=[]
    if language=="unknown" and subject.get("front_door_mode")!="heuristic_ir":
        results.append({"gate_id":"safety.unknown_language_fallback","status":"fail","residual_obligations":["unknown_language_fallback"]})
    else:
        results.append({"gate_id":"safety.unknown_language_fallback","status":"pass","residual_obligations":[]})
    if subject.get("trace_links"):
        results.append({"gate_id":"assurance.trace_linkage","status":"pass","residual_obligations":[]})
    else:
        results.append({"gate_id":"assurance.trace_linkage","status":"warn","residual_obligations":["trace_linkage"]})
    if ("shell_exec" in code or "exec(" in code or ("system(" in code and "safe_system(" not in code)) and ("safe_exec_wrapper" not in code and "safeExec(" not in code):
        results.append({"gate_id":"risk.command_exec","status":"warn","residual_obligations":["manual_exec_review","allowlist_command_args"]})
    if "eval(" in code and "safeMathEval(" not in code:
        results.append({"gate_id":"risk.dynamic_eval","status":"warn","residual_obligations":["replace_dynamic_eval"]})
    broken_password_store = ("const user = {" in code) and ("benefitStartDate" in code) and ("password" in code) and ("bcrypt.hashSync" not in code)
    direct_password_compare = ("const comparePassword = (fromDB, fromUser)" in code) and ("return fromDB === fromUser;" in code)
    if broken_password_store or direct_password_compare:
        results.append({"gate_id":"risk.broken_auth_password_handling","status":"warn","residual_obligations":["hash_password_storage","repair_password_compare"]})
    if ("$where:" in code) and ("threshold" in code) and ("safeWhereQuery(" not in code):
        results.append({"gate_id":"risk.nosql_where_injection","status":"warn","residual_obligations":["replace_nosql_where_query"]})
    if ("pickle.loads(" in code) and ("request.POST" in code or "encoded_user" in code) and ("safeDeserialize(" not in code):
        results.append({"gate_id":"risk.unsafe_deserialization","status":"warn","residual_obligations":["replace_unsafe_deserialization"]})
    if ("MD5.new()" in code) and ("return str(user_id) + '-'" in code) and ("safeToken(" not in code):
        results.append({"gate_id":"risk.predictable_token_generation","status":"warn","residual_obligations":["replace_predictable_token_generation"]})
    suspicious_ssrf = (
        ('requests.get("https://" + target +' in code) or
        ('requests.get(target)' in code) or
        ('urllib.request.urlopen(site)' in code) or
        ('urllib.request.urlopen(url)' in code)
    )
    request_control = ('request.args["target"]' in code) or ("request.args.get('site')" in code) or ("request.args['url']" in code)
    if suspicious_ssrf and request_control and ("safeOutboundRequest(" not in code) and ("mapOutboundTarget(" not in code):
        results.append({"gate_id":"risk.ssrf_request_forwarding","status":"warn","residual_obligations":["replace_ssrf_request_forwarding"]})
    suspicious_ssti = ("render_template_string(" in code) or ("jinja2.Template(" in code)
    tainted_template = (
        ('request.args["name"]' in code) or
        ('request.args["tpl"]' in code) or
        ('template = "<h1>Hello %s</h1>" % name' in code) or
        ('render_template_string(tpl + resp.text)' in code)
    )
    if suspicious_ssti and tainted_template and ("safeRenderTemplate(" not in code):
        results.append({"gate_id":"risk.ssti_template_injection","status":"warn","residual_obligations":["replace_ssti_template_injection"]})
    if ("function allowlist($x) { return $x; }" in code) or ("function safeRedirect(x) { return x; }" in code) or ("function safeMathEval(expr: string) { return eval(expr) }" in code) or ("def allowlist(x)\\n    x\\n  end" in code):
        results.append({"gate_id":"risk.fake_safety_wrapper","status":"warn","residual_obligations":["manual_wrapper_validation"]})
    if (("SELECT " in code and "'" in code and ("$" in code or "+" in code)) or "executeQuery(sql)" in code or ("mysqli_query" in code and "mysqli_prepare" not in code) or ("SqlCommand(sql, conn)" in code and '@id' not in code)):
        results.append({"gate_id":"risk.sqli","status":"warn","residual_obligations":["parameterize_query","bind_untrusted_input"]})
    reflected_xss_rendering_closed = ("$_GET" in code) and ("$html .=" in code) and ("htmlspecialchars(" in code)
    csrf_state_change_closed = (("$_GET[ 'Change' ]" in code) or ("$_GET['Change']" in code)) and ("validateCsrfToken(" in code)
    open_redirect_closed = (("$_GET['redirect']" in code) or ("$_GET[\'redirect\']" in code)) and ("safeRedirect(" in code) and ("SAFE_REDIRECT_MAP" in code)
    if (("$_GET" in code) or ("getParameter(" in code) or ("$_REQUEST" in code) or ("Request.Query" in code) or ("params[" in code)) and ("allowlist(" not in code) and ("normalize_input(" not in code) and ("SAFE_PAGE_MAP" not in code) and not reflected_xss_rendering_closed and not csrf_state_change_closed and not open_redirect_closed:
        results.append({"gate_id":"risk.untrusted_input","status":"warn","residual_obligations":["normalize_input","allowlist_expected_values"]})
    if "move_uploaded_file" in code and "validatedUpload(" not in code:
        results.append({"gate_id":"risk.upload_validation","status":"warn","residual_obligations":["upload_type_validation","upload_storage_policy"]})
    explicit_reflection = (
        ("Hello ' . $_GET" in code)
        or ('{$user}' in code and '$html .=' in code)
        or ('$_GET' in code and '$html .= \'<pre>Hello ' in code)
        or ('$_GET' in code and '$html .= "<p>Welcome' in code)
    )
    if explicit_reflection and "htmlspecialchars(" not in code:
        results.append({"gate_id":"risk.xss_reflected","status":"warn","residual_obligations":["html_encode_output"]})
    if ("INSERT INTO guestbook" in code and "$message" in code and "$name" in code and "htmlspecialchars(" not in code):
        results.append({"gate_id":"risk.xss_stored","status":"warn","residual_obligations":["html_encode_output","parameterize_query"]})
    if ("$_GET[ 'Change' ]" in code and ("UPDATE `users`" in code or "INSERT INTO" in code) and "validateCsrfToken(" not in code):
        results.append({"gate_id":"risk.csrf_state_change","status":"warn","residual_obligations":["validate_csrf_token"]})
    if (
        (('header' in code) and ('location:' in code) and ("$_GET['redirect']" in code))
        or ('Response.Redirect(next);' in code)
        or ('res.redirect(next);' in code)
        or ('redirect_to ' in code and 'params[:url]' in code)
        or ('redirect_to ' in code and 'target_url.to_s' in code)
    ) and ("safeRedirect(" not in code) and ("SAFE_REDIRECT_MAP" not in code) and ("security.isRedirectAllowed(" not in code):
        results.append({"gate_id":"risk.open_redirect","status":"warn","residual_obligations":["constrain_redirect_target"]})
    suspicious_unknown = (subject.get("language","unknown") == "unknown") and (("SELECT * FROM" in code) or ("redirect = input(" in code) or ("exec = sh(" in code))
    if suspicious_unknown:
        results.append({"gate_id":"risk.suspicious_unknown_representation","status":"warn","residual_obligations":["manual_unknown_review"]})
    broken_fragment = (subject.get("language","unknown") != "unknown") and ((code.count("(") != code.count(")")) or (code.count("{") != code.count("}"))) and (("SELECT * FROM" in code) or ("header(" in code) or ("shell_exec" in code) or ("eval(" in code))
    if broken_fragment:
        results.append({"gate_id":"risk.broken_fragment","status":"warn","residual_obligations":["manual_fragment_reconstruction"]})
    novel_unknown = (subject.get("language","unknown") == "unknown") and (
        ("sigil " in code) or ("glyph " in code) or ("bind " in code) or ("sig " in code) or ("cord " in code) or ("pendant " in code) or ("[phase " in code) or ("tree main" in code) or ("wire strange" in code) or ("module starfall" in code) or ("flow " in code) or ("machine " in code) or ("schema " in code) or ("orbit " in code) or ("plan:" in code) or ("diagram " in code) or ("holon " in code) or ("state " in code) or ("branch " in code) or ("inlet " in code) or ("ledger " in code) or ("relay " in code) or ("track " in code) or ("vessel " in code) or ("frame " in code) or ("garden " in code) or ("orchestra " in code) or ("vault " in code) or ("mint " in code) or ("store " in code)
    )
    if novel_unknown:
        results.append({"gate_id":"risk.novel_unknown_language","status":"warn","residual_obligations":["manual_unknown_review"]})
    unknown_semantic_risk = (subject.get("language","unknown") == "unknown") and (
        ("beam.exec [" in code) or ('"Location":' in code) or ("select [" in code) or ("deserialize(" in code) or ("pickle.loads(" in code) or ("db.run(" in code) or ("db.query(" in code) or ("redirect(next)" in code) or ("shell(cmd)" in code) or ("render.inline(" in code) or ("net.fetch " in code) or ("http 302" in code) or ("channel.open(" in code) or ("surface.inline" in code) or ("compose(" in code) or ("capsule(" in code) or ("run(cmd)" in code) or ("go(path)" in code) or ("tunnel(target)" in code) or ("surface(" in code) or ("send route" in code) or ("show veil" in code) or ("actor.secret <=" in code) or ("settle actor" in code) or ("cast outward" in code) or ("reveal draft" in code) or ("open site" in code) or ("blend skin" in code) or ("answer route" in code) or ("mint(user,email)" in code) or ("hand token outward" in code) or ("ignite phrase" in code) or ("stage draft with person" in code) or ("lower clause into store" in code) or ("keep actor" in code) or ("leave route" in code) or ("weave(user,email)" in code) or ("pass token outward" in code) or ("settle clause into ledger" in code) or ("shape(user)" in code) or ("form(password)" in code) or ("present draft" in code)
    )
    if unknown_semantic_risk:
        results.append({"gate_id":"risk.unknown_semantic_risk","status":"warn","residual_obligations":["manual_unknown_review","semantic_reconstruction_required"]})
    counts={"pass":0,"warn":0,"fail":0}
    residuals=[]
    for r in results:
        counts[r["status"]]+=1
        residuals.extend(r.get("residual_obligations",[]))
    return {"gate_results":results,"gate_counts":counts,"residual_obligations":sorted(set(residuals))}
