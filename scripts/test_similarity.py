# -*- coding: utf-8 -*-
import unittest
import similarity as sim


class TestSimilarity(unittest.TestCase):
    def test_identical_text_high(self):
        t = "今天推荐三个好用的AI工具，能极大提升工作效率。"
        self.assertGreater(sim.similarity(t, t), 0.9)

    def test_different_text_low(self):
        a = "今天推荐三个好用的AI工具，能极大提升工作效率。"
        b = "周末去爬山，天气很好，风景很美。"
        self.assertLess(sim.similarity(a, b), 0.3)

    def test_rewrite_drops_similarity(self):
        a = "今天推荐三个好用的AI工具，能极大提升工作效率。"
        b = "我最近发现几款特别好用的效率软件，直接改变了我每天干活的方式。"
        self.assertLess(sim.similarity(a, b), 0.6)

    def test_six_char_run_detected(self):
        a = "今天推荐三个好用的AI工具"
        b = "今天推荐三个好用的AI工具，超级好用。"
        self.assertTrue(sim.has_six_char_run(a, b))


if __name__ == "__main__":
    unittest.main()
