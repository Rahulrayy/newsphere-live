import os
import json
import requests

from config import (
    OUTPUT_PATH, DIFF_PATH, DIGEST_PATH,
    SITE_URL, RESEND_API_KEY, RESEND_AUDIENCE_ID, RESEND_FROM_EMAIL,
)

CLUSTER_COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
    "#c49c94", "#f7b6d2",
]


def build_digest_data(data, diff):
    clusters    = data.get("clusters", {})
    points      = data.get("points", [])

    counts      = {}
    outlet_sets = {}
    for p in points:
        c = p["cluster"]
        if c == -1:
            continue
        counts[c] = counts.get(c, 0) + 1
        outlets   = outlet_sets.setdefault(c, set())
        outlets.add(p["source"])
        for s in p.get("also_covered_by", []):
            outlets.add(s)

    top_clusters = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:8]

    cluster_articles = {}
    for cid, _ in top_clusters:
        arts = [p for p in points if p["cluster"] == cid]
        arts = sorted(arts, key=lambda x: x["date"], reverse=True)[:5]
        cluster_articles[cid] = arts

    return {
        "generated_at":     data.get("generated_at", "unknown"),
        "n_articles":       len(points),
        "n_clusters":       data.get("n_clusters", 0),
        "n_new":            diff.get("n_new", 0) if diff else 0,
        "top_clusters":     top_clusters,
        "cluster_labels":   clusters,
        "cluster_articles": cluster_articles,
        "outlet_counts":    {c: len(s) for c, s in outlet_sets.items()},
    }


def generate_html(d, for_email=False):
    cluster_rows = ""
    for rank, (cid, count) in enumerate(d["top_clusters"], 1):
        label     = d["cluster_labels"].get(str(cid), "unknown")
        color     = CLUSTER_COLORS[int(cid) % len(CLUSTER_COLORS)]
        articles  = d["cluster_articles"].get(cid, [])
        n_outlets = d["outlet_counts"].get(cid, 1)

        article_rows = ""
        for a in articles:
            article_rows += f"""
            <div style="padding: 8px 0; border-top: 0.5px solid #f0f0f0;">
              <a href="{a['url']}" target="_blank"
                 style="font-size: 13px; color: #1a1a1a; text-decoration: none;">
                {a['title']}
              </a>
              <div style="font-size: 11px; color: #aaa; margin-top: 2px;">
                {a['date']} -- {a['source']}
              </div>
            </div>"""

        cluster_rows += f"""
        <div style="background: white; border: 0.5px solid #e0e0e0;
                    border-radius: 10px; padding: 16px 20px; margin-bottom: 16px;">
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <div style="width: 10px; height: 10px; border-radius: 50%;
                        background: {color}; flex-shrink: 0;"></div>
            <div style="font-size: 15px; font-weight: 500;">{label}</div>
            <div style="margin-left: auto; font-size: 12px; color: #aaa;">
              {count} stories &middot; {n_outlets} outlets
            </div>
          </div>
          {article_rows}
        </div>"""

    subscribe_section = "" if for_email else """
    <div style="background: white; border: 0.5px solid #e0e0e0; border-radius: 10px;
                padding: 20px; margin-top: 32px;">
      <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 12px;">
        <input type="email" id="email-input" placeholder="your@email.com"
               autocomplete="email"
               style="flex: 1; font-size: 13px; padding: 8px 12px;
                      border: 0.5px solid #e0e0e0; border-radius: 6px;
                      background: #f9f9f7; color: #1a1a1a;" />
        <input type="text" id="website" name="website" tabindex="-1"
               autocomplete="off"
               style="position:absolute; left:-9999px; width:1px; height:1px; opacity:0;" />
        <button id="subscribe-btn" onclick="subscribe()"
                style="font-size: 13px; padding: 8px 16px; border: 0.5px solid #4e79a7;
                       border-radius: 6px; background: #4e79a7; color: white; cursor: pointer;">
          Get daily digest
        </button>
      </div>
      <div class="cf-turnstile" data-sitekey="YOUR_TURNSTILE_SITE_KEY"
           data-callback="onTurnstileSuccess" data-theme="light"></div>
      <div id="subscribe-status" style="font-size:12px; color:#888; margin-top:8px;"></div>
    </div>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
    <script>
      let turnstileToken = null;
      let lastAttempt = 0;
      function onTurnstileSuccess(token) { turnstileToken = token; }
      function setStatus(msg, isError) {
        const el = document.getElementById('subscribe-status');
        el.textContent = msg;
        el.style.color = isError ? '#c0392b' : '#888';
      }
      async function subscribe() {
        const btn   = document.getElementById('subscribe-btn');
        const email = document.getElementById('email-input').value.trim();
        const honey = document.getElementById('website').value;
        if (honey) {
          setStatus('Subscribed. You will receive your first digest tomorrow morning.', false);
          return;
        }
        if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) {
          setStatus('That does not look like a valid email address.', true);
          return;
        }
        const now = Date.now();
        if (now - lastAttempt < 3000) {
          setStatus('Please wait a moment before trying again.', true);
          return;
        }
        lastAttempt = now;
        if (!turnstileToken) {
          setStatus('Please complete the verification and try again.', true);
          return;
        }
        btn.disabled = true;
        btn.textContent = 'Subscribing...';
        try {
          const r = await fetch('YOUR_WORKER_URL', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, turnstileToken, honeypot: honey }),
          });
          if (r.ok) {
            setStatus('Subscribed. You will receive your first digest tomorrow morning.', false);
            document.getElementById('email-input').value = '';
          } else {
            setStatus('Something went wrong. Please try again later.', true);
          }
        } catch (e) {
          setStatus('Network error. Please try again.', true);
        } finally {
          btn.disabled = false;
          btn.textContent = 'Get daily digest';
          turnstileToken = null;
          if (window.turnstile) window.turnstile.reset();
        }
      }
    </script>"""

    nav = "" if for_email else """
  <nav style="position:fixed; top:0; left:0; right:0; height:48px; background:white;
              border-bottom:0.5px solid #e0e0e0; display:flex; align-items:center;
              padding:0 32px; gap:24px; z-index:100;">
    <a href="index.html" style="font-size:14px; font-weight:500; color:#1a1a1a; text-decoration:none;">
      Newsphere Live
    </a>
    <div style="display:flex; gap:20px; margin-left:auto;">
      <a href="index.html" style="font-size:13px; color:#888; text-decoration:none;">Visualization</a>
      <a href="digest.html" style="font-size:13px; color:#1a1a1a; font-weight:500; text-decoration:none;">Digest</a>
      <a href="writeup.html" style="font-size:13px; color:#888; text-decoration:none;">Write-up</a>
    </div>
  </nav>"""

    open_map_btn = f"""
    <a href="{SITE_URL}/index.html"
       style="display:inline-block; margin-top:24px; font-size:13px; color:#4e79a7;
              text-decoration:none; border:0.5px solid #4e79a7; border-radius:6px;
              padding:8px 16px;">
      Open the live map
    </a>"""

    body_padding = "80px 24px 80px" if not for_email else "32px 24px"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Newsphere Live -- Daily Digest</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #f9f9f7; color: #1a1a1a; line-height: 1.6;
    }}
  </style>
