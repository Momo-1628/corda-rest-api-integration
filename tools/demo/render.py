"""Renders recorded casts (rec.py) and title cards into 1920x1080 H.264 segments for the demo video."""
import json
import os
import re
import shutil
import subprocess
import glob
import textwrap

from PIL import Image, ImageDraw, ImageFont

DEMO = r"D:\corda-rest-api-run\demo"
CASTS, FRAMES, SEGS = (os.path.join(DEMO, d) for d in ("casts", "frames", "segments"))
for d in (FRAMES, SEGS):
    os.makedirs(d, exist_ok=True)
FFBIN = glob.glob(os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin"))[0]
FFMPEG = os.path.join(FFBIN, "ffmpeg.exe")

W, H = 1920, 1080
F = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 20)
FB = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 20)
UI = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 19)
UIB = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 19)
BG = (22, 26, 34); BAR = (36, 41, 52); FG = (214, 220, 228); DIM = (120, 130, 146)
GREEN = (80, 220, 130); RED = (255, 105, 105); YELLOW = (240, 200, 90); CYAN = (90, 200, 230)
MAGENTA = (200, 150, 255); ORANGE = (255, 170, 80); TEAL = (20, 196, 184); NAVY = (11, 26, 51)
CW = F.getbbox("M")[2]; LH = 26
TOP, BOTTOM = 56, 46
ROWS = (H - TOP - BOTTOM - 20) // LH
COLS = (W - 56) // CW
PROMPT = "PS C:\\Users\\LENOVO\\corda-rest-api> "


def colour(line):
    s = line.strip()
    if line.startswith(PROMPT):
        return YELLOW, True
    if re.search(r"\bFAILED\b|Exception:|\bERROR\b", line) and "0 CHECK" not in line and "FLOW_FAILED" not in line:
        return RED, False
    if re.search(r"PASS|BUILD SUCCESSFUL|started up|ALL CHECKS PASSED|ready after|are up|Stopped", line):
        return GREEN, bool(re.search(r"BUILD|ALL CHECKS|started up|are up", line))
    if re.search(r"HTTP (4|5)\d\d", line) or '"success": false' in line or '"success":false' in line:
        return ORANGE, False
    if re.search(r"HTTP 20\d", line):
        return CYAN, False
    if line.startswith(("$ ", "> Task", "=====", "[")) and not line.startswith("[INFO"):
        return YELLOW, line.startswith(("[", "$ "))
    if s.startswith("+-"):
        return MAGENTA, False
    if s.startswith(("=", "---")):
        return DIM, False
    return FG, False


def wrap(line):
    if len(line) <= COLS:
        return [line]
    return textwrap.wrap(line, COLS, subsequent_indent="    ", drop_whitespace=False, replace_whitespace=False) or [line]


class Term:
    def __init__(self, title, recorded_at):
        self.title, self.recorded_at, self.lines = title, recorded_at, []

    def frame(self, path, typed=None, cursor=True, elapsed=None, note=None):
        im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, TOP - 8), fill=BAR)
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse((22 + i * 28, 16, 38 + i * 28, 32), fill=c)
        tw = d.textbbox((0, 0), self.title, font=UIB)[2]
        d.text(((W - tw) / 2, 12), self.title, font=UIB, fill=(225, 230, 238))
        rows = list(self.lines)
        if typed is not None:
            rows.append(PROMPT + typed)
        flat = []
        for r in rows:
            flat += [(seg, r) for seg in wrap(r)]
        flat = flat[-ROWS:]
        y = TOP + 8
        for seg, orig in flat:
            col, bold = colour(orig)
            if orig.startswith(PROMPT) and seg.startswith(PROMPT):
                d.text((28, y), PROMPT, font=FB, fill=TEAL)
                d.text((28 + CW * len(PROMPT), y), seg[len(PROMPT):], font=FB, fill=YELLOW)
            else:
                d.text((28, y), seg, font=FB if bold else F, fill=col)
            y += LH
        if cursor:
            last = flat[-1][0] if flat else ""
            cx = 28 + CW * len(last) if typed is not None else 28
            cy = y - LH if typed is not None else y
            d.rectangle((cx + 2, cy + 3, cx + CW, cy + LH - 3), fill=(200, 205, 215))
        # status bar
        d.rectangle((0, H - BOTTOM, W, H), fill=BAR)
        d.text((24, H - BOTTOM + 11), f"Real run recorded {self.recorded_at}  |  Suraj Patel (24BTRBT029)", font=UI, fill=DIM)
        right = ""
        if elapsed is not None:
            right = f"real elapsed time  {int(elapsed // 60):02d}:{elapsed % 60:04.1f}"
        if note:
            right = note + "     " + right
        if right:
            rw = d.textbbox((0, 0), right, font=UI)[2]
            d.text((W - rw - 24, H - BOTTOM + 11), right, font=UIB if note else UI, fill=YELLOW if note else DIM)
        im.save(path, compress_level=1)


