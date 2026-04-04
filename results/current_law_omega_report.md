# Current Law Omega Codebase Report v1.0

## public/public_codeql_flask_full_ssrf.py
- expected bucket: clear
- first-round findings: ssrf_request_forwarding
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_codeql_ruby_open_redirect.rb
- expected bucket: clear
- first-round findings: untrusted_get_input, open_redirect
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_django_password_resets_views.py
- expected bucket: clear
- first-round findings: unsafe_deserialization, predictable_token_generation
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_django_pickle_reset.py
- expected bucket: clear
- first-round findings: unsafe_deserialization
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_dvwa_brute_low.php
- expected bucket: clear
- first-round findings: query_string_interpolation, untrusted_get_input, xss_reflected
- final-round findings: none
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': True, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': True}
- round delta: cleared
- expectation_met: True

## public/public_dvwa_csrf_low.php
- expected bucket: clear
- first-round findings: query_string_interpolation, untrusted_get_input, csrf_state_change
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': True, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_dvwa_exec_low.php
- expected bucket: clear
- first-round findings: command_exec_surface, untrusted_get_input
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': True, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_dvwa_fi_low.php
- expected bucket: clear
- first-round findings: untrusted_get_input
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_dvwa_open_redirect_low.php
- expected bucket: clear
- first-round findings: untrusted_get_input, open_redirect
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_dvwa_sqli_low.php
- expected bucket: clear
- first-round findings: query_string_interpolation, untrusted_get_input
- final-round findings: none
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': True, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_dvwa_upload_low.php
- expected bucket: clear
- first-round findings: file_upload_surface
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': True, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_dvwa_xss_r_low.php
- expected bucket: clear
- first-round findings: untrusted_get_input, xss_reflected
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': True}
- round delta: cleared
- expectation_met: True

## public/public_dvwa_xss_s_low.php
- expected bucket: clear
- first-round findings: query_string_interpolation, xss_stored
- final-round findings: none
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': True, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': True}
- round delta: cleared
- expectation_met: True

