#!/usr/bin/env python3
"""Assemble the Capafy-audience trailer: light narrator cards + labeled real
footage + synthesized soundtrack.

Usage: python3 assemble.py A_START A_DUR B_START B_DUR C_START C_DUR [OUT]
"""
import subprocess
import sys

XF = 0.45
FOOT = "/tmp/sd-trailer/harvard-walkthrough.webm"
CHIP = "/tmp/sd-trailer/footage-chip.png"
MUSIC = "/tmp/sd-trailer/trailer-music.wav"

a0, ad, b0, bd, c0, cd = [float(x) for x in sys.argv[1:7]]
out = sys.argv[7] if len(sys.argv) > 7 else "/tmp/sd-trailer/trailer-capafy.mp4"

TIMELINE = [
    ("img", "/tmp/sd-trailer/c0-before.png",    0, 2.2),
    ("img", "/tmp/sd-trailer/c1-pain-light.png", 0, 2.8),
    ("vid", FOOT, a0, ad),
    ("img", "/tmp/sd-trailer/c2-meet-light.png", 0, 2.8),
    ("vid", FOOT, b0, bd),
    ("img", "/tmp/sd-trailer/c3-start-light.png", 0, 3.0),
    ("img", "/tmp/sd-trailer/c4-file-light.png",  0, 3.2),
    ("vid", FOOT, c0, cd),
    ("img", "/tmp/sd-trailer/c5-keep-light.png",  0, 2.8),
    ("img", "/tmp/sd-trailer/c6-cta-light.png",   0, 4.6),
]

inputs, filters, durs = [], [], []
nvid = sum(1 for k, *_ in TIMELINE if k == "vid")
chip_idx = len(TIMELINE)
vid_seen = 0
for i, (kind, src, start, dur) in enumerate(TIMELINE):
    if kind == "img":
        inputs += ["-loop", "1", "-t", str(dur), "-i", src]
        filters.append(f"[{i}:v]scale=1280:720,fps=30,format=yuv420p,setsar=1[v{i}]")
    else:
        inputs += ["-ss", str(start), "-t", str(dur), "-i", src]
        # real-footage label chip, bottom-left
        filters.append(f"[{i}:v]scale=1280:720,fps=30,setsar=1[raw{i}]")
        filters.append(f"[raw{i}][ch{vid_seen}]overlay=44:720-43-86,format=yuv420p[v{i}]")
        vid_seen += 1
    durs.append(dur)
inputs += ["-i", CHIP]
splits = "".join(f"[ch{k}]" for k in range(nvid))
filters.insert(0, f"[{chip_idx}:v]split={nvid}{splits}")

chain = "[v0]"
total = durs[0]
for i in range(1, len(TIMELINE)):
    off = total - XF
    outl = f"[x{i}]" if i < len(TIMELINE) - 1 else "[pre]"
    filters.append(f"{chain}[v{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}{outl}")
    chain = outl
    total = off + XF + (durs[i] - XF)

fc = ";".join(filters)
fc += f";[pre]fade=t=in:st=0:d=0.4,fade=t=out:st={total-0.55:.2f}:d=0.55[out]"

cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-i", MUSIC,
       "-filter_complex", fc, "-map", "[out]", "-map", f"{chip_idx+1}:a",
       "-c:v", "libx264", "-crf", "21", "-preset", "medium",
       "-c:a", "aac", "-b:a", "192k", "-shortest",
       "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
print(f"wrote {out} — {float(d):.1f}s (video {total:.2f}s)")
# segment starts, for keeping the music map in sync
acc = 0
for (kind, src, start, dur) in TIMELINE:
    print(f"  {acc:6.2f}s  {kind}  {src.split('/')[-1]}")
    acc += dur - XF
