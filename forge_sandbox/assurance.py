
def evaluate_assurance(gates):
    counts=gates["gate_counts"]
    residuals=gates["residual_obligations"]
    status="green"
    if counts["fail"]>0: status="red"
    elif counts["warn"]>0 or residuals: status="amber"
    return {"assurance_rollup":{"status":status,"residual":residuals,"falsified":[r["gate_id"] for r in gates["gate_results"] if r["status"]=="fail"]}}