</head>
<body>
  {nav}
  <div style="max-width: 680px; margin: 0 auto; padding: {body_padding};">
    <h1 style="font-size: 22px; font-weight: 500; margin-bottom: 6px;">Daily digest</h1>
    <div style="font-size: 13px; color: #aaa; margin-bottom: 28px;">
      Generated {d['generated_at']} -- data refreshes every day at 02:00 UTC
    </div>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 32px;">
      <div style="background:white; border:0.5px solid #e0e0e0; border-radius:10px;
                  padding:16px; text-align:center;">
        <div style="font-size:24px; font-weight:500;">{d['n_articles']}</div>
        <div style="font-size:12px; color:#aaa; margin-top:4px;">Unique stories</div>
      </div>
      <div style="background:white; border:0.5px solid #e0e0e0; border-radius:10px;
                  padding:16px; text-align:center;">
        <div style="font-size:24px; font-weight:500;">{d['n_clusters']}</div>
        <div style="font-size:12px; color:#aaa; margin-top:4px;">Topics found</div>
      </div>
      <div style="background:white; border:0.5px solid #e0e0e0; border-radius:10px;
                  padding:16px; text-align:center;">
        <div style="font-size:24px; font-weight:500;">{d['n_new']}</div>
        <div style="font-size:12px; color:#aaa; margin-top:4px;">New since yesterday</div>
      </div>
    </div>
    <div style="font-size:14px; font-weight:500; color:#999; text-transform:uppercase;
                letter-spacing:0.05em; margin-bottom:16px;">Top topics today</div>
    {cluster_rows}
    {open_map_btn}
    {subscribe_section}
  </div>
</body>
</html>"""


def send_email_digest(d):
    if not RESEND_API_KEY or not RESEND_AUDIENCE_ID:
        print("Resend credentials not configured, skipping email")
        return

    subject  = (f"Newsphere Live -- {d['n_clusters']} topics, "
                f"{d['n_new']} new articles today")
    date_str = d["generated_at"][:10]
    html     = generate_html(d, for_email=True)

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type":  "application/json",
    }

    try:
        resp = requests.post(
            "https://api.resend.com/broadcasts",
            headers=headers,
            json={
                "audience_id": RESEND_AUDIENCE_ID,
                "from":        RESEND_FROM_EMAIL,
                "subject":     subject,
                "html":        html,
                "name":        f"digest-{date_str}",
            },
            timeout=30,
        )
        resp.raise_for_status()
        broadcast_id = resp.json()["id"]

        resp = requests.post(
            f"https://api.resend.com/broadcasts/{broadcast_id}/send",
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        print(f"email digest sent via Resend broadcast {broadcast_id}")

    except requests.HTTPError as e:
        print(f"Resend API error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"email send failed: {e}")


def digest():
    with open(OUTPUT_PATH) as f:
        data = json.load(f)

    try:
        with open(DIFF_PATH) as f:
            diff = json.load(f)
    except FileNotFoundError:
        diff = None

    d = build_digest_data(data, diff)

    with open(DIGEST_PATH, "w") as f:
        f.write(generate_html(d, for_email=False))
    print("digest.html generated")

    send_email_digest(d)


if __name__ == "__main__":
    digest()