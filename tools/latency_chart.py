"""Latency chart for the report / PPT: 20 x POST /api/invoices (one series)."""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(__file__), "..")
data = json.load(open(os.path.join(ROOT, "evidence", "latency_results.json")))
s, samples = data["summary"], data["samples"]
x = [p["call"] for p in samples]; y = [p["ms"] for p in samples]

plt.rcParams.update({"font.family": "Segoe UI", "font.size": 13})
fig, ax = plt.subplots(figsize=(12, 5.4), dpi=150)
fig.patch.set_facecolor("white")
ax.bar(x, y, width=0.6, color="#0E9696", edgecolor="white", linewidth=2, zorder=3)
ax.hlines(s["average_ms"], 0.5, 20.5, color="#0F2040", linewidth=2, linestyle=(0, (6, 4)), zorder=4)
ax.set_xlim(0.3, 23.2)
ax.text(20.8, s["average_ms"], f"avg {s['average_ms']:.0f} ms", ha="left", va="center",
        color="#0F2040", fontsize=13, fontweight="bold")
imin, imax = y.index(min(y)), y.index(max(y))
for i, lbl in ((imin, "min"), (imax, "max")):
    ax.annotate(f"{lbl} {y[i]:.0f}", (x[i], y[i]), xytext=(0, 6), textcoords="offset points",
                ha="center", fontsize=11, color="#3C465A")
ax.set_xticks(x)
ax.set_xlabel("POST /api/invoices call # (each = full IssueInvoiceFlow incl. notarisation)", color="#3C465A")
ax.set_ylabel("End-to-end latency (ms)", color="#3C465A")
ax.set_title("REST -> Corda write latency, 20 sequential calls (2 warm-up calls excluded)",
             loc="left", fontsize=15, fontweight="bold", color="#0F2040")
ax.set_ylim(0, max(y) * 1.18)
ax.grid(axis="y", color="#E3E7EE", zorder=0)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
for sp in ("left", "bottom"):
    ax.spines[sp].set_color("#B8C0CC")
ax.tick_params(colors="#5A6270")
fig.tight_layout()
out = os.path.join(ROOT, "docs", "diagrams", "latency_chart.png")
fig.savefig(out)
print(out)
