import re
import numpy as np

from config import DEDUPE_THRESHOLD


def normalise_title(title):
    t = title.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def dedupe_by_normalised_title(articles):
    seen = {}
    kept = []
    for a in articles:
        key = normalise_title(a["title"])
        if len(key) < 20:
            continue
        if key in seen:
            seen[key]["also_covered_by"].append(a["source"])
            continue
        a["also_covered_by"] = []
        seen[key] = a
        kept.append(a)
    return kept


def dedupe_by_embedding(articles, embeddings, threshold=DEDUPE_THRESHOLD):
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    unit = embeddings / norms

    priority = sorted(
        range(len(articles)),
        key=lambda i: (-len(articles[i].get("content", "")), i),
    )

    kept_idx      = []
    kept_unit     = []
    absorbed_into = {}

    for i in priority:
        if not kept_unit:
            kept_idx.append(i)
            kept_unit.append(unit[i])
            absorbed_into[i] = []
            continue

        sims = np.array(kept_unit) @ unit[i]
        best = int(sims.argmax())

        if sims[best] >= threshold:
            canonical = kept_idx[best]
            absorbed_into[canonical].append(articles[i]["source"])
            absorbed_into[canonical].extend(articles[i].get("also_covered_by", []))
        else:
            kept_idx.append(i)
            kept_unit.append(unit[i])
            absorbed_into[i] = []

    kept_idx_sorted = sorted(kept_idx)
    kept_articles   = []
    kept_embeds     = np.zeros(
        (len(kept_idx_sorted), embeddings.shape[1]),
        dtype=embeddings.dtype,
    )

    for new_i, orig_i in enumerate(kept_idx_sorted):
        a = dict(articles[orig_i])
        existing_also = a.get("also_covered_by", [])
        a["also_covered_by"] = sorted(set(existing_also + absorbed_into[orig_i]))
        a["n_sources"]       = 1 + len(a["also_covered_by"])
        kept_articles.append(a)
        kept_embeds[new_i]   = embeddings[orig_i]

    removed = len(articles) - len(kept_articles)
    pct     = 100 * removed / max(len(articles), 1)
    print(f"semantic dedup: kept {len(kept_articles)}, "
          f"removed {removed} ({pct:.1f}%)")

    return kept_articles, kept_embeds