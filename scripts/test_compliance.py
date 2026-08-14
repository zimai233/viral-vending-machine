# scripts/test_compliance.py
# -*- coding: utf-8 -*-
import unittest
import compliance


class TestCompliance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.words = compliance.load_words()

    def test_words_loaded(self):
        self.assertGreater(len(self.words["一"]), 10)
        self.assertGreater(len(self.words["二"]), 10)

    def test_hard_word_detected(self):
        text = "加微信领取资料，免费赠送"
        hits, hard = compliance.check(text, self.words)
        self.assertGreater(hard, 0)
        self.assertEqual(compliance.LEVELS[hits[0][0]], "🔴硬性")

    def test_risk_word_detected(self):
        text = "这款产品全网最低价，赶紧抢购"
        hits, hard = compliance.check(text, self.words)
        self.assertEqual(hard, 0)
        levels = [h[0] for h in hits]
        self.assertIn("二", levels)

    def test_clean_text(self):
        text = "昨晚跟朋友吃饭，聊到感情话题，他刚分手，我劝他先过好自己。"
        hits, hard = compliance.check(text, self.words)
        self.assertEqual(len(hits), 0)
        self.assertEqual(hard, 0)


if __name__ == "__main__":
    unittest.main()
