import re

def parse_judge_verdict(verdict: str) -> dict:
    out = {}
    for model_label in ["DeepSeek", "Llama"]:
        pattern = rf"{model_label}:\s*\n(.*?)(?=\n(?:DeepSeek|Llama|Winner):|\Z)"
        m = re.search(pattern, verdict, re.DOTALL)
        if not m: continue
        for line in m.group(1).strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                out[f"{model_label.lower()}_{key}"] = val.strip()
    winner_m = re.search(r"Winner:\s*(.+?)(?:\n|$)", verdict)
    if winner_m: out["winner"] = winner_m.group(1).strip()
    reason_m = re.search(r"Reason:\s*(.+)", verdict, re.DOTALL)
    if reason_m: out["reason"] = reason_m.group(1).strip()
    return out