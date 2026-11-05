"""Generate the skin's media: a white texture for flat colour fills, and line icons.

Icons are drawn white on transparent (the skin tints them with colordiffuse),
drawn on a 24x24 grid at 8x and downsampled.

    python tools/make_media.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

MEDIA = Path(__file__).resolve().parent.parent / "skin.oakline" / "media"
SCALE = 8          # 24 * 8 = 192 px drawing canvas
OUT = 64           # final icon size
STROKE = 2 * SCALE


def p(*xy):
    return [v * SCALE for v in xy]


def rect(d, x0, y0, x1, y1):
    h = STROKE / 2
    d.rectangle([x0 * SCALE - h, y0 * SCALE - h, x1 * SCALE + h, y1 * SCALE + h], outline="white", width=STROKE)


def line(d, *pts):
    d.line([v * SCALE for v in pts], fill="white", width=STROKE, joint="curve")


ICONS = {
    "search": lambda d: (rect(d, 3.5, 3.5, 16.5, 16.5), line(d, 15, 15, 21, 21)),
    "home": lambda d: (line(d, 3, 21, 3, 11, 12, 4, 21, 11, 21, 21, 3, 21), line(d, 10, 21, 10, 15, 14, 15, 14, 21)),
    "film": lambda d: (rect(d, 3, 4, 21, 20), line(d, 7, 4, 7, 20), line(d, 17, 4, 17, 20), line(d, 3, 12, 21, 12)),
    "music": lambda d: (line(d, 9, 18, 9, 5, 20, 3, 20, 16), rect(d, 4, 15, 9, 20), rect(d, 15, 13, 20, 18)),
    "list": lambda d: (line(d, 4, 6, 20, 6), line(d, 4, 12, 20, 12), line(d, 4, 18, 14, 18)),
    "settings": lambda d: (line(d, 4, 7, 14, 7), line(d, 18, 7, 20, 7), line(d, 4, 17, 6, 17), line(d, 10, 17, 20, 17),
                           rect(d, 14, 4.5, 18, 9.5), rect(d, 6, 14.5, 10, 19.5)),
    "play": lambda d: d.polygon(p(6, 3.5, 6, 20.5, 20, 12), fill="white"),
    # player
    "pause": lambda d: (d.rectangle(p(6, 4, 10.5, 20), fill="white"), d.rectangle(p(13.5, 4, 18, 20), fill="white")),
    "back": lambda d: (d.polygon(p(11, 5, 11, 19, 2, 12), fill="white"), d.polygon(p(21, 5, 21, 19, 12, 12), fill="white")),
    "fwd": lambda d: (d.polygon(p(3, 5, 3, 19, 12, 12), fill="white"), d.polygon(p(13, 5, 13, 19, 22, 12), fill="white")),
    "next": lambda d: (d.polygon(p(4, 4, 4, 20, 15, 12), fill="white"), d.rectangle(p(16.5, 4, 19, 20), fill="white")),
    "subs": lambda d: (rect(d, 3, 5, 21, 19), line(d, 7, 11, 11, 11), line(d, 13, 11, 17, 11), line(d, 7, 15, 17, 15)),
    "audio": lambda d: (line(d, 4, 9, 8, 9, 13, 5, 13, 19, 8, 15, 4, 15, 4, 9), line(d, 16.5, 9, 18, 12, 16.5, 15)),
    "stop": lambda d: d.rectangle(p(6, 6, 18, 18), fill="white"),
    "prev": lambda d: (d.polygon(p(20, 4, 20, 20, 9, 12), fill="white"), d.rectangle(p(5, 4, 7.5, 20), fill="white")),
    "shuffle": lambda d: (line(d, 3, 7, 8, 7, 16, 17, 21, 17), line(d, 3, 17, 8, 17, 16, 7, 21, 7),
                          line(d, 18, 4, 21, 7, 18, 10), line(d, 18, 14, 21, 17, 18, 20)),
    "addons": lambda d: (rect(d, 4, 4, 10, 10), rect(d, 14, 4, 20, 10), rect(d, 4, 14, 10, 20), line(d, 17, 13, 17, 21), line(d, 13, 17, 21, 17)),
    "zip": lambda d: (line(d, 6, 3, 6, 21, 18, 21, 18, 8, 13, 3, 6, 3), line(d, 13, 3, 13, 8, 18, 8)),
    "update": lambda d: (line(d, 5, 12, 5, 7, 18, 7), line(d, 15, 4, 18, 7, 15, 10), line(d, 19, 12, 19, 17, 6, 17), line(d, 9, 14, 6, 17, 9, 20)),
    "store": lambda d: (rect(d, 4, 8, 20, 20), line(d, 9, 8, 9, 5, 15, 5, 15, 8)),
    "repeat": lambda d: (line(d, 4, 12, 4, 7, 20, 7), line(d, 17, 4, 20, 7, 17, 10),
                         line(d, 20, 12, 20, 17, 4, 17), line(d, 7, 14, 4, 17, 7, 20)),
    # sections added with the remaining Kodi windows
    "live": lambda d: (rect(d, 2.5, 8, 21.5, 20), line(d, 7, 3, 12, 8, 17, 3)),
    "star": lambda d: d.polygon(p(12, 2.5, 14.8, 9, 21.5, 9.3, 16.3, 13.6, 18, 20.5, 12, 16.6, 6, 20.5, 7.7, 13.6, 2.5, 9.3, 9.2, 9), outline="white", width=STROKE),
    "more": lambda d: (rect(d, 4, 4, 10, 10), rect(d, 14, 4, 20, 10), rect(d, 4, 14, 10, 20), rect(d, 14, 14, 20, 20)),
    "picture": lambda d: (rect(d, 3, 4, 21, 20), line(d, 3, 17, 9, 11, 14, 16, 17, 13, 21, 17), rect(d, 15, 7.5, 17, 9.5)),
    "game": lambda d: (rect(d, 2.5, 7, 21.5, 18), line(d, 8, 10, 8, 15), line(d, 5.5, 12.5, 10.5, 12.5), rect(d, 15, 10, 16, 11), rect(d, 17.5, 13, 18.5, 14)),
    "weather": lambda d: (d.ellipse(p(7, 7, 17, 17), outline="white", width=STROKE), line(d, 12, 1.5, 12, 4), line(d, 12, 20, 12, 22.5),
                          line(d, 1.5, 12, 4, 12), line(d, 20, 12, 22.5, 12)),
    "folder": lambda d: line(d, 3, 6, 3, 19, 21, 19, 21, 8, 11, 8, 9, 5, 3, 5, 3, 6),
    "radio": lambda d: (rect(d, 3, 9, 21, 20), d.ellipse(p(12.5, 11.5, 18.5, 17.5), outline="white", width=STROKE), line(d, 6, 9, 17, 3)),
    "chevron": lambda d: line(d, 15, 4, 7, 12, 15, 20),
    "info": lambda d: (rect(d, 3, 3, 21, 21), line(d, 12, 10.5, 12, 17), rect(d, 11.5, 6.5, 12.5, 7.5)),
    "program": lambda d: (rect(d, 3, 4, 21, 20), line(d, 3, 8.5, 21, 8.5), line(d, 7, 12, 10, 14.5, 7, 17), line(d, 12, 17, 16, 17)),
}


def main():
    (MEDIA / "icons").mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (16, 16), "white").save(MEDIA / "white.png")
    # 2px outline for buttons, stretched by Kodi with <texture border="2">. Large, so the
    # centre is barely scaled: a small texture smears the edge when stretched.
    im = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
    ImageDraw.Draw(im).rectangle([0, 0, 255, 255], outline="white", width=2)
    im.save(MEDIA / "frame.png")
    for name, draw in ICONS.items():
        im = Image.new("RGBA", (24 * SCALE, 24 * SCALE), (255, 255, 255, 0))
        draw(ImageDraw.Draw(im))
        im.resize((OUT, OUT), Image.LANCZOS).save(MEDIA / "icons" / f"{name}.png")
    # mouse pointer: a solid arrow (tinted by the skin), drawn large and scaled down
    im = Image.new("RGBA", (24 * SCALE, 24 * SCALE), (255, 255, 255, 0))
    ImageDraw.Draw(im).polygon(p(3, 2, 3, 19, 7.5, 15, 10.5, 21.5, 13.5, 20, 10.5, 13.8, 16.5, 13.5), fill="white")
    im.resize((OUT, OUT), Image.LANCZOS).save(MEDIA / "pointer.png")
    # guide cell: solid with a 3px clear gap right and bottom, stretched with border="0,0,3,3"
    im = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
    ImageDraw.Draw(im).rectangle([0, 0, 60, 60], fill="white")
    im.save(MEDIA / "cell.png")
    # screen calibration corners: an L in each corner's direction, 6px arms
    for name, box in (("calib-topleft", [(0, 0, 64, 6), (0, 0, 6, 64)]), ("calib-bottomright", [(0, 58, 64, 64), (58, 0, 64, 64)])):
        im = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
        d = ImageDraw.Draw(im)
        for b in box:
            d.rectangle([b[0], b[1], b[2] - 1, b[3] - 1], fill="white")
        im.save(MEDIA / f"{name}.png")
    # Kodi's stand-in icon for add-ons without one (looked up by name in the skin)
    im = Image.new("RGBA", (24 * SCALE, 24 * SCALE), (255, 255, 255, 0))
    ICONS["addons"](ImageDraw.Draw(im))
    tile = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    tile.paste(im.resize((128, 128), Image.LANCZOS).point(lambda v: v * 0.55), (64, 64))
    tile.save(MEDIA / "DefaultAddon.png")
    print(f"wrote {len(ICONS)} icons to {MEDIA}")


if __name__ == "__main__":
    main()
