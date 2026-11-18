"""Turns the raw Gradle test log into evidence/test_results.txt (clean) and keeps the raw log."""
import glob
import os
import re
import shutil
import xml.etree.ElementTree as ET

ROOT = os.path.join(os.path.dirname(__file__), "..")
raw = os.path.join(ROOT, "evidence", "test_results.txt")
full = os.path.join(ROOT, "evidence", "test_results_full_log.txt")
shutil.copyfile(raw, full)

keep = re.compile(r"^(> gradlew|> Task|\S+Tests > |BUILD |\d+ actionable)")
lines = [l.rstrip() for l in open(full, encoding="utf-8", errors="replace") if keep.match(l)]

summary = ["", "=" * 78, " JUnit summary (from build/test-results XML)", "=" * 78,
           f" {'Test class':<46}{'tests':>7}{'failed':>8}{'time s':>10}", "-" * 78]
tot = fail = 0
for p in sorted(glob.glob(os.path.join(ROOT, "**", "build", "test-results", "test", "*.xml"), recursive=True)):
    r = ET.parse(p).getroot()
    t, f = int(r.get("tests")), int(r.get("failures")) + int(r.get("errors"))
    tot += t; fail += f
    summary.append(f" {r.get('name'):<46}{t:>7}{f:>8}{float(r.get('time')):>10.1f}")
summary += ["-" * 78, f" {'TOTAL':<46}{tot:>7}{fail:>8}", "=" * 78,
            " Note: the flow tests that expect failures make Corda log the rejected flows; those",
            " log lines are in test_results_full_log.txt and are not test failures."]
open(raw, "w", encoding="utf-8").write("\n".join(lines + summary) + "\n")
print("\n".join(summary))
