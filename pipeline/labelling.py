import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS

NEWS_STOPWORDS = {
    "said", "says", "told", "reported", "reports", "according",
    "new", "year", "years", "week", "day", "time", "times",
    "people", "like", "just", "also", "would", "could",
    "one", "two", "first", "last",
}


def _c_tf_idf(cluster_docs, ngram_range=(1, 2), stop_words=None,
              max_features=5000, min_df=2):
    cv = CountVectorizer(
        ngram_range=ngram_range,
        stop_words=stop_words,
        max_features=max_features,
        min_df=min_df,
    )
    counts = cv.fit_transform(cluster_docs).toarray().astype(float)
    vocab  = cv.get_feature_names_out()

    words_per_cluster = counts.sum(axis=1, keepdims=True)
    words_per_cluster[words_per_cluster == 0] = 1
    tf = counts / words_per_cluster

    term_totals     = counts.sum(axis=0)
    avg_cluster_len = counts.sum() / max(len(cluster_docs), 1)
    idf             = np.log(1 + (avg_cluster_len / np.maximum(term_totals, 1)))

    return tf * idf, vocab


def _dedupe_substrings(candidates, k):
    kept = []
    for term in candidates:
        clash = any(term in kt or kt in term for kt in kept)
        if not clash:
            kept.append(term)
        if len(kept) == k:
            break
    return kept


def label_clusters(articles, labels, unique_cluster_ids, top_n=3):
    cluster_docs = []
    for cid in unique_cluster_ids:
        texts = [articles[i]["content"]
                 for i, l in enumerate(labels) if l == cid]
        cluster_docs.append(" ".join(texts))

    stop_words = list(ENGLISH_STOP_WORDS.union(NEWS_STOPWORDS))

    scores, vocab = _c_tf_idf(
        cluster_docs,
        ngram_range=(1, 2),
        stop_words=stop_words,
        max_features=5000,
        min_df=2,
    )

    candidate_pool = max(top_n * 4, 10)
    out = {-1: "noise"}

    for row_idx, cid in enumerate(unique_cluster_ids):
        row        = scores[row_idx]
        top_idx    = row.argsort()[-candidate_pool:][::-1]
        candidates = [vocab[i] for i in top_idx if row[i] > 0]
        kept       = _dedupe_substrings(candidates, k=top_n)
        out[cid]   = " ".join(kept) if kept else "unlabelled"

    return out