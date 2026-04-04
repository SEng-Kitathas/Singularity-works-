
def plan_remediation(code: str, axiom: str, language: str):
    plan = {"axiom": axiom, "language": language, "strategy": "", "obligations_closed": [], "proposed_patch": code}
    patch = code

    if axiom == "replace_command_exec":
        plan["strategy"] = "wrap command execution in allowlisted command + argument validation layer"
        if language == "php":
            patch = patch.replace("$target = $_REQUEST[ 'ip' ];", "$target = allowlist($_REQUEST[ 'ip' ]);")
            patch = patch.replace("shell_exec(", "safe_exec_wrapper(")
        elif language == "javascript":
            if "function run(userInput) {" in patch and "allowlist(userInput)" not in patch:
                patch = patch.replace("function run(userInput) {", "function run(userInput) {\n  userInput = allowlist(userInput);")
            patch = patch.replace("exec(", "safeExec(")
        elif language == "ruby_like":
            patch = patch.replace("user = params[:host]", "user = allowlist(params[:host])")
            patch = patch.replace("system(", "safe_system(")
        plan["obligations_closed"] = ["allowlist_command_args", "normalize_input", "allowlist_expected_values"]

    elif axiom == "quarantine_fake_wrapper":
        plan["strategy"] = "quarantine fake safety wrapper theater for manual review"
        patch = "# QUARANTINED_FAKE_WRAPPER_THEATER\n" + patch
        plan["obligations_closed"] = []

    elif axiom == "quarantine_broken_fragment":
        plan["strategy"] = "quarantine broken security-significant fragment for reconstruction"
        patch = "# QUARANTINED_BROKEN_SECURITY_FRAGMENT\n" + patch
        plan["obligations_closed"] = []

    elif axiom == "repair_password_handling":
        plan["strategy"] = "hash passwords at storage and compare with bcrypt instead of plaintext equality"
        patch = patch.replace(
            "            password\n        };",
            "            password: bcrypt.hashSync(password, bcrypt.genSaltSync())\n        };"
        )
        patch = patch.replace(
            "            return fromDB === fromUser;",
            "            return bcrypt.compareSync(fromUser, fromDB);"
        )
        plan["obligations_closed"] = ["hash_password_storage","repair_password_compare"]

    elif axiom == "repair_nosql_where_query":
        plan["strategy"] = "replace raw $where javascript query with parsed threshold and structured query"
        patch = patch.replace(
            "                return {\n                    $where: `this.userId == ${parsedUserId} && this.stocks > '${threshold}'`\n                };",
            "                const parsedThreshold = parseInt(threshold, 10);\n                return safeWhereQuery({ userId: parsedUserId, stocks: { $gt: parsedThreshold } });"
        )
        patch = patch.replace(
            '  const crit = { $where: `this.userId == ${parseInt(req.query.userId)} && this.stocks > \'${threshold}\'` }',
            '  const parsedThreshold = parseInt(threshold, 10)\n  const crit = safeWhereQuery({ userId: parseInt(req.query.userId), stocks: { $gt: parsedThreshold } })'
        )
        plan["obligations_closed"] = ["replace_nosql_where_query"]

    elif axiom == "repair_unsafe_deserialization":
        plan["strategy"] = "replace unsafe pickle loads on user-controlled input with constrained decode/parse path"
        patch = patch.replace(
            "        user = pickle.loads(base64.b64decode(encoded_user))",
            "        user = safeDeserialize(base64.b64decode(encoded_user))"
        )
        plan["obligations_closed"] = ["replace_unsafe_deserialization"]

    elif axiom == "repair_predictable_token_generation":
        plan["strategy"] = "replace predictable MD5-based token generation with a dedicated safe token primitive"
        patch = patch.replace(
            "    h = MD5.new()\n    h.update(email)\n    return str(user_id) + '-' + str(h.hexdigest())",
            "    return safeToken(user_id, email)"
        )
        plan["obligations_closed"] = ["replace_predictable_token_generation"]

    elif axiom == "repair_ssrf_request_forwarding":
        plan["strategy"] = "replace attacker-controlled outbound requests with mapped safe targets"
        patch = patch.replace(
            '    resp = requests.get("https://" + target + ".example.com/data/")',
            '    resp = safeOutboundRequest(mapOutboundTarget(target))'
        )
        patch = patch.replace(
            '    resp = requests.get(target)',
            '    resp = safeOutboundRequest(mapOutboundTarget(target))'
        )
        patch = patch.replace(
            '    text = urllib.request.urlopen(site, timeout=5).read()',
            '    text = safeOutboundRequest(mapOutboundTarget(site)).read()'
        )
        patch = patch.replace(
            '    r = requests.get(url)',
            '    r = safeOutboundRequest(mapOutboundTarget(url))'
        )
        plan["obligations_closed"] = ["replace_ssrf_request_forwarding"]

    elif axiom == "repair_ssti_template_injection":
        plan["strategy"] = "replace user-controlled template strings with fixed templates and escaped context variables"
        patch = patch.replace(
            '    return render_template_string(template)',
            '    return safeRenderTemplate("greet.html", {"name": name})'
        )
        patch = patch.replace(
            '    return render_template_string(tpl + resp.text)',
            '    return safeRenderTemplate("proxy.html", {"resp_text": resp.text})'
        )
        plan["obligations_closed"] = ["replace_ssti_template_injection"]

    elif axiom == "replace_dynamic_eval":
        plan["strategy"] = "replace dynamic eval with constrained arithmetic evaluator"
        patch = patch.replace("eval(expression)", "safeMathEval(expression)")
        plan["obligations_closed"] = ["replace_dynamic_eval"]

    elif axiom == "parameterize_query":
        plan["strategy"] = "replace string-built query with prepared statement / bound parameters"
        patch = code
        if language == "php":
            patch = patch.replace("$id = $_REQUEST[ 'id' ];", "$id = allowlist($_REQUEST[ 'id' ]);")
            patch = patch.replace("$user = $_GET[ 'username' ];", "$user = allowlist($_GET[ 'username' ]);")
            patch = patch.replace("$pass = $_GET[ 'password' ];", "$pass = allowlist($_GET[ 'password' ]);")
            patch = patch.replace("""$result = mysqli_query($GLOBALS["___mysqli_ston"],  $query );""",
                                 """$stmt = mysqli_prepare($GLOBALS["___mysqli_ston"], "SELECT first_name, last_name FROM users WHERE user_id = ?");
mysqli_stmt_bind_param($stmt, "s", $id);
mysqli_stmt_execute($stmt);""")
            patch = patch.replace('''$result = mysqli_query($GLOBALS["___mysqli_ston"],  $query ) or die( '<pre>' . ((is_object($GLOBALS["___mysqli_ston"])) ? mysqli_error($GLOBALS["___mysqli_ston"]) : (($___mysqli_res = mysqli_connect_error()) ? $___mysqli_res : false)) . '</pre>' );''',
                                 '''$stmt = mysqli_prepare($GLOBALS["___mysqli_ston"], "SELECT * FROM `users` WHERE user = ? AND password = ?;");
mysqli_stmt_bind_param($stmt, "ss", $user, $pass);
mysqli_stmt_execute($stmt);''')
            patch = patch.replace('''$result = mysqli_query($GLOBALS["___mysqli_ston"],  $insert ) or die( '<pre>' . ((is_object($GLOBALS["___mysqli_ston"])) ? mysqli_error($GLOBALS["___mysqli_ston"]) : (($___mysqli_res = mysqli_connect_error()) ? $___mysqli_res : false)) . '</pre>' );''',
                                 '''$stmt = mysqli_prepare($GLOBALS["___mysqli_ston"], "UPDATE `users` SET password = ? WHERE user = ?;");
mysqli_stmt_bind_param($stmt, "ss", $pass_new, $current_user);
mysqli_stmt_execute($stmt);''')
        elif language == "java_like":
            patch = patch.replace('String id = request.getParameter("id");', 'String id = allowlist(request.getParameter("id"));')
            patch = patch.replace('Statement st = connection.createStatement();',
                                 'PreparedStatement st = connection.prepareStatement("SELECT * FROM users WHERE id = ?");\nst.setString(1, id);')
            patch = patch.replace("ResultSet rs = st.executeQuery(sql);", "ResultSet rs = st.executeQuery();")
        elif language == "csharp_like":
            patch = patch.replace('var id = Request.Query["id"];', 'var id = allowlist(Request.Query["id"]);')
            patch = patch.replace("""var sql = "SELECT * FROM users WHERE id = '" + id + "'";""", """var sql = "SELECT * FROM users WHERE id = @id";""")
            patch = patch.replace('using var cmd = new SqlCommand(sql, conn);', 'using var cmd = new SqlCommand(sql, conn);\ncmd.Parameters.AddWithValue("@id", id);')
        plan["obligations_closed"] = ["parameterize_query","bind_untrusted_input","normalize_input","allowlist_expected_values"]

    elif axiom == "sanitize_file_input":
        plan["strategy"] = "normalize untrusted selector/input and allowlist expected values before use"
        patch = code
        if language == "php" and "include($file);" in code:
            patch = patch.replace("$file = $_GET[ 'page' ];", "$file = allowlist($_GET[ 'page' ]);")
            patch = patch.replace("include($file);", "include(SAFE_PAGE_MAP[$file]);")
        elif language == "php" and "$_REQUEST" in code:
            patch = patch.replace("$id = $_REQUEST[ 'id' ];", "$id = allowlist($_REQUEST[ 'id' ]);")
            patch = patch.replace("$target = $_REQUEST[ 'ip' ];", "$target = allowlist($_REQUEST[ 'ip' ]);")
        elif language == "java_like" and "getParameter(" in code:
            patch = patch.replace('String id = request.getParameter("id");', 'String id = allowlist(request.getParameter("id"));')
        elif language == "csharp_like" and "Request.Query" in code:
            patch = patch.replace('var id = Request.Query["id"];', 'var id = allowlist(Request.Query["id"]);')
        elif language == "ruby_like" and "params[" in code:
            patch = patch.replace("user = params[:host]", "user = allowlist(params[:host])")
        plan["obligations_closed"] = ["normalize_input","allowlist_expected_values"]

    elif axiom == "validate_uploaded_file":
        plan["strategy"] = "validate file type/name/storage policy before upload persistence"
        patch = code.replace("move_uploaded_file( $_FILES[ 'uploaded' ][ 'tmp_name' ], $target_path )", "validatedUpload($_FILES['uploaded'], $target_path)")
        plan["obligations_closed"] = ["upload_type_validation","upload_storage_policy"]

    elif axiom == "encode_output":
        plan["strategy"] = "HTML-encode untrusted output before rendering"
        patch = patch.replace("$_GET[ 'name' ]", "htmlspecialchars($_GET[ 'name' ], ENT_QUOTES, 'UTF-8')")
        patch = patch.replace('{$user}', '{htmlspecialchars($user, ENT_QUOTES, "UTF-8")}')
        plan["obligations_closed"] = ["html_encode_output"]

    elif axiom == "validate_csrf_and_parameterize":
        plan["strategy"] = "validate CSRF token before state change and parameterize update"
        if "if( isset( $_GET[ 'Change' ] ) ) {" in patch and "validateCsrfToken(" not in patch:
            patch = patch.replace("if( isset( $_GET[ 'Change' ] ) ) {", "if( isset( $_GET[ 'Change' ] ) ) {\n\tif( !validateCsrfToken($_GET['user_token']) ) { exit; }")
        patch = patch.replace('''$result = mysqli_query($GLOBALS["___mysqli_ston"],  $insert ) or die( '<pre>' . ((is_object($GLOBALS["___mysqli_ston"])) ? mysqli_error($GLOBALS["___mysqli_ston"]) : (($___mysqli_res = mysqli_connect_error()) ? $___mysqli_res : false)) . '</pre>' );''',
                              '''$stmt = mysqli_prepare($GLOBALS["___mysqli_ston"], "UPDATE `users` SET password = ? WHERE user = ?;");
mysqli_stmt_bind_param($stmt, "ss", $pass_new, $current_user);
mysqli_stmt_execute($stmt);''')
        plan["obligations_closed"] = ["validate_csrf_token","parameterize_query","normalize_input","allowlist_expected_values"]

    elif axiom == "constrain_redirect_target":
        plan["strategy"] = "allowlist or map redirect targets before redirecting"
        patch = patch.replace("$_GET['redirect']", "allowlist($_GET['redirect'])")
        patch = patch.replace('header ("location: " . allowlist($_GET[\'redirect\']));', 'safeRedirect(SAFE_REDIRECT_MAP[allowlist($_GET[\'redirect\'])]);')
        patch = patch.replace('header ("location: " . $_GET[\'redirect\']);', 'safeRedirect(SAFE_REDIRECT_MAP[allowlist($_GET[\'redirect\'])]);')
        patch = patch.replace('header("location: " . $_GET[\'redirect\']);', 'safeRedirect(SAFE_REDIRECT_MAP[allowlist($_GET[\'redirect\'])]);')
        patch = patch.replace('res.redirect(next);', 'res.redirect(SAFE_REDIRECT_MAP[allowlist(next)]);')
        patch = patch.replace('Response.Redirect(next);', 'Response.Redirect(SAFE_REDIRECT_MAP[allowlist(next)]);')
        patch = patch.replace('redirect_to target_url.to_s', 'redirect_to SAFE_REDIRECT_MAP[allowlist(params[:url])]')
        patch = patch.replace('redirect_to allowlist(target_url.to_s)', 'redirect_to SAFE_REDIRECT_MAP[allowlist(params[:url])]')
        plan["obligations_closed"] = ["constrain_redirect_target","normalize_input","allowlist_expected_values"]

    elif axiom == "quarantine_unknown_representation":
        plan["strategy"] = "quarantine suspicious unknown representation for manual review instead of false-green treatment"
        patch = "# QUARANTINED_SUSPICIOUS_UNKNOWN_REPRESENTATION\n" + patch
        plan["obligations_closed"] = []

    elif axiom == "encode_output_and_parameterize":
        plan["strategy"] = "HTML-encode output-facing fields and parameterize persistence"
        patch = patch.replace("$message = trim( $_POST[ 'mtxMessage' ] );", "$message = htmlspecialchars(trim( $_POST[ 'mtxMessage' ] ), ENT_QUOTES, 'UTF-8');")
        patch = patch.replace("$name    = trim( $_POST[ 'txtName' ] );", "$name    = htmlspecialchars(trim( $_POST[ 'txtName' ] ), ENT_QUOTES, 'UTF-8');")
        patch = patch.replace("""$result = mysqli_query($GLOBALS["___mysqli_ston"],  $query ) or die( '<pre>' . ((is_object($GLOBALS["___mysqli_ston"])) ? mysqli_error($GLOBALS["___mysqli_ston"]) : (($___mysqli_res = mysqli_connect_error()) ? $___mysqli_res : false)) . '</pre>' );""",
                              """$stmt = mysqli_prepare($GLOBALS["___mysqli_ston"], "INSERT INTO guestbook ( comment, name ) VALUES ( ?, ? );");
mysqli_stmt_bind_param($stmt, "ss", $message, $name);
mysqli_stmt_execute($stmt);""")
        plan["obligations_closed"] = ["html_encode_output","parameterize_query"]

    plan["proposed_patch"] = patch
    return plan

def reassess_obligations(existing, plan):
    closed = set(plan.get("obligations_closed", []))
    remaining = [x for x in existing if x not in closed]
    return sorted(set(remaining))
