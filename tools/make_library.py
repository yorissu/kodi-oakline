"""Build a fake Kodi library for skin development: dummy video files, NFOs and
flat palette artwork. Scanned with the 'Local information only' scraper.

    python tools/make_library.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "dev" / "library"
FONT = ROOT / "skin.oakline" / "fonts" / "NotoSans-Regular.ttf"

TONES = [("#1D3150", "#13223A"), ("#4A5566", "#1D3150"), ("#13223A", "#08111D"),
         ("#8A93A0", "#4A5566"), ("#2A3B55", "#13223A")]
WHITE, NAVY = "#F4F2ED", "#08111D"

MOVIES = [
    ("Northbound", 2025, "Drama", 128, "Agnė Vasiliauskaitė",
     "A cartographer sent to map a vanishing coastline finds her late father's handwriting on every chart she was told to finish."),
    ("Paper Moons", 2024, "Comedy", 106, "Tomas Reyes", "Two rival stage magicians are forced to share one small-town theatre for a summer."),
    ("Saltwater", 2024, "Drama", 118, "Ines Okafor", "A ferry captain's last season on the island route, told one crossing at a time."),
    ("Atlas of Small Things", 2023, "Animation", 99, "Jun Park", "A museum mouse catalogues everything humans leave behind after closing time."),
    ("Ember Street", 2023, "Crime", 122, "Elena Varga", "One night, one street, eleven people who all saw the fire start."),
    ("Kestrel", 2025, "Thriller", 111, "Sami Kallio", "A drone pilot notices the same car in every surveillance frame she reviews."),
    ("Undertow", 2022, "Mystery", 134, "Noor Haddad", "When the tide goes out further than ever recorded, the village finds what it buried."),
    ("The Last Ferry", 2022, "Drama", 104, "Piet de Wit", "Strangers stranded overnight on a ferry terminal trade the stories they never told."),
    ("Orchard", 2025, "Family", 97, "Mara Lind", "Three cousins have one autumn to save their grandmother's apple orchard."),
    ("Midsummer Signal", 2024, "Sci-fi", 125, "Tomas Reyes", "A radio astronomer receives a broadcast of her own voice, dated forty years from now."),
]

SHOWS = [
    ("Harbor Lights", 2023, "Crime", "Inspector Daly keeps the peace in a port town where every crate has a secret.",
     {1: ["Pilot", "The Manifest", "Fog Bell", "Dry Dock"], 2: ["Low Tide", "Salt", "Night Shift", "Breakwater"]}),
    ("Glass Mountain", 2020, "Thriller", "A research station on a glacier loses contact with its lower camp.",
     {1: ["Thaw", "Crevasse", "Whiteout"]}),
    ("Copper Age", 2025, "Historical", "A forge guild splits when a stranger arrives with a technique nobody can explain.",
     {1: ["Ore", "Bellows", "Smelt", "Quench"]}),
    ("Lowland", 2025, "Drama", "Families in a reclaimed polder fight over who controls the water.",
     {1: ["Dikes", "Pumps", "The Vote"]}),
]


def font(size):
    return ImageFont.truetype(str(FONT), size)


def art(path, size, i, title=None):
    """Two flat tones split by a hard diagonal; optional title for posters."""
    w, h = size
    top, bottom = TONES[i % len(TONES)]
    im = Image.new("RGB", size, bottom)
    d = ImageDraw.Draw(im)
    y0, y1 = [(0.52, 0.62), (0.66, 0.56), (0.48, 0.58), (0.70, 0.66), (0.58, 0.50)][i % 5]
    d.polygon([(0, 0), (w, 0), (w, h * y1), (0, h * y0)], fill=top)
    if title:
        f = font(int(w * 0.075))
        words, lines = title.upper().split(), [""]
        for word in words:
            trial = (lines[-1] + " " + word).strip()
            if d.textlength(trial, font=f) > w * 0.8 and lines[-1]:
                lines.append(word)
            else:
                lines[-1] = trial
        light = top in ("#8A93A0",)
        y = h * 0.78
        for ln in lines:
            d.text((w / 2, y), ln, font=f, fill=WHITE if not light else NAVY, anchor="mm")
            y += f.size * 1.25
    im.save(path)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def dummy(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\0" * 1024)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def main():
    n = 0
    for title, year, genre, runtime, director, plot in MOVIES:
        folder = LIB / "Movies" / f"{title} ({year})"
        base = folder / f"{title} ({year})"
        dummy(base.with_suffix(".mkv"))
        write(base.with_suffix(".nfo"), f"""<?xml version="1.0" encoding="UTF-8"?>
<movie>
  <title>{esc(title)}</title>
  <year>{year}</year>
  <premiered>{year}-0{1 + n % 9}-1{n % 9}</premiered>
  <plot>{esc(plot)}</plot>
  <genre>{genre}</genre>
  <runtime>{runtime}</runtime>
  <director>{esc(director)}</director>
  <ratings><rating name="default" max="10" default="true"><value>{7 + (n * 3 % 19) / 10:.1f}</value></rating></ratings>
  <actor><name>Mara Lind</name><role>Lead</role></actor>
  <actor><name>Tomas Reyes</name><role>Support</role></actor>
</movie>
""")
        # <file>-poster.png etc.: Kodi only reads bare poster.png for movies when the
        # source is set to "movies in separate folders"
        art(Path(f"{base}-poster.png"), (500, 750), n, title)
        art(Path(f"{base}-fanart.png"), (1920, 1080), n + 1)
        art(Path(f"{base}-landscape.png"), (640, 360), n + 1)
        n += 1

    for title, year, genre, plot, seasons in SHOWS:
        folder = LIB / "TV" / title
        write(folder / "tvshow.nfo", f"""<?xml version="1.0" encoding="UTF-8"?>
<tvshow>
  <title>{esc(title)}</title>
  <year>{year}</year>
  <premiered>{year}-03-01</premiered>
  <plot>{esc(plot)}</plot>
  <genre>{genre}</genre>
  <ratings><rating name="default" max="10" default="true"><value>8.{n % 9}</value></rating></ratings>
</tvshow>
""")
        art(folder / "poster.png", (500, 750), n, title)
        art(folder / "fanart.png", (1920, 1080), n + 1)
        art(folder / "landscape.png", (640, 360), n + 1)
        for season, eps in seasons.items():
            for e, ep in enumerate(eps, 1):
                base = folder / f"Season {season}" / f"{title} S{season:02d}E{e:02d}"
                dummy(base.with_suffix(".mkv"))
                write(base.with_suffix(".nfo"), f"""<?xml version="1.0" encoding="UTF-8"?>
<episodedetails>
  <title>{esc(ep)}</title>
  <season>{season}</season>
  <episode>{e}</episode>
  <aired>{year + season - 1}-0{1 + e}-0{e}</aired>
  <runtime>{46 + (e * 7) % 12}</runtime>
  <plot>Episode {e} of season {season}. {esc(plot)}</plot>
</episodedetails>
""")
                art(base.parent / f"{base.name}-thumb.png", (640, 360), n + e)
        n += 1
    print(f"library written to {LIB}")


if __name__ == "__main__":
    main()
