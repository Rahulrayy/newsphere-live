import json
import numpy as np
from sentence_transformers import SentenceTransformer

from config import EMBED_MODEL, EMBED_BATCH_SIZE


def embed():
    with open("pipeline/articles.json") as f:
        articles = json.load(f)

    texts = [a.get("content") or a["title"] for a in articles]
    model = SentenceTransformer(EMBED_MODEL)

    embeddings = model.encode(
        texts,
        batch_size=EMBED_BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    np.save("pipeline/embeddings.npy", embeddings)
    print(f"embedded {len(texts)} articles using {EMBED_MODEL}, "
          f"shape- {embeddings.shape}")


if __name__ == "__main__":
    embed()