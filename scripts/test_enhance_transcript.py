# scripts/test_enhance_transcript.py
# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

import enhance_transcript as et


class TestEnhance(unittest.TestCase):
    def test_fix_glossary(self):
        mapping = {"皇阿码": "皇阿玛", "郭浩南": "郭浩楠"}
        text = "皇阿码今天和郭浩南一起去吃饭"
        self.assertEqual(et.fix_glossary(text, mapping), "皇阿玛今天和郭浩楠一起去吃饭")

    def test_fix_long_first(self):
        # 长词优先替换：不会把"iPhone15"里的"15"单独误替换
        mapping = {"iPhone 15": "iPhone15", "15": "十五"}
        text = "他买了台 iPhone 15"
        self.assertEqual(et.fix_glossary(text, mapping), "他买了台 iPhone15")

    def test_remove_fillers(self):
        text = "那个我觉得就是怎么说呢，其实吧这个方案还行"
        out = et.remove_fillers(text, ["那个", "就是", "怎么说呢", "其实吧"])
        self.assertNotIn("那个", out)
        self.assertNotIn("就是", out)

    def test_split_paragraphs(self):
        text = "第一句。第二句！第三句？第四句。"
        out = et.split_paragraphs(text, max_len=8)
        self.assertIn("\n", out)
        self.assertGreaterEqual(len(out.split("\n")), 2)

    def test_load_glossary_exists(self):
        mapping = et.load_glossary()
        self.assertIsInstance(mapping, dict)


if __name__ == "__main__":
    unittest.main()
