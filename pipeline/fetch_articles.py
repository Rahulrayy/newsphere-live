import re
import json
import sys
from datetime import datetime, timezone, timedelta

import feedparser

from config import RSS_FEEDS, MAX_ARTICLES, MIN_ARTICLES, DAYS_BACK
from dedupe import dedupe_by_normalised_title
from store import merge_and_prune, save_store


def clean(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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
    save_store(articles)

    articles = articles[:MAX_ARTICLES]

    if len(articles) < MIN_ARTICLES:
        print(f"only {len(articles)} articles after merge, aborting")
        sys.exit(1)

    with open("pipeline/articles.json", "w") as f:
        json.dump(articles, f)


if __name__ == "__main__":
    fetch()