# scripts/test_deai.py
# -*- coding: utf-8 -*-
import unittest
import deai


class TestDeai(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = deai.load_rules()

    def test_rules_loaded(self):
        self.assertGreater(len(self.rules["一"]), 0)
        self.assertGreater(len(self.rules["二"]), 0)

    def test_ai_text_high_score(self):
        text = ("首先，我们要明确的是，众所周知AI赋能已经成为一种趋势。"
                "总而言之，我们要从底层逻辑出发，致力于实现价值最大化！")
        hits, score = deai.scan(text, self.rules)
        self.assertGreater(score, 40)
        self.assertGreater(len(hits), 3)

    def test_natural_text_low_score(self):
        text = ("昨晚跟朋友吃饭，他吐槽说刚分手。我问他咋了，"
                "他说女朋友觉得他不上进。我劝他别急。")
        _, score = deai.scan(text, self.rules)
        self.assertLess(score, 20)

    def test_protect_facts(self):
        text = "他花了 3000 元，买了部 iPhone 15，说'值得'。"
        masked, protected = deai.protect_facts(text)
        self.assertGreater(len(protected), 0)
        # 数字和英文名应被占位符替换
        self.assertNotIn("3000", masked.replace("{F", ""))  # 数字被锁定
        self.assertIn("{F", masked)

    def test_rating(self):
        self.assertIn("自然", deai.rating(10))
        self.assertIn("重度", deai.rating(80))


if __name__ == "__main__":
    unittest.main()
