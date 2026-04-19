import json
import os
from datetime import datetime, timezone, timedelta

from config import STORE_PATH


def _parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def load_store():
    if not os.path.exists(STORE_PATH):
        return []
    try:
        with open(STORE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"store corrupt or unreadable ({e}), starting fresh")
        return []


def save_store(articles):
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w") as f:
        json.dump(articles, f)


def merge_and_prune(fresh_articles, days_back=7):
    existing = load_store()

    by_key = {}
    for a in existing + fresh_articles:
        key = a.get("url") or ("title:" + a.get("title", "").lower().strip())
        if not key or key == "title:":
            continue
        by_key[key] = a

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    kept = []
    for a in by_key.values():
        d = _parse_date(a.get("date", ""))
        if d is None or d >= cutoff:
            kept.append(a)

    kept.sort(key=lambda a: a.get("date", ""), reverse=True)
    kept = kept[:20_000]  # hard cap.... sorted newest-first so oldest get dropped
    print(f"store: {len(existing)} existing + {len(fresh_articles)} fresh "
          f"-> {len(kept)} after merge+prune")
    return kept
