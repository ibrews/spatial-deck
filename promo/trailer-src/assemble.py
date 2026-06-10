#!/usr/bin/env python3
"""Assemble the Capafy-audience trailer from cards + walkthrough highlights.

Usage: python3 assemble.py A_START A_DUR B_START B_DUR C_START C_DUR [OUT]
Times in seconds into harvard-walkthrough.mp4.
"""
import subprocess
import sys

XF = 0.45  # crossfade duration
FOOT = "/tmp/sd-trailer/harvard-walkthrough.mp4"

a0, ad, b0, bd, c0, cd = [float(x) for x in sys.argv[1:7]]
out = sys.argv[7] if len(sys.argv) > 7 else "/tmp/sd-trailer/trailer-capafy.mp4"

# (kind, src, start, dur)
TIMELINE = [
    ("img",  "/tmp/sd-trailer/c0-before.png", 0, 2.2),
    ("img",  "/tmp/sd-trailer/c1-pain.png",   0, 2.8),
    ("vid",  FOOT, a0, ad),
    ("img",  "/tmp/sd-trailer/c2-meet.png",   0, 2.8),
    ("vid",  FOOT, b0, bd),
    ("img",  "/tmp/sd-trailer/c3-start.png",  0, 3.0),
    ("img",  "/tmp/sd-trailer/c4-file.png",   0, 3.2),
    ("vid",  FOOT, c0, cd),
    ("img",  "/tmp/sd-trailer/c5-keep.png",   0, 2.8),
    ("img",  "/tmp/sd-trailer/c6-cta.png",    0, 4.6),
]

inputs, filters, durs = [], [], []
for i, (kind, src, start, dur) in enumerate(TIMELINE):
    if kind == "img":
        inputs += ["-loop", "1", "-t", str(dur), "-i", src]
        filters.append(f"[{i}:v]scale=1280:720,fps=30,format=yuv420p,setsar=1[v{i}]")
    else:
        inputs += ["-ss", str(start), "-t", str(dur), "-i", src]
        filters.append(f"[{i}:v]scale=1280:720,fps=30,format=yuv420p,setsar=1[v{i}]")
    durs.append(dur)

# chain xfades: offset accumulates (sum of prior durations - fades so far)
chain = "[v0]"
total = durs[0]
for i in range(1, len(TIMELINE)):
    off = total - XF
    outl = f"[x{i}]" if i < len(TIMELINE) - 1 else "[out]"
    filters.append(f"{chain}[v{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}{outl}")
    chain = outl
    total = off + XF + (durs[i] - XF)

# fade the whole thing in and out
fc = ";".join(filters).replace("[out]", "[pre]")
fc += f";[pre]fade=t=in:st=0:d=0.4,fade=t=out:st={total-0.55:.2f}:d=0.55[out]"

cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
       "-filter_complex", fc, "-map", "[out]",
       "-c:v", "libx264", "-crf", "21", "-preset", "medium",
       "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
print(f"wrote {out} — {float(d):.1f}s")
