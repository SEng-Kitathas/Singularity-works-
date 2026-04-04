
from pathlib import Path
import json
from forge_sandbox.probe_loop import probe_loop

expectations = json.loads(Path("tests/expectations.json").read_text(encoding="utf-8"))
results = []
for path in sorted(Path("corpus").rglob("*")):
    if path.is_file():
        rel = str(path.relative_to(Path("corpus")))
        results.append(probe_loop(rel, path.read_text(encoding="utf-8"), max_rounds=3))

Path("results").mkdir(exist_ok=True)
(Path("results") / "current_law_omega_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

def classify_outcome(item):
    first = item["rounds"][0]
    final = item["rounds"][-1]
    clear = bool(first["summary"]["findings"]) and not final["summary"]["findings"]
    final_green = final["summary"]["assurance_status"] == "green"
    return clear, final_green

regression_failures = []
lines = ["# Current Law Omega Codebase Report v1.0", ""]
for item in results:
    first = item["rounds"][0]
    final = item["rounds"][-1]
    name = item["file"]
    exp = expectations.get(name, "unknown")
    clear, final_green = classify_outcome(item)
    ok = False
    if exp == "clear":
        ok = clear
    elif exp == "stay_green":
        ok = (not first["summary"]["findings"]) and final_green
    elif exp == "stay_green_or_known_amber":
        ok = (not first["summary"]["findings"]) and final["summary"]["assurance_status"] in {"green", "amber"}
    elif exp == "pressure":
        ok = True
    if not ok:
        regression_failures.append(name)

    lines.append(f"## {name}")
    lines.append(f"- expected bucket: {exp}")
    lines.append(f"- first-round findings: {', '.join(first['summary']['findings']) if first['summary']['findings'] else 'none'}")
    lines.append(f"- final-round findings: {', '.join(final['summary']['findings']) if final['summary']['findings'] else 'none'}")
    lines.append(f"- final-round assurance: {final['summary']['assurance_status']}")
    lines.append(f"- final semantic markers: {final['summary']['semantic_markers']}")
    delta = "cleared" if clear else "unchanged_or_partial"
    lines.append(f"- round delta: {delta}")
    lines.append(f"- expectation_met: {ok}")
    lines.append("")

pressure_items = [item["file"] for item in results if expectations.get(item["file"]) == "pressure"]
summary = {
    "total_cases": len(results),
    "expected_clear_cases": sum(1 for v in expectations.values() if v == "clear"),
    "cleared_expected_cases": sum(1 for item in results if expectations.get(item["file"]) == "clear" and classify_outcome(item)[0]),
    "expected_control_cases": sum(1 for v in expectations.values() if v in {"stay_green", "stay_green_or_known_amber"}),
    "passing_control_cases": sum(1 for item in results if expectations.get(item["file"]) in {"stay_green", "stay_green_or_known_amber"} and item["file"] not in regression_failures),
    "pressure_cases": pressure_items,
    "regression_failures": regression_failures,
}
(Path("results") / "regression_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
lines.append("# Regression Summary")
lines.append(f"- total cases: {summary['total_cases']}")
lines.append(f"- expected clear cases: {summary['expected_clear_cases']}")
lines.append(f"- cleared expected cases: {summary['cleared_expected_cases']}")
lines.append(f"- expected control cases: {summary['expected_control_cases']}")
lines.append(f"- passing control cases: {summary['passing_control_cases']}")
lines.append(f"- pressure cases: {', '.join(summary['pressure_cases']) if summary['pressure_cases'] else 'none'}")
lines.append(f"- regression failures: {', '.join(summary['regression_failures']) if summary['regression_failures'] else 'none'}")
(Path("results") / "current_law_omega_report.md").write_text("\n".join(lines), encoding="utf-8")
print("done")
