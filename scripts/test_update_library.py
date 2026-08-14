# scripts/test_update_library.py
# -*- coding: utf-8 -*-
import glob
import json
import os
import tempfile
import unittest

import update_library as ul


SAMPLE = {
    "platform": "xhs",
    "items": [
        {
            "platform": "xiaohongshu",
            "source_id": "n1",
            "title": "AI工具亲测",
            "content": "这篇讲的是如何用AI提高效率……",
            "tags": ["AI工具"],
            "author": "博主A",
            "author_id": "hash1",
            "url": "https://www.xiaohongshu.com/explore/n1",
            "likes": 12000,
            "publish_time": 0,
        }
    ],
}


class TestUpdateLibrary(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertEqual(ul.sanitize("博主A/大:神?"), "博主A_大_神")

    def test_framework_tags(self):
        self.assertIn("揭秘", ul.framework_tags({"title": "男生绝对不会告诉你的秘密"}))
        self.assertIn("清单", ul.framework_tags({"title": "如何筛选不正常的男生"}))
        self.assertIn("金句", ul.framework_tags({"title": "爱是尽可能不包容"}))

    def test_build_case_md(self):
        item = SAMPLE["items"][0]
        md = ul.build_case_md(item)
        self.assertIn("AI工具亲测", md)
        self.assertIn("1.2万", md)
        self.assertIn("框架:", md)

    def test_update_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cases = ul.CASES
            ul.CASES = os.path.join(tmp, "cases")
            try:
                ul.update(SAMPLE, "AI工具")
                ul.update(SAMPLE, "AI工具")
                author_file = glob.glob(os.path.join(ul.CASES, "博主A.md"))
                self.assertTrue(author_file)
                content = open(author_file[0], encoding="utf-8").read()
                self.assertEqual(content.count("AI工具亲测"), 1)
                self.assertEqual(content.count("<!-- id: n1 -->"), 1)
                # 索引生成且含博主
                idx = open(os.path.join(ul.CASES, "index.md"), encoding="utf-8").read()
                self.assertIn("博主A", idx)
            finally:
                ul.CASES = old_cases

    def test_update_merge_new_items(self):
        """新增案例应合并进已有文件，不丢旧的。"""
        with tempfile.TemporaryDirectory() as tmp:
            old_cases = ul.CASES
            ul.CASES = os.path.join(tmp, "cases")
            try:
                sample2 = json.loads(json.dumps(SAMPLE))
                sample2["items"][0]["source_id"] = "n2"
                ul.update(SAMPLE, "AI工具")
                ul.update(sample2, "AI工具")
                content = open(os.path.join(ul.CASES, "博主A.md"), encoding="utf-8").read()
                self.assertIn("<!-- id: n1 -->", content)
                self.assertIn("<!-- id: n2 -->", content)
            finally:
                ul.CASES = old_cases


if __name__ == "__main__":
    unittest.main()
