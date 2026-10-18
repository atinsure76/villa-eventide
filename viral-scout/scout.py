#!/usr/bin/env python3
"""Personal viral-video scout built on the official YouTube Data API v3.

For a search term it finds recent videos, pulls their stats and channel
subscriber counts, and scores each one as an outlier:

    outlier = views / subscribers

A high score means a video did far better than its channel's audience
would predict, which is the signal worth studying.

Usage:
    export YOUTUBE_API_KEY=...
    python scout.py search "home coffee" --days 30 --limit 25
    python scout.py top --limit 20
"""
import argparse
import json
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://www.googleapis.com/youtube/v3"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scout.db")


def api_get(endpoint, key, **params):
    params["key"] = key
    url = f"{API}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def to_int(value):
    return int(value) if value is not None else None


def build_rows(videos, channels):
    """Join videos.list and channels.list payloads into flat rows."""
    subs_by_channel = {
        c["id"]: to_int(c.get("statistics", {}).get("subscriberCount"))
        for c in channels.get("items", [])
    }
    rows = []
    for item in videos.get("items", []):
        stats = item.get("statistics", {})
        snippet = item["snippet"]
        views = to_int(stats.get("viewCount")) or 0
        subs = subs_by_channel.get(snippet["channelId"])
        rows.append({
            "video_id": item["id"],
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "channel_id": snippet["channelId"],
            "published": snippet["publishedAt"],
            "views": views,
            "likes": to_int(stats.get("likeCount")),
            "comments": to_int(stats.get("commentCount")),
            "subs": subs,
            # Subscriber counts can be hidden by the channel owner.
            "outlier": round(views / subs, 3) if subs else None,
        })
    return rows


def search(query, key, days, limit):
    after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = api_get(
        "search", key, part="snippet", q=query, type="video",
        order="viewCount", publishedAfter=after, maxResults=min(limit, 50),
    )
    video_ids = [i["id"]["videoId"] for i in found.get("items", [])]
    if not video_ids:
        return []
    videos = api_get("videos", key, part="snippet,statistics", id=",".join(video_ids))
    channel_ids = sorted({i["snippet"]["channelId"] for i in videos.get("items", [])})
    channels = api_get("channels", key, part="statistics", id=",".join(channel_ids))
    return build_rows(videos, channels)


def open_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            query TEXT,
            title TEXT,
            channel TEXT,
            channel_id TEXT,
            published TEXT,
            views INTEGER,
            likes INTEGER,
            comments INTEGER,
            subs INTEGER,
            outlier REAL,
            fetched_at TEXT
        )
    """)
    return db


def save(db, query, rows):
    now = datetime.now(timezone.utc).isoformat()
    db.executemany("""
        INSERT OR REPLACE INTO videos VALUES
        (:video_id, :query, :title, :channel, :channel_id, :published,
         :views, :likes, :comments, :subs, :outlier, :fetched_at)
    """, [dict(r, query=query, fetched_at=now) for r in rows])
    db.commit()


def print_table(rows):
    print(f"{'outlier':>8}  {'views':>10}  {'subs':>9}  channel / title")
    for r in rows:
        score = f"{r['outlier']:.2f}" if r["outlier"] is not None else "n/a"
        subs = f"{r['subs']:,}" if r["subs"] is not None else "hidden"
        print(f"{score:>8}  {r['views']:>10,}  {subs:>9}  {r['channel']} / {r['title']}")
        print(f"{'':>8}  https://www.youtube.com/watch?v={r['video_id']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="fetch and store recent videos for a query")
    s.add_argument("query")
    s.add_argument("--days", type=int, default=30)
    s.add_argument("--limit", type=int, default=25)

    t = sub.add_parser("top", help="show stored videos ranked by outlier score")
    t.add_argument("--limit", type=int, default=20)

    args = parser.parse_args(argv)
    db = open_db()

    if args.cmd == "search":
        key = os.environ.get("YOUTUBE_API_KEY")
        if not key:
            sys.exit("Set YOUTUBE_API_KEY first.")
        rows = search(args.query, key, args.days, args.limit)
        save(db, args.query, rows)
        rows.sort(key=lambda r: (r["outlier"] is None, -(r["outlier"] or 0)))
        print_table(rows)
    else:
        cur = db.execute("""
            SELECT video_id, title, channel, views, subs, outlier FROM videos
            ORDER BY outlier IS NULL, outlier DESC LIMIT ?
        """, (args.limit,))
        cols = ["video_id", "title", "channel", "views", "subs", "outlier"]
        print_table([dict(zip(cols, r)) for r in cur])


if __name__ == "__main__":
    main()
