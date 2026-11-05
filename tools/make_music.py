"""Build a fake music library for skin development: short WAV tracks with ID3
tags (Kodi reads an "id3 " chunk in WAV), plus flat palette album covers.

    python tools/make_music.py
"""
import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "dev" / "library" / "Music"
FONT = ROOT / "skin.oakline" / "fonts" / "NotoSans-Regular.ttf"
RATE, SECONDS = 8000, 25
TONES = [("#1D3150", "#13223A"), ("#4A5566", "#1D3150"), ("#8A93A0", "#4A5566"), ("#2A3B55", "#13223A"), ("#D3D7DD", "#8A93A0")]

ALBUMS = [
    ("Mara Lind", "Low Light Sessions", 2024, "Jazz",
     ["Blue Hour", "Second Pour", "Lamplight", "After the Rain", "Quiet Street", "Last Set"]),
    ("Tomas Reyes Trio", "Northern Rooms", 2023, "Folk",
     ["Cold Kitchen", "Window Seat", "Spruce", "Long Way North", "Kettle Song"]),
    ("Ines Okafor", "Paper & Pine", 2025, "Indie",
     ["Origami", "Pine Needles", "Tape Deck", "Sunday Paper", "Fold", "Woodsmoke", "Pinecone"]),
    ("Saltmarsh", "Tidal", 2022, "Ambient",
     ["Ebb", "Flow", "Slack Water", "Spring Tide"]),
    ("Mara Lind", "Small Hours", 2021, "Jazz",
     ["Three A.M.", "Night Bus", "Small Hours", "Streetlight", "Dawn"]),
]


def id3(frames):
    """ID3v2.3 tag with Latin-1 text frames."""
    body = b""
    for fid, text in frames.items():
        data = b"\x00" + text.encode("latin-1")
        body += fid.encode() + struct.pack(">I", len(data)) + b"\x00\x00" + data
    n = len(body)
    size = bytes([(n >> 21) & 0x7F, (n >> 14) & 0x7F, (n >> 7) & 0x7F, n & 0x7F])
    return b"ID3\x03\x00\x00" + size + body


def wav(path, freq, tag):
    samples = bytearray()
    for i in range(RATE * SECONDS):
        t = i / RATE
        fade = min(1, t * 2, (SECONDS - t) * 2)
        v = 0.18 * fade * (math.sin(2 * math.pi * freq * t) + 0.5 * math.sin(2 * math.pi * freq * 1.5 * t))
        samples += struct.pack("<h", int(v * 32767 / 1.5))
    fmt = struct.pack("<HHIIHH", 1, 1, RATE, RATE * 2, 2, 16)
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    chunks += b"data" + struct.pack("<I", len(samples)) + bytes(samples)
    tag = id3(tag)
    chunks += b"id3 " + struct.pack("<I", len(tag)) + tag + (b"\0" if len(tag) % 2 else b"")
    path.write_bytes(b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks)


def cover(path, i, title, artist):
    w = h = 600
    top, bottom = TONES[i % len(TONES)]
    im = Image.new("RGB", (w, h), bottom)
    d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (w, 0), (w, h * (0.45 + 0.05 * i)), (0, h * (0.6 - 0.04 * i))], fill=top)
    light = top in ("#8A93A0", "#D3D7DD")
    ink = "#08111D" if light else "#F4F2ED"
    d.text((40, h - 110), title.upper(), font=ImageFont.truetype(str(FONT), 34), fill=ink)
    d.text((40, h - 64), artist, font=ImageFont.truetype(str(FONT), 24), fill=ink)
    im.save(path)


def main():
    for a, (artist, album, year, genre, tracks) in enumerate(ALBUMS):
        folder = LIB / artist / album
        folder.mkdir(parents=True, exist_ok=True)
        cover(folder / "folder.jpg", a, album, artist)
        for n, title in enumerate(tracks, 1):
            wav(folder / f"{n:02d} - {title}.wav", 220 + 40 * a + 15 * n,
                {"TIT2": title, "TPE1": artist, "TPE2": artist, "TALB": album, "TRCK": str(n), "TYER": str(year), "TCON": genre})
    print(f"music written to {LIB}")


if __name__ == "__main__":
    main()
