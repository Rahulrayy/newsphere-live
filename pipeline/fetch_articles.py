import re
import html
import json
import sys
from datetime import datetime, timezone, timedelta

import feedparser

from config import RSS_FEEDS, MAX_ARTICLES, MIN_ARTICLES, DAYS_BACK
from dedupe import dedupe_by_normalised_title
from store import merge_and_prune, save_store


# feed furniture that ends up in the descriptions and then dominates the
# c-tf-idf labels ("continue reading", nature's doi header, bloomberg tag...)
BOILERPLATE_PATTERNS = [
    r"^Nature, Published online: [^;]*; doi:\S*?/[\w.-]*?\d(?=[A-Z])",
    r"^Nature, Published online: [^;]*; doi:\S+\s*",
    r"\s*Continue reading\.*\s*$",
    r"\s*\(Source: Bloomberg\)\s*$",
    r"^This blog is now closed\.?",
    # guardian promo lines, usually glued straight onto the next sentence
    r"Sign up (for|to) [^.]*?(email|newsletter|column as a free \w+)( here)?",
    r"Get our [\w ]*?(email|newsletter), free app or daily news podcast",
    r"Follow our [\w ]*?live blog for (the )?latest updates( here)?",
    r"\{beacon\}",
    r"\s*-? ?live on Sky Sports Racing\.*",
]
BOILERPLATE_RE = [re.compile(p) for p in BOILERPLATE_PATTERNS]


def clean(text):
    text = re.sub(r"<[^>]+>", "", text)
    # html.unescape handles the numeric ones too (&#8230; etc), the old
    # regex only caught named entities so "8230" was leaking into labels
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_boilerplate(text):
    for pat in BOILERPLATE_RE:
        text = pat.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch():
    articles = []
    cutoff   = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = clean(entry.get("title") or "")
                desc  = clean(entry.get("summary") or entry.get("description") or "")
                url   = entry.get("link", "")

                published = entry.get("published_parsed")
                if published:
                    d = datetime(*published[:6], tzinfo=timezone.utc)
                    if d < cutoff:
                        continue
                    date_str = d.strftime("%Y-%m-%d")
                else:
                    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                if not title or len(title) < 20:
                    continue

                articles.append({
                    "title":   title,
                    "content": desc if desc else title,
                    "url":     url,
                    "date":    date_str,
                    "source":  feed.feed.get("title", feed_url),
                })

        except Exception as e:
            print(f"failed to parse {feed_url}: {e}")
            continue

    articles = dedupe_by_normalised_title(articles)
    print(f"fetched {len(articles)} unique articles from {len(RSS_FEEDS)} feeds")

    articles = merge_and_prune(articles, days_back=DAYS_BACK)

    # run this after the merge so articles already sitting in the store get
    # cleaned too, not just the fresh ones. it's idempotent so rerunning is fine
    for a in articles:
        a["title"]   = strip_boilerplate(clean(a["title"]))
        a["content"] = strip_boilerplate(clean(a["content"])) or a["title"]
    save_store(articles)

    articles = articles[:MAX_ARTICLES]

    if len(articles) < MIN_ARTICLES:
        print(f"only {len(articles)} articles after merge, aborting")
        sys.exit(1)

    with open("pipeline/articles.json", "w") as f:
        json.dump(articles, f)


if __name__ == "__main__":
    fetch()