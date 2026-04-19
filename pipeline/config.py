import os

RSS_FEEDS = [
    # general news
    "http://feeds.bbci.co.uk/news/rss.xml",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com&ceid=US:en&hl=en-US&gl=US",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.theguardian.com/us-news/rss",
    "https://feeds.npr.org/1001/rss.xml",
    "https://feeds.npr.org/1004/rss.xml",
    "https://abcnews.go.com/abcnews/topstories",
    "https://feeds.skynews.com/feeds/rss/home.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.washingtonpost.com/rss/world",
    "https://feeds.washingtonpost.com/rss/national",

    # technology
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.feedburner.com/venturebeat/SZYF",

    # science
    "https://www.sciencedaily.com/rss/top/science.xml",
    "https://www.newscientist.com/feed/home/",
    "https://www.nature.com/nature.rss",

    # business and finance
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.ft.com/?format=rss",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "https://fortune.com/feed/",

    # sports
    "https://www.espn.com/espn/rss/news",
    "https://www.skysports.com/rss/12040",

    # health
    "https://rss.medicalnewstoday.com/featurednews.xml",
    "https://www.health.com/syndication/rss/content.xml",

    # politics
    "https://thehill.com/rss/syndicator/19110",
    "https://feeds.politico.com/politico/rss/politicopicks",
]

MAX_ARTICLES              = 5000
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

BREVO_API_KEY             = os.environ.get("BREVO_API_KEY")

CLOUDFLARE_WORKER_URL     = os.environ.get(
    "CLOUDFLARE_WORKER_URL",
    "https://newsphere-subscribe.rahulraypm2002.workers.dev",
)