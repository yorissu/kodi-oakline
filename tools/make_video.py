"""Write a small playable test video (MJPEG in AVI, no ffmpeg needed) and put it
in place of a few dummy library files, so the player screens can be tested.

    python tools/make_video.py
"""
import io
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "dev" / "library"
FONT = ROOT / "skin.oakline" / "fonts" / "NotoSans-Regular.ttf"
W, H, FPS, SECONDS = 640, 360, 10, 150

# library files that get real video (the rest stay dummies)
TARGETS = [
    LIB / "TV" / "Harbor Lights" / "Season 2" / "Harbor Lights S02E01.mkv",
    LIB / "TV" / "Harbor Lights" / "Season 2" / "Harbor Lights S02E02.mkv",
    LIB / "Movies" / "Paper Moons (2024)" / "Paper Moons (2024).mkv",
]


def frame(n, font):
    """Palette-only test card: two tones, a moving wood bar, a timecode."""
    im = Image.new("RGB", (W, H), "#13223A")
    d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (W, 0), (W, H * .55), (0, H * .68)], fill="#1D3150")
    x = int((n / (FPS * 10)) % 1 * W)
    d.rectangle([x, H - 40, x + 80, H - 34], fill="#C99A52")
    s = n // FPS
    d.text((W / 2, H / 2 - 10), f"{s // 60:02d}:{s % 60:02d}", font=font, fill="#F4F2ED", anchor="mm")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=70)
    return buf.getvalue()


def chunk(fourcc, data):
    pad = b"\0" if len(data) % 2 else b""
    return fourcc + struct.pack("<I", len(data)) + data + pad


def lst(kind, payload):
    return b"LIST" + struct.pack("<I", len(payload) + 4) + kind + payload


def write_avi(path, frames):
    biggest = max(map(len, frames))
    n = len(frames)
    avih = struct.pack("<IIIIIIIIII4I", 1_000_000 // FPS, biggest * FPS, 0, 0x10, n, 0, 1, biggest, W, H, 0, 0, 0, 0)
    strh = struct.pack("<4s4sIHHIIIIIIIIhhhh", b"vids", b"MJPG", 0, 0, 0, 0, 1, FPS, 0, n, biggest, 0xFFFFFFFF, 0, 0, 0, W, H)
    strf = struct.pack("<IiiHH4sIiiII", 40, W, H, 1, 24, b"MJPG", W * H * 3, 0, 0, 0, 0)
    hdrl = lst(b"hdrl", chunk(b"avih", avih) + lst(b"strl", chunk(b"strh", strh) + chunk(b"strf", strf)))

    movi, index, offset = [], [], 4      # idx1 offsets count from the 'movi' fourcc
    for f in frames:
        c = chunk(b"00dc", f)
        index.append(struct.pack("<4sIII", b"00dc", 0x10, offset, len(f)))
        movi.append(c)
        offset += len(c)
    body = b"AVI " + hdrl + lst(b"movi", b"".join(movi)) + chunk(b"idx1", b"".join(index))
    path.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)


def main():
    font = ImageFont.truetype(str(FONT), 72)
    frames = [frame(n, font) for n in range(FPS * SECONDS)]
    out = ROOT / "dev" / "sample.avi"
    write_avi(out, frames)
    for t in TARGETS:
        t.write_bytes(out.read_bytes())
    print(f"{out} ({out.stat().st_size // 1024} KB, {SECONDS}s) copied to {len(TARGETS)} library files")


if __name__ == "__main__":
    main()
