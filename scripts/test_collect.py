# scripts/test_collect.py
# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest

import collect


class TestParsing(unittest.TestCase):
    def test_platform_xhs(self):
        self.assertEqual(collect.detect_platform("https://www.xiaohongshu.com/explore/abc"), "xhs")

    def test_platform_douyin(self):
        self.assertEqual(collect.detect_platform("https://www.douyin.com/video/123"), "dy")

    def test_extract_creator_id_xhs(self):
        url = "https://www.xiaohongshu.com/user/profile/5f0e1234567890abcdef?xsec_token=tk&xsec_source=pc"
        self.assertEqual(collect.extract_creator_id("xhs", url), "5f0e1234567890abcdef")

    def test_extract_creator_id_douyin(self):
        url = "https://www.douyin.com/user/MS4wLjABAAAAxyz"
        self.assertEqual(collect.extract_creator_id("dy", url), "MS4wLjABAAAAxyz")

    def test_extract_note_id_xhs(self):
        url = "https://www.xiaohongshu.com/explore/66f0abcdef123456"
        self.assertEqual(collect.extract_note_id("xhs", url), "66f0abcdef123456")

    def test_extract_aweme_id_douyin(self):
        url = "https://www.douyin.com/video/7381234567890123456"
        self.assertEqual(collect.extract_aweme_id("dy", url), "7381234567890123456")


class TestExtractTags(unittest.TestCase):
    def test_tags_string_form(self):
        self.assertEqual(collect._extract_tags("AI工具,效率,工具推荐"), ["AI工具", "效率", "工具推荐"])

    def test_tags_dict_list_form(self):
        raw = [{"name": "AI工具", "type": "topic"}, {"name": "效率"}]
        self.assertEqual(collect._extract_tags(raw), ["AI工具", "效率"])

    def test_tags_empty(self):
        self.assertEqual(collect._extract_tags(None), [])
        self.assertEqual(collect._extract_tags(""), [])


class TestToInt(unittest.TestCase):
    def test_to_int_plain(self):
        self.assertEqual(collect._to_int("1234"), 1234)
        self.assertEqual(collect._to_int(1234), 1234)

    def test_to_int_comma(self):
        self.assertEqual(collect._to_int("12,345"), 12345)

    def test_to_int_wan(self):
        self.assertEqual(collect._to_int("1.2万"), 12000)

    def test_to_int_garbage(self):
        self.assertEqual(collect._to_int(None), 0)
        self.assertEqual(collect._to_int(""), 0)
        self.assertEqual(collect._to_int("abc"), 0)


class TestBuildMcArgs(unittest.TestCase):
    def test_creator_mode(self):
        args = collect.build_mc_args("xhs", "creator", "5f0e123", 10)
        self.assertIn("--type", args)
        self.assertIn("creator", args)
        self.assertIn("--creator_id", args)
        self.assertIn("5f0e123", args)

    def test_search_mode(self):
        args = collect.build_mc_args("dy", "search", "AI工具", 5)
        self.assertIn("--type", args)
        self.assertIn("search", args)
        self.assertIn("--keywords", args)
        self.assertIn("AI工具", args)


class TestNormalize(unittest.TestCase):
    def test_xhs_normalize_sorts_by_likes(self):
        items = [
            {"note_id": "a", "title": "t", "desc": "d", "tag_list": "AI",
             "liked_count": "100", "nickname": "博主", "note_url": "u"},
            {"note_id": "b", "title": "t", "desc": "d", "liked_count": "500",
             "nickname": "博主", "note_url": "u"},
        ]
        out = collect.normalize("xhs", items, "kw")
        self.assertEqual([r["source_id"] for r in out], ["b", "a"])
        self.assertEqual(out[0]["likes"], 500)
        self.assertEqual(out[1]["tags"], ["AI"])
        self.assertEqual(out[0]["platform"], "xiaohongshu")

    def test_douyin_normalize_fields(self):
        items = [{"aweme_id": "x", "desc": "d", "video_download_url": "vurl",
                  "liked_count": "9", "nickname": "n", "aweme_url": "u"}]
        out = collect.normalize("dy", items, "kw")
        self.assertEqual(out[0]["video_url"], "vurl")
        self.assertEqual(out[0]["platform"], "douyin")
        self.assertEqual(out[0]["likes"], 9)

    def test_normalize_drops_empty_source(self):
        out = collect.normalize("xhs", [{"desc": "no id"}], "kw")
        self.assertEqual(out, [])


class TestReadLatestJson(unittest.TestCase):
    def _make_mc_json(self, mc_dir: str, fname: str, items: list):
        d = os.path.join(mc_dir, "data", "xhs", "json")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, fname), "w", encoding="utf-8") as f:
            json.dump(items, f)

    def test_reads_realistic_contents_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = collect.MC_DIR
            collect.MC_DIR = tmp
            try:
                self._make_mc_json(tmp, "search_contents_20260813.json",
                                   [{"note_id": "n1"}])
                out = collect.read_latest_json("xhs")
                self.assertEqual(out, [{"note_id": "n1"}])
            finally:
                collect.MC_DIR = old

    def test_fallback_to_any_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = collect.MC_DIR
            collect.MC_DIR = tmp
            try:
                self._make_mc_json(tmp, "search_note_20260813.json",
                                   [{"note_id": "n2"}])
                out = collect.read_latest_json("xhs")
                self.assertEqual(out, [{"note_id": "n2"}])
            finally:
                collect.MC_DIR = old

    def test_missing_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = collect.MC_DIR
            collect.MC_DIR = tmp
            try:
                with self.assertRaises(RuntimeError):
                    collect.read_latest_json("xhs")
            finally:
                collect.MC_DIR = old


if __name__ == "__main__":
    unittest.main()
