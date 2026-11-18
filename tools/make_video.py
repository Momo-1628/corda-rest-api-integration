"""Voice-over video: slide PNGs + edge-tts narration from the speaker notes -> MP4 (1920x1080, H.264 + AAC)
with burned-in subtitles (also saved as .srt).  Falls back to pyttsx3 if edge-tts fails."""
import asyncio
import glob
import os
import re
import subprocess
import sys

from pptx import Presentation

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DELIV = os.path.join(ROOT, "deliverables")
WORK = os.path.join(DELIV, "_work", "video")
SLIDES = os.path.join(DELIV, "_work", "slides")
PPTX = os.path.join(DELIV, "Topic25_Corda_REST_API_24BTRBT029.pptx")
MP4 = os.path.join(DELIV, "Topic25_Presentation_24BTRBT029.mp4")
SRT = os.path.join(DELIV, "Topic25_Presentation_24BTRBT029.srt")
FFBIN = glob.glob(os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin"))[0]
FFMPEG, FFPROBE = os.path.join(FFBIN, "ffmpeg.exe"), os.path.join(FFBIN, "ffprobe.exe")
VOICE = "en-IN-PrabhatNeural"
HOLD, FADE = 0.7, 0.5
os.makedirs(WORK, exist_ok=True)

notes = [s.notes_slide.notes_text_frame.text.strip() for s in Presentation(PPTX).slides]
pngs = sorted(glob.glob(os.path.join(SLIDES, "slide_*.png")))
assert len(pngs) == len(notes) == 17, (len(pngs), len(notes))


async def tts_edge(text, path):
    import edge_tts
    await edge_tts.Communicate(text, VOICE, rate="+15%").save(path)


def tts(i, text):
    mp3 = os.path.join(WORK, f"audio_{i:02d}.mp3")
    if os.path.exists(mp3) and os.path.getsize(mp3) > 1000:
        return mp3
    for attempt in range(3):
        try:
            asyncio.run(tts_edge(text, mp3))
            if os.path.getsize(mp3) > 1000:
                return mp3
        except Exception as e:  # network hiccup -> retry, then fall back
            print("edge-tts failed:", e)
    import pyttsx3
    wav = mp3.replace(".mp3", ".wav")
    eng = pyttsx3.init(); eng.save_to_file(text, wav); eng.runAndWait()
    return wav


def duration(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


audios, durs = [], []
for i, n in enumerate(notes, 1):
    a = tts(i, n); d = duration(a)
    audios.append(a); durs.append(d + HOLD)
    print(f"slide {i:02d}: audio {d:6.2f} s")

# ---- subtitles: split each note into short chunks, time them by character share of the audio
srt, idx, t0 = [], 1, 0.0
for n, a, D in zip(notes, audios, durs):
    adur = D - HOLD
    sentences = re.split(r"(?<=[.!?])\s+", n)
    chunks = []
    for s_ in sentences:
        words = s_.split()
        while words:  # max ~12 words per subtitle line
            take = len(words) if len(words) <= 14 else 12
            chunks.append(" ".join(words[:take])); words = words[take:]
    total = sum(len(c) for c in chunks)
    t = t0 + 0.15
    for c in chunks:
        dt = adur * len(c) / total
        srt.append(f"{idx}\n{ts(t)} --> {ts(t + dt - 0.05)}\n{c}\n"); idx += 1; t += dt
    t0 += D
open(SRT, "w", encoding="utf-8").write("\n".join(srt))
open(os.path.join(WORK, "subs.srt"), "w", encoding="utf-8").write("\n".join(srt))

# ---- ffmpeg graph: looped stills -> xfade chain; padded audio -> concat; burn subtitles
args = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-stats"]
N = len(pngs)
for i, (p, D) in enumerate(zip(pngs, durs)):
    L = D + (FADE if i < N - 1 else 0)
    args += ["-loop", "1", "-framerate", "30", "-t", f"{L:.3f}", "-i", p]
for a in audios:
    args += ["-i", a]
fg = []
for i in range(N):
    fg.append(f"[{i}:v]scale=1920:1080,setsar=1,format=yuv420p[s{i}]")
prev, off = "s0", 0.0
for i in range(1, N):
    off += durs[i - 1]
    fg.append(f"[{prev}][s{i}]xfade=transition=fade:duration={FADE}:offset={off:.3f}[x{i}]")
    prev = f"x{i}"
style = ("FontName=Segoe UI,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BackColour=&H90000000,"
         "BorderStyle=4,Outline=0,Shadow=0,MarginV=6")
fg.append(f"[{prev}]subtitles=subs.srt:force_style='{style}'[vout]")
for i, D in enumerate(durs):
    fg.append(f"[{N + i}:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{D:.3f},asetpts=PTS-STARTPTS[a{i}]")
fg.append("".join(f"[a{i}]" for i in range(N)) + f"concat=n={N}:v=0:a=1[aout]")
graph = os.path.join(WORK, "graph.txt")
open(graph, "w", encoding="utf-8").write(";\n".join(fg))
args += ["-/filter_complex", graph, "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", "30", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", MP4]
print("total planned length: %.1f s" % sum(durs))
r = subprocess.run(args, cwd=WORK)
sys.exit(r.returncode)
