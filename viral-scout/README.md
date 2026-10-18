# viral-scout

A personal tool that finds recent YouTube videos for a search term and ranks them by how far they outperformed their channel's audience.

It uses the official YouTube Data API v3 only. There is no scraping.

## Setup

1. Create a YouTube Data API key in Google Cloud Console and enable "YouTube Data API v3".
2. `export YOUTUBE_API_KEY=your-key`

Python 3 standard library only, no install step.

## Use

```
python scout.py search "home coffee" --days 30 --limit 25
python scout.py top --limit 20
```

- `search` queries the API, stores results in `scout.db` (git-ignored), and prints them ranked by outlier score.
- `top` ranks everything already stored.

Outlier score = views ÷ channel subscribers. Videos from channels with hidden subscriber counts show `n/a`.

## Quota

A `search` call costs about 100 quota units, and the default daily quota is 10,000. Each `search` run makes one search call plus a few cheap lookups, so roughly 90 searches a day fit in the default quota.

## Tests

```
python -m unittest test_scout.py
```

## Scope

Use the output to study formats, hooks, and pacing. Don't re-upload other people's videos. Recreate ideas in your own footage and wording.
