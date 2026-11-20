"""Read-only Reddit research script for personal, non-commercial investment research.

Searches a configurable list of investing subreddits for given tickers and saves
post titles, bodies and top comments to a local JSON file. It never posts, votes,
comments or sends messages.

Usage:
    python research.py NVDA MSFT --limit 5 --comments 5

Credentials come from environment variables (see README). Nothing secret is stored here.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import praw

SUBREDDITS = ["stocks", "investing", "SecurityAnalysis", "ValueInvesting", "StockMarket"]

MAX_REQUESTS_PER_RUN = 15      # 6 runs/day x 15 = 90 requests/day, under 100
MAX_RUNS_PER_DAY = 6
SECONDS_BETWEEN_REQUESTS = 2.0
CACHE_DIR = Path("cache")
CACHE_MAX_AGE_DAYS = 7          # older result files are deleted on each run
RUN_LOG = CACHE_DIR / "runs.json"


class Budget:
    def __init__(self, limit):
        self.limit, self.used = limit, 0

    def spend(self):
        if self.used >= self.limit:
            raise RuntimeError("request budget for this run reached")
        self.used += 1
        time.sleep(SECONDS_BETWEEN_REQUESTS)


def check_daily_runs():
    today = datetime.now(timezone.utc).date().isoformat()
    runs = json.loads(RUN_LOG.read_text()) if RUN_LOG.exists() else {}
    runs = {today: runs.get(today, 0)}
    if runs[today] >= MAX_RUNS_PER_DAY:
        sys.exit(f"Daily run limit ({MAX_RUNS_PER_DAY}) reached; try again tomorrow.")
    runs[today] += 1
    RUN_LOG.write_text(json.dumps(runs))


def prune_cache():
    cutoff = time.time() - CACHE_MAX_AGE_DAYS * 86400
    for f in CACHE_DIR.glob("results-*.json"):
        if f.stat().st_mtime < cutoff:
            f.unlink()


def make_client():
    try:
        reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent=os.environ.get("REDDIT_USER_AGENT", "script:reddit-thesis-research:v0.1 (read-only)"),
        )
    except KeyError as e:
        sys.exit(f"Missing environment variable: {e}")
    reddit.read_only = True
    return reddit


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("tickers", nargs="+")
    p.add_argument("--subreddits", nargs="+", default=SUBREDDITS)
    p.add_argument("--limit", type=int, default=3, help="posts per search")
    p.add_argument("--comments", type=int, default=5, help="top comments per post")
    p.add_argument("--time", default="week", choices=["day", "week", "month", "year"])
    args = p.parse_args()

    CACHE_DIR.mkdir(exist_ok=True)
    check_daily_runs()
    prune_cache()
    reddit = make_client()
    budget = Budget(MAX_REQUESTS_PER_RUN)
    results = []

    try:
        for ticker in args.tickers:
            query = f'"{ticker}" OR "${ticker}"'
            for sub in args.subreddits:
                budget.spend()
                for post in reddit.subreddit(sub).search(query, sort="relevance", time_filter=args.time, limit=args.limit):
                    budget.spend()
                    post.comment_sort = "top"
                    post.comments.replace_more(limit=0)
                    results.append({
                        "ticker": ticker,
                        "subreddit": sub,
                        "title": post.title,
                        "body": post.selftext,
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "created_utc": post.created_utc,
                        "url": f"https://www.reddit.com{post.permalink}",
                        "top_comments": [
                            {"body": c.body, "score": c.score}
                            for c in post.comments[: args.comments]
                        ],
                    })
    except RuntimeError as e:
        print(f"Stopped early: {e}")

    out = CACHE_DIR / f"results-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"Saved {len(results)} posts to {out} ({budget.used} requests)")


if __name__ == "__main__":
    main()
