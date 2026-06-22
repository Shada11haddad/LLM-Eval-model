import re
from config import cfg


def parse_judge_verdict(verdict: str):

    results = {}

    for model_name in (k for k in cfg.MODELS.keys() if k != "judge"):

        pattern = (
            rf"{model_name.upper()}:\s*\n"
            rf"(.*?)(?=\n[A-Z0-9_]+:|\nWinner:|\Z)")

        match = re.search(pattern,verdict,re.DOTALL)

        if not match:
            continue

        section = match.group(1)

        for line in section.split("\n"):

            if ":" not in line:
                continue

            key, value = line.split(":", 1)

            key = (key.strip().lower().replace(" ", "_"))

            value = value.strip()

            try:
                value = float(value) 
            except:
                pass

            results[
                f"{model_name}_{key}"
            ] = value

    winner_match = re.search(r"Winner:\s*(.+)",verdict)

    if winner_match:
        results["winner"] = (winner_match.group(1).strip())

    return results