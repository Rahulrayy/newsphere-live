import json

from config import OUTPUT_PATH, PREVIOUS_PATH, DIFF_PATH


def diff():
    try:
        with open(OUTPUT_PATH) as f:
            current = json.load(f)
        with open(PREVIOUS_PATH) as f:
            previous = json.load(f)
    except FileNotFoundError:
        print("no previous snapshot found, skipping diff")
        return

    def key(p):
        return p.get("url") or f"title::{p.get('title', '')}"

    prev_keys  = {key(p) for p in previous["points"]}
    new_points = [p for p in current["points"] if key(p) not in prev_keys]

    out = {
        "generated_at": current["generated_at"],
        "n_new":        len(new_points),
        "new_points":   new_points,
    }

    with open(DIFF_PATH, "w") as f:
        json.dump(out, f)

    print(f"diff: {len(new_points)} new articles since last run")


if __name__ == "__main__":
    diff()