"""Runs a real command and records every output line with its timestamp (like asciinema).
Usage: python tools/demo/rec.py <name> "<display command>" "<shell command>" [--ps]
Writes D:/corda-rest-api-run/demo/casts/<name>.json"""
import json
import os
import subprocess
import sys
import time

OUT = r"D:\corda-rest-api-run\demo\casts"
os.makedirs(OUT, exist_ok=True)
BASH = r"C:\Program Files\Git\bin\bash.exe"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

name, display, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
use_ps = "--ps" in sys.argv
argv = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd] if use_ps else [BASH, "-c", cmd]
env = dict(os.environ, PYTHONUNBUFFERED="1", TERM="dumb")
t0 = time.time()
# Output goes to a file, not a pipe: background processes started by the command (e.g. Corda nodes) may
# inherit the handle, and a pipe would then never reach EOF. We stop when the command's own process exits.
log_path = os.path.join(OUT, name + ".log")
events = []
with open(log_path, "wb") as logf:
    p = subprocess.Popen(argv, cwd=ROOT, stdout=logf, stderr=subprocess.STDOUT, env=env)
    with open(log_path, "rb") as rd:
        buf = b""
        while True:
            chunk = rd.read()
            if chunk:
                buf += chunk
                *lines, buf = buf.split(b"\n")
                now = round(time.time() - t0, 3)
                for raw in lines:
                    line = raw.decode("utf-8", errors="replace").rstrip("\r").replace("\t", "    ")
                    events.append([now, line]); print(line, flush=True)
            elif p.poll() is not None:
                time.sleep(0.3)
                rest = rd.read()
                if not rest:
                    if buf:
                        events.append([round(time.time() - t0, 3), buf.decode("utf-8", "replace").rstrip("\r")])
                    break
                buf += rest
                continue
            else:
                time.sleep(0.05)
json.dump({"name": name, "display": display, "events": events, "exit": p.returncode,
           "duration": round(time.time() - t0, 2), "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S")},
          open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8"), indent=0)
print(f"[rec] {name}: {len(events)} lines, {time.time() - t0:.1f}s, exit {p.returncode}", flush=True)
