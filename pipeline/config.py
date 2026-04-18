import os

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com&ceid=US:en&hl=en-US&gl=US",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.theguardian.com/world/rss",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://techcrunch.com/feed/",
    "https://www.sciencedaily.com/rss/top/science.xml",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.ft.com/?format=rss",
    "https://www.espn.com/espn/rss/news",
    "https://rss.medicalnewstoday.com/featurednews.xml",
]

MAX_ARTICLES              = 3000
MIN_ARTICLES              = 300
DAYS_BACK                 = 7

EMBED_MODEL               = "all-MiniLM-L6-v2"
EMBED_BATCH_SIZE          = 64

DEDUPE_THRESHOLD          = 0.90

UMAP_NEIGHBORS            = 20
UMAP_MIN_DIST             = 0.1
UMAP_COMPONENTS           = 3
UMAP_METRIC               = "cosine"
UMAP_RANDOM_STATE         = 42

HDBSCAN_MIN_SIZE_FRACTION = 0.025
HDBSCAN_MIN_SIZE_FLOOR    = 8
HDBSCAN_MIN_SAMPLES       = 6
HDBSCAN_METHOD            = "eom"

TFIDF_NGRAM_RANGE         = (1, 2)
TFIDF_MAX_FEATURES        = 5000
TFIDF_TOP_N               = 3

MIN_CLUSTERS              = 5

OUTPUT_PATH               = "data/news_map.json"
PREVIOUS_PATH             = "data/news_map_previous.json"
DIFF_PATH                 = "data/news_map_diff.json"
STORE_PATH                = "data/article_store.json"
STATUS_LOG_PATH           = "data/status_log.jsonl"
DIGEST_PATH               = "digest.html"

SITE_URL                  = "https://rahulrayy.github.io/newsphere-live"

RESEND_API_KEY            = os.environ.get("RESEND_API_KEY")
RESEND_AUDIENCE_ID        = os.environ.get("RESEND_AUDIENCE_ID")
RESEND_FROM_EMAIL         = os.environ.get("RESEND_FROM_EMAIL", "digest@example.com")

CLOUDFLARE_WORKER_URL     = os.environ.get(
    "CLOUDFLARE_WORKER_URL",
    "https://newsphere-subscribe.YOUR_SUBDOMAIN.workers.dev",
)