## public/public_flask_ssti_render.py
- expected bucket: clear
- first-round findings: ssti_template_injection
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_juice_shop_captcha_ts.ts
- expected bucket: clear
- first-round findings: dynamic_eval
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_juice_shop_redirect_ts.ts
- expected bucket: stay_green_or_known_amber
- first-round findings: none
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## public/public_nodegoat_allocations_dao.js
- expected bucket: clear
- first-round findings: nosql_where_injection
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## public/public_nodegoat_user_dao.js
- expected bucket: clear
- first-round findings: broken_auth_password_handling
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## representative/adversarial_broken_half_file.php
- expected bucket: pressure
- first-round findings: query_string_interpolation, untrusted_get_input, broken_security_significant_fragment
- final-round findings: query_string_interpolation, untrusted_get_input, broken_security_significant_fragment
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_django_pickle_exec.py
- expected bucket: pressure
- first-round findings: unsafe_deserialization, fake_safety_wrapper
- final-round findings: unsafe_deserialization, fake_safety_wrapper
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_fake_allowlist_php.php
- expected bucket: pressure
- first-round findings: fake_safety_wrapper, query_string_interpolation, untrusted_get_input
- final-round findings: fake_safety_wrapper, query_string_interpolation, untrusted_get_input
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_fake_math_eval_ts.ts
- expected bucket: pressure
- first-round findings: dynamic_eval, fake_safety_wrapper
- final-round findings: dynamic_eval, fake_safety_wrapper
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_fake_redirect_js.js
- expected bucket: pressure
- first-round findings: fake_safety_wrapper
- final-round findings: fake_safety_wrapper
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_nosql_eval_redirect.js
- expected bucket: pressure
- first-round findings: dynamic_eval, nosql_where_injection
- final-round findings: dynamic_eval
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_polyglot_mixed_fragment.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation
- final-round findings: suspicious_unknown_representation
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_python_pickle_md5_exec.py
- expected bucket: pressure
- first-round findings: unsafe_deserialization, predictable_token_generation, fake_safety_wrapper
- final-round findings: unsafe_deserialization, fake_safety_wrapper
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_python_ssrf_exec.py
- expected bucket: pressure
- first-round findings: ssrf_request_forwarding, fake_safety_wrapper
- final-round findings: fake_safety_wrapper
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_python_ssti_ssrf_exec.py
- expected bucket: pressure
- first-round findings: ssrf_request_forwarding, ssti_template_injection, fake_safety_wrapper
- final-round findings: fake_safety_wrapper
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_ruby_redirect_eval_sql.rb
- expected bucket: pressure
- first-round findings: dynamic_eval, fake_safety_wrapper, query_string_interpolation, untrusted_get_input, open_redirect
- final-round findings: dynamic_eval, fake_safety_wrapper, query_string_interpolation, untrusted_get_input, open_redirect
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/adversarial_unknown_polyglot.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation
- final-round findings: suspicious_unknown_representation
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_01.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_02.txt
- expected bucket: pressure
- first-round findings: command_exec_surface, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: command_exec_surface, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_03.txt
- expected bucket: pressure
- first-round findings: novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_04.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_05.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation
- final-round findings: suspicious_unknown_representation
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_06.txt
- expected bucket: pressure
- first-round findings: novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_07.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_08.txt
- expected bucket: pressure
- first-round findings: novel_structured_unknown_language
- final-round findings: novel_structured_unknown_language
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_09.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_10.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_11.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_12.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_13.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_14.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation
- final-round findings: suspicious_unknown_representation
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_15.txt
- expected bucket: pressure
- first-round findings: novel_structured_unknown_language
- final-round findings: novel_structured_unknown_language
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_16.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_17.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_18.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_19.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_20.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_21.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_22.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_23.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/alien_semantic_blob_24.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/novel_runeflow_lang.rf
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round findings: suspicious_unknown_representation, novel_structured_unknown_language, unknown_semantic_risk
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/prepared_java_control.java
- expected bucket: stay_green
- first-round findings: none
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': True, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/prepared_php_control.php
- expected bucket: stay_green_or_known_amber
- first-round findings: none
- final-round findings: none
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': True, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/representative_csharp_sql.cs
- expected bucket: clear
- first-round findings: query_string_interpolation, untrusted_get_input
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': True, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## representative/representative_java_sqli.java
- expected bucket: clear
- first-round findings: query_string_interpolation, untrusted_get_input
- final-round findings: none
- final-round assurance: amber
- final semantic markers: {'prepared_java': True, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## representative/representative_node_exec.js
- expected bucket: clear
- first-round findings: command_exec_surface
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': True, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## representative/representative_ruby_cmd.rb
- expected bucket: clear
- first-round findings: command_exec_surface, untrusted_get_input
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': True, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## representative/safe_control_python.py
- expected bucket: stay_green
- first-round findings: none
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_csharp_sql_redirect.cs
- expected bucket: pressure
- first-round findings: query_string_interpolation, untrusted_get_input, open_redirect
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': True, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## representative/synth_java_exec_sqli.java
- expected bucket: pressure
- first-round findings: command_exec_surface, query_string_interpolation, untrusted_get_input
- final-round findings: command_exec_surface, query_string_interpolation
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_js_nosql_redirect_wrapper.js
- expected bucket: pressure
- first-round findings: nosql_where_injection
- final-round findings: nosql_where_injection
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': True, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_js_pickle_like_unknown.txt
- expected bucket: pressure
- first-round findings: suspicious_unknown_representation
- final-round findings: suspicious_unknown_representation
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_php_csrf_open_redirect.php
- expected bucket: pressure
- first-round findings: query_string_interpolation, untrusted_get_input
- final-round findings: query_string_interpolation, untrusted_get_input
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_php_fake_allowlist_redirect.php
- expected bucket: pressure
- first-round findings: fake_safety_wrapper, untrusted_get_input
- final-round findings: fake_safety_wrapper, untrusted_get_input
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_php_fileinclude_xss.php
- expected bucket: pressure
- first-round findings: untrusted_get_input
- final-round findings: untrusted_get_input
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_python_decode_wrapper_pickle.py
- expected bucket: pressure
- first-round findings: fake_safety_wrapper
- final-round findings: fake_safety_wrapper
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_python_eval_template.py
- expected bucket: pressure
- first-round findings: dynamic_eval, ssti_template_injection
- final-round findings: dynamic_eval, ssti_template_injection
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_python_pickle_ssrf_template.py
- expected bucket: pressure
- first-round findings: ssti_template_injection
- final-round findings: ssti_template_injection
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_python_predictable_token_exec.py
- expected bucket: pressure
- first-round findings: predictable_token_generation
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: cleared
- expectation_met: True

## representative/synth_python_redirect_pickle.py
- expected bucket: pressure
- first-round findings: none
- final-round findings: none
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_python_ssrf_ssti_wrapper.py
- expected bucket: pressure
- first-round findings: ssrf_request_forwarding, ssti_template_injection, fake_safety_wrapper
- final-round findings: fake_safety_wrapper
- final-round assurance: green
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_python_ssti_only.py
- expected bucket: pressure
- first-round findings: ssti_template_injection
- final-round findings: ssti_template_injection
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_ruby_cmd_template.rb
- expected bucket: pressure
- first-round findings: command_exec_surface, untrusted_get_input
- final-round findings: untrusted_get_input
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': True, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

## representative/synth_ruby_redirect_sql_eval.rb
- expected bucket: pressure
- first-round findings: dynamic_eval, query_string_interpolation, untrusted_get_input, open_redirect
- final-round findings: dynamic_eval, query_string_interpolation, untrusted_get_input, open_redirect
- final-round assurance: amber
- final semantic markers: {'prepared_java': False, 'prepared_php': False, 'parameterized_csharp': False, 'allowlisted_input': False, 'validated_upload': False, 'wrapped_command_exec': False, 'html_encoded_output': False}
- round delta: unchanged_or_partial
- expectation_met: True

# Regression Summary
- total cases: 78
- expected clear cases: 21
- cleared expected cases: 21
- expected control cases: 4
- passing control cases: 4
- pressure cases: representative/adversarial_broken_half_file.php, representative/adversarial_django_pickle_exec.py, representative/adversarial_fake_allowlist_php.php, representative/adversarial_fake_math_eval_ts.ts, representative/adversarial_fake_redirect_js.js, representative/adversarial_nosql_eval_redirect.js, representative/adversarial_polyglot_mixed_fragment.txt, representative/adversarial_python_pickle_md5_exec.py, representative/adversarial_python_ssrf_exec.py, representative/adversarial_python_ssti_ssrf_exec.py, representative/adversarial_ruby_redirect_eval_sql.rb, representative/adversarial_unknown_polyglot.txt, representative/alien_semantic_blob_01.txt, representative/alien_semantic_blob_02.txt, representative/alien_semantic_blob_03.txt, representative/alien_semantic_blob_04.txt, representative/alien_semantic_blob_05.txt, representative/alien_semantic_blob_06.txt, representative/alien_semantic_blob_07.txt, representative/alien_semantic_blob_08.txt, representative/alien_semantic_blob_09.txt, representative/alien_semantic_blob_10.txt, representative/alien_semantic_blob_11.txt, representative/alien_semantic_blob_12.txt, representative/alien_semantic_blob_13.txt, representative/alien_semantic_blob_14.txt, representative/alien_semantic_blob_15.txt, representative/alien_semantic_blob_16.txt, representative/alien_semantic_blob_17.txt, representative/alien_semantic_blob_18.txt, representative/alien_semantic_blob_19.txt, representative/alien_semantic_blob_20.txt, representative/alien_semantic_blob_21.txt, representative/alien_semantic_blob_22.txt, representative/alien_semantic_blob_23.txt, representative/alien_semantic_blob_24.txt, representative/novel_runeflow_lang.rf, representative/synth_csharp_sql_redirect.cs, representative/synth_java_exec_sqli.java, representative/synth_js_nosql_redirect_wrapper.js, representative/synth_js_pickle_like_unknown.txt, representative/synth_php_csrf_open_redirect.php, representative/synth_php_fake_allowlist_redirect.php, representative/synth_php_fileinclude_xss.php, representative/synth_python_decode_wrapper_pickle.py, representative/synth_python_eval_template.py, representative/synth_python_pickle_ssrf_template.py, representative/synth_python_predictable_token_exec.py, representative/synth_python_redirect_pickle.py, representative/synth_python_ssrf_ssti_wrapper.py, representative/synth_python_ssti_only.py, representative/synth_ruby_cmd_template.rb, representative/synth_ruby_redirect_sql_eval.rb
- regression failures: none