"""Short results-only demo: intro card + live Swagger UI recording + result cards (no code, no terminal)."""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import render as R

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "deliverables", "Topic25_Project_Demo_24BTRBT029.mp4")
NAVY, TEAL, WHITE, SOFT = (11, 26, 51), (20, 196, 184), (255, 255, 255), (201, 214, 232)
GREEN = (91, 214, 142)
FB = lambda s: ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", s)
FR = lambda s: ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", s)


def still(name, im, dur):
    p = os.path.join(R.FRAMES, name + ".png"); im.save(p)
    out = os.path.join(R.SEGS, name + ".mp4")
    subprocess.run([R.FFMPEG, "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-t", str(dur), "-i", p,
                    "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "-an", out],
                   check=True)
    return out


def base(kicker, title):
    im = Image.new("RGB", (1920, 1080), NAVY); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 14, 1080), fill=TEAL)
    d.text((120, 70), kicker.upper(), font=FB(26), fill=TEAL)
    d.text((120, 110), title, font=FB(60), fill=WHITE)
    d.rectangle((122, 200, 280, 207), fill=TEAL)
    d.text((120, 1010), "Topic 25 - External REST API Integration with a Corda CorDapp   |   Suraj Patel (24BTRBT029)",
           font=FR(22), fill=(138, 155, 181))
    return im, d


# results card: big numbers
im, d = base("Results", "What the live run proved")
tiles = [("42 / 42", "automated tests passing", "15 contract  -  6 flow  -  21 REST API"),
         ("11", "REST endpoints working", "issue, list, get, approve, pay, reject, history ..."),
         ("3 nodes", "Corda 4.12 network", "Notary + SellerCorp (Mumbai) + BuyerCorp"),
         ("401 400 404 422", "errors handled correctly", "API key, validation, unknown id, contract rules"),
         ("583 ms", "average invoice issue", "full flow: 2 signatures + notary (min 391, max 766)"),
         ("100 %", "vaults in agreement", "seller and buyer hold the same invoices")]
for i, (big, h, sub) in enumerate(tiles):
    x = 120 + (i % 3) * 580; y = 270 + (i // 3) * 350
    d.rounded_rectangle((x, y, x + 540, y + 310), radius=22, fill=(19, 40, 74), outline=(28, 54, 96), width=2)
    d.rectangle((x, y, x + 540, y + 8), fill=TEAL)
    size = 76 if len(big) < 9 else 54
    d.text((x + 36, y + 50), big, font=FB(size), fill=GREEN if i in (0, 5) else WHITE)
    d.text((x + 36, y + 170), h, font=FB(30), fill=WHITE)
    d.text((x + 36, y + 222), sub, font=FR(22), fill=SOFT)
results = still("r_results", im, 10)

# latency chart card
im, d = base("Performance", "Latency of 20 invoice issues through the API")
chart = Image.open(os.path.join(ROOT, "docs", "diagrams", "latency_chart.png")).convert("RGB")
w = 1680; h = int(chart.height * w / chart.width)
d.rounded_rectangle((110, 250, 110 + w + 20, 250 + h + 20), radius=18, fill=WHITE)
im.paste(chart.resize((w, h), Image.LANCZOS), (120, 260))
d.text((120, 270 + h + 30), "Reading invoices (GET) averages 78 ms - almost all of the write time is Corda's signing and notarisation.",
       font=FR(28), fill=SOFT)
latency = still("r_latency", im, 9)

segs = [
    R.title_card("r_intro", "Topic 25  |  Corda Development  |  Mini project demo",
                 "Corda REST API Integration", [
                     "Invoices shared by SellerCorp and BuyerCorp on a Corda 4.12 ledger",
                     "Outside systems use it through a simple REST API (Swagger UI shown here)",
                     "Suraj Patel (24BTRBT029)"], 7),
    R.title_card("r_live", "Live demo", "The working application", [
        "Seller issues an invoice  ->  buyer approves  ->  buyer pays",
        "Wrong key, invalid amount, paying too early and unknown id are all rejected",
        "Full history of the invoice at the end"], 6),
    os.path.join(R.SEGS, "s06_swagger.mp4"),
    results, latency,
    R.title_card("r_end", "Thank you", "Project complete", [
        "Suraj Patel  -  24BTRBT029",
        "CSE (Blockchain Technology), Semester V  -  Jain (Deemed-to-be University)",
        "github.com/Momo-1628/corda-rest-api-integration"], 6),
]
lst = os.path.join(R.DEMO, "concat_results.txt")
with open(lst, "w") as f:
    for s in segs:
        f.write(f"file '{s}'\n")
joined = os.path.join(R.DEMO, "joined_results.mp4")
subprocess.run([R.FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)
subprocess.run([R.FFMPEG, "-y", "-v", "error", "-i", joined, "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "32k", "-shortest",
                "-movflags", "+faststart", OUT], check=True)
print("written", OUT)
