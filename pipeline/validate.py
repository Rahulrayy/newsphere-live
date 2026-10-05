import os
import json
import sys
from datetime import datetime, timezone

from config import (
    OUTPUT_PATH, STORE_PATH, STATUS_LOG_PATH,
    MIN_ARTICLES, MAX_ARTICLES, MIN_CLUSTERS, MIN_COORD_SPREAD,
)


def _store_size():
    if not os.path.exists(STORE_PATH):
        return 0
    try:
        with open(STORE_PATH) as f:
            return len(json.load(f))
    except Exception:
        return 0


def _append_status(**fields):
    line = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    os.makedirs(os.path.dirname(STATUS_LOG_PATH), exist_ok=True)
    try:
        with open(STATUS_LOG_PATH, "a") as f:
            f.write(json.dumps(line) + "\n")
    except OSError as e:
        print(f"could not write status log: {e}")


def _coord_spread(points):
    # smallest per-axis std, if any axis has flattened out the map is broken
    if not points:
        return 0.0
    spreads = []
    for axis in ("x", "y", "z"):
        vals = [p[axis] for p in points]
        mean = sum(vals) / len(vals)
        spreads.append((sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5)
    return min(spreads)


def validate():
    try:
        with open(OUTPUT_PATH) as f:
            data = json.load(f)
    except Exception as e:
        _append_status(status="fail", reason=f"json_parse: {e}")
        print(f"validation failed: could not parse JSON -- {e}")
        sys.exit(1)

    n_points   = len(data.get("points", []))
    n_clusters = data.get("n_clusters", 0)
    store_size = _store_size()

    expected = max(MIN_ARTICLES, min(store_size // 2, MAX_ARTICLES // 2))

    if n_points < expected:
        _append_status(
            status="fail", reason=f"n_points {n_points} < expected {expected}",
            n_points=n_points, n_clusters=n_clusters, store_size=store_size,
        )
        print(f"validation failed: {n_points} points below expected {expected} "
              f"(store has {store_size}, floor {MIN_ARTICLES})")
        sys.exit(1)

    spread = _coord_spread(data.get("points", []))
    if spread < MIN_COORD_SPREAD:
        _append_status(
            status="fail", reason=f"coord_spread {spread:.2e} < {MIN_COORD_SPREAD}",
            n_points=n_points, n_clusters=n_clusters, store_size=store_size,
        )
        print(f"validation failed: layout has collapsed, min axis std "
              f"{spread:.2e} is below {MIN_COORD_SPREAD}")
        sys.exit(1)

    if n_clusters < MIN_CLUSTERS:
        _append_status(
            status="fail", reason=f"n_clusters {n_clusters} < {MIN_CLUSTERS}",
            n_points=n_points, n_clusters=n_clusters, store_size=store_size,
        )
        print(f"validation failed: only {n_clusters} clusters, "
              f"minimum is {MIN_CLUSTERS}")
        sys.exit(1)

    _append_status(
        status="ok",
        n_points=n_points, n_clusters=n_clusters, store_size=store_size,
        coord_spread=round(spread, 4),
    )
    print(f"validation passed: {n_points} points, {n_clusters} clusters, "
          f"store size {store_size}, spread {spread:.3f}")


if __name__ == "__main__":
    validate()