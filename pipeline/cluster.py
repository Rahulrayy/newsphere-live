import json
import os
import shutil
from datetime import datetime, timezone

import numpy as np
import umap
import hdbscan

from config import (
    UMAP_NEIGHBORS, UMAP_MIN_DIST, UMAP_COMPONENTS,
    UMAP_METRIC, UMAP_RANDOM_STATE,
    HDBSCAN_MIN_SIZE_FRACTION, HDBSCAN_MIN_SIZE_FLOOR,
    HDBSCAN_MIN_SAMPLES, HDBSCAN_METHOD,
    TFIDF_TOP_N,
    OUTPUT_PATH, PREVIOUS_PATH,
)
from dedupe import dedupe_by_embedding
from align import procrustes_align
from labelling import label_clusters


def cluster():
    with open("pipeline/articles.json") as f:
        articles = json.load(f)

    embeddings = np.load("pipeline/embeddings.npy")

    articles, embeddings = dedupe_by_embedding(articles, embeddings)

    prev_coords, prev_keys = None, None
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH) as f:
                prev = json.load(f)
            prev_coords = np.array(
                [[p["x"], p["y"], p["z"]] for p in prev["points"]],
                dtype=np.float32,
            )
            prev_keys = [p.get("url", "") for p in prev["points"]]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"previous output unreadable ({e}), will use raw UMAP")

    reducer = umap.UMAP(
        n_components=UMAP_COMPONENTS,
        n_neighbors=UMAP_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        metric=UMAP_METRIC,
        random_state=UMAP_RANDOM_STATE,
    )
    coords = reducer.fit_transform(embeddings)

    if prev_coords is not None and prev_keys is not None:
        curr_keys = [a.get("url", "") for a in articles]
        coords    = procrustes_align(coords, curr_keys, prev_coords, prev_keys)

    min_size = max(
        HDBSCAN_MIN_SIZE_FLOOR,
        int(len(articles) * HDBSCAN_MIN_SIZE_FRACTION),
    )
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_size,
        min_samples=HDBSCAN_MIN_SAMPLES,
        cluster_selection_method=HDBSCAN_METHOD,
        gen_min_span_tree=True,
    )
    labels = clusterer.fit_predict(coords)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise    = int((labels == -1).sum())
    print(f"hdbscan min_size={min_size} on {len(articles)} articles: "
          f"{n_clusters} clusters, {n_noise} noise "
          f"({100 * n_noise / len(labels):.1f}%)")

    unique = sorted([c for c in set(labels) if c != -1])
    cluster_labels = label_clusters(articles, labels, unique, top_n=TFIDF_TOP_N)

    points = []
    for i, a in enumerate(articles):
        date = a.get("date", "")
        try:
            day = datetime.strptime(date, "%Y-%m-%d").timetuple().tm_yday
        except Exception:
            day = 1

        points.append({
            "x":               round(float(coords[i, 0]), 4),
            "y":               round(float(coords[i, 1]), 4),
            "z":               round(float(coords[i, 2]), 4),
            "cluster":         int(labels[i]),
            "title":           a["title"],
            "content":         a["content"],
            "date":            date,
            "url":             a["url"],
            "source":          a["source"],
            "also_covered_by": a.get("also_covered_by", []),
            "n_sources":       a.get("n_sources", 1),
            "day":             day,
        })

    try:
        shutil.copy(OUTPUT_PATH, PREVIOUS_PATH)
    except FileNotFoundError:
        pass

    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "n_articles":   len(points),
        "n_clusters":   n_clusters,
        "points":       points,
        "clusters":     {str(k): v for k, v in cluster_labels.items()},
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f)

    print(f"exported {len(points)} points to {OUTPUT_PATH}")


if __name__ == "__main__":
    cluster()