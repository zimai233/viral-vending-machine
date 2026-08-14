# -*- coding: utf-8 -*-
"""一键运行全部离线单元测试。"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = ["test_collect.py", "test_update_library.py", "test_similarity.py",
         "test_deai.py", "test_enhance_transcript.py", "test_compliance.py",
         "test_prepublish.py"]

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

failed = []
for t in TESTS:
    print(f"--- {t} ---", flush=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, t)])
    if r.returncode != 0:
        failed.append(t)
    print()

if failed:
    print(f"失败: {failed}")
    sys.exit(1)
print("全部离线测试通过 ✓")
