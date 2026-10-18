import unittest

from scout import build_rows


class BuildRowsTest(unittest.TestCase):
    def test_outlier_is_views_over_subscribers(self):
        videos = {"items": [{
            "id": "abc",
            "snippet": {"title": "T", "channelId": "C1", "channelTitle": "Chan", "publishedAt": "2026-10-01T00:00:00Z"},
            "statistics": {"viewCount": "5000", "likeCount": "100", "commentCount": "7"},
        }]}
        channels = {"items": [{"id": "C1", "statistics": {"subscriberCount": "500"}}]}
        [row] = build_rows(videos, channels)
        self.assertEqual(row["outlier"], 10.0)
        self.assertEqual(row["views"], 5000)
        self.assertEqual(row["subs"], 500)

    def test_hidden_subscriber_count_gives_no_score(self):
        videos = {"items": [{
            "id": "abc",
            "snippet": {"title": "T", "channelId": "C1", "channelTitle": "Chan", "publishedAt": "x"},
            "statistics": {"viewCount": "5000"},
        }]}
        channels = {"items": [{"id": "C1", "statistics": {}}]}
        [row] = build_rows(videos, channels)
        self.assertIsNone(row["outlier"])
        self.assertIsNone(row["subs"])
        self.assertIsNone(row["likes"])

    def test_missing_views_counts_as_zero(self):
        videos = {"items": [{
            "id": "abc",
            "snippet": {"title": "T", "channelId": "C1", "channelTitle": "Chan", "publishedAt": "x"},
            "statistics": {},
        }]}
        channels = {"items": [{"id": "C1", "statistics": {"subscriberCount": "100"}}]}
        [row] = build_rows(videos, channels)
        self.assertEqual(row["views"], 0)
        self.assertEqual(row["outlier"], 0.0)


if __name__ == "__main__":
    unittest.main()
