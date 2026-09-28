"""Сводка JUnit XML: по каждому упавшему тесту — первая строка причины. Использование:
    python tests/tools/junit_summary.py docs/evidence/before_fix.xml [--passed]
"""
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict


def main(path, show_passed=False):
    root = ET.parse(path).getroot()
    by_file = defaultdict(list)
    for tc in root.iter("testcase"):
        name = f"{tc.get('classname')}::{tc.get('name')}"
        fail = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        if fail is not None:
            msg = (fail.get("message") or fail.text or "").strip().splitlines()
            by_file[tc.get("classname")].append(("FAIL", tc.get("name"), msg[0][:220] if msg else ""))
        elif tc.find("skipped") is not None:
            by_file[tc.get("classname")].append(("SKIP", tc.get("name"), (tc.find("skipped").get("message") or "")[:120]))
        elif show_passed:
            by_file[tc.get("classname")].append(("PASS", tc.get("name"), ""))
    for cls in sorted(by_file):
        print(f"\n## {cls}")
        for status, name, msg in by_file[cls]:
            name = name if len(name) <= 110 else name[:100] + "…]"
            print(f"  [{status}] {name}  {msg[:220]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], "--passed" in sys.argv)
