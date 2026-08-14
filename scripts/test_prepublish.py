# scripts/test_prepublish.py
# -*- coding: utf-8 -*-
import unittest
import prepublish_check as pp


class TestPrepublish(unittest.TestCase):
    def test_check_length_ok(self):
        lvl, msg = pp.check_length("这是一段五十字左右的正常文案内容测试一下字数长度是否符合平台要求范围之内。", "douyin")
        self.assertEqual(lvl, 0)

    def test_check_length_short(self):
        lvl, _ = pp.check_length("太短", "douyin")
        self.assertEqual(lvl, 1)

    def test_check_length_long(self):
        lvl, _ = pp.check_length("字" * 600, "douyin")
        self.assertEqual(lvl, 1)

    def test_check_title_banned(self):
        words = pp.compliance.load_words()
        lvl, _ = pp.check_title("加微信免费领取", words)
        self.assertEqual(lvl, 2)

    def test_check_title_ok(self):
        words = pp.compliance.load_words()
        lvl, _ = pp.check_title("男生冷暴力的时候在想什么", words)
        self.assertEqual(lvl, 0)


if __name__ == "__main__":
    unittest.main()
