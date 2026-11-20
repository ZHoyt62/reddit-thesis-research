# reddit-thesis-research

A small, read-only Python script for personal investment research. It searches a few
investing subreddits for stock tickers and saves post titles, bodies and top comments to
a local JSON file.

## How the data is used

- **Personal and non-commercial.** One individual uses this for their own long-term
  investing research. There is no app, website, or other users.
- **Read-only.** The script only reads public posts and comments. It never posts, comments,
  votes, or sends messages, and the client is set to `read_only`.
- **Summarized, then checked.** Results are summarized by a personal AI research assistant
  (Claude) and checked against SEC filings and company reports. Reddit content is used as a
  sentiment signal, not as a source of facts.
- **Short cache only.** Result files live in a local `cache/` folder and are deleted after
  7 days. Nothing is stored long term or in a database.
- **No resale, no redistribution, and no model training.** Data is never sold, shared,
  or used to train any machine-learning model.

## Rate limits

- At most 15 API requests per run and 6 runs per day (under 100 requests a day).
- A 2-second pause between requests.

## Subreddits

r/stocks, r/investing, r/SecurityAnalysis, r/ValueInvesting, r/StockMarket
(change with `--subreddits`).

## Setup

```bash
pip install -r requirements.txt
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USER_AGENT="script:reddit-thesis-research:v0.1 (read-only)"
python research.py NVDA MSFT --limit 3 --comments 5
```

Credentials are read from environment variables only and are never committed.

## License

MIT