def encode(list_file, out):
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", list_file,
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-r", "30", "-an", out], check=True)


def render_cast(name, title, keep_prior=None, max_gap=1.1, tail_hold=3.0, min_group=0.045):
    cast = json.load(open(os.path.join(CASTS, name + ".json"), encoding="utf-8"))
    fdir = os.path.join(FRAMES, name)
    shutil.rmtree(fdir, ignore_errors=True); os.makedirs(fdir)
    t = Term(title, cast["recorded_at"])
    if keep_prior:
        t.lines = list(keep_prior)
    items = []  # (png, duration)
    n = [0]

    def snap(dur, **kw):
        p = os.path.join(fdir, f"{n[0]:05d}.png"); n[0] += 1
        t.frame(p, **kw); items.append((p, dur))

    snap(0.8, typed="", elapsed=0.0)
    cmd = cast["display"]
    step = max(1, len(cmd) // 60)
    for i in range(step, len(cmd) + step, step):
        snap(0.035, typed=cmd[:i], elapsed=0.0)
    snap(0.6, typed=cmd, elapsed=0.0)
    t.lines.append(PROMPT + cmd)
    ev = cast["events"]
    i, last_t = 0, 0.0
    while i < len(ev):
        # group lines that arrived within 80 ms (bursts) but cap the group size for a scrolling feel
        j = i + 1
        while j < len(ev) and ev[j][0] - ev[j - 1][0] < 0.08 and j - i < 6:
            j += 1
        gap = ev[i][0] - last_t
        note = f"waiting {gap:.0f} s (shortened)" if gap > 6 else None
        if items:
            # extend the previous frame by the (compressed) wait before these lines arrive
            shown = gap if gap < 0.35 else min(max_gap, 0.35 + (gap - 0.35) * 0.15)
            shown = max(shown, 0.045)
            if note:
                # show the waiting note during the pause
                p = os.path.join(fdir, f"{n[0]:05d}.png"); n[0] += 1
                t.frame(p, elapsed=last_t, note=note); items.append((p, max(shown, 1.2)))
            else:
                prev = items[-1]; items[-1] = (prev[0], prev[1] + shown)
        t.lines += [e[1] for e in ev[i:j]]
        last_t = ev[j - 1][0]
        snap(min_group, elapsed=last_t)
        i = j
    snap(tail_hold, typed="", elapsed=cast["duration"])
    lst = os.path.join(fdir, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p, d in items:
            f.write(f"file '{p}'\nduration {d:.3f}\n")
        f.write(f"file '{items[-1][0]}'\n")
    out = os.path.join(SEGS, name + ".mp4")
    encode(lst, out)
    print(name, "frames", len(items), "length %.1f s" % sum(d for _, d in items))
    return out


def title_card(name, step, title, lines, dur=5.0):
    im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 14, H), fill=TEAL)
    big = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 66)
    mid = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 34)
    small = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
    d.text((140, 250), step.upper(), font=small, fill=TEAL)
    d.text((140, 300), title, font=big, fill=(255, 255, 255))
    d.rectangle((142, 404, 300, 412), fill=TEAL)
    y = 460
    for ln in lines:
        d.text((140, y), "\u25A0", font=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22), fill=TEAL)
        d.text((180, y - 8), ln, font=mid, fill=(201, 214, 232)); y += 62
    d.text((140, H - 90), "Topic 25 - External REST API Integration with a Corda CorDapp   |   Suraj Patel (24BTRBT029)",
           font=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22), fill=(138, 155, 181))
    fdir = os.path.join(FRAMES, name); os.makedirs(fdir, exist_ok=True)
    p = os.path.join(fdir, "card.png"); im.save(p)
    out = os.path.join(SEGS, name + ".mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-t", f"{dur}", "-i", p,
                    "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "-an", out],
                   check=True)
    return out


def webm_to_segment(src, name, trim_start=0.0):
    out = os.path.join(SEGS, name + ".mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", f"{trim_start}", "-i", src,
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0B1A33,fps=30,format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "-an", out], check=True)
    return out
