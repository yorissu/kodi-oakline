"""Install a fake video add-on (plugin.video.oakdemo) into the dev Kodi, to see how
streaming add-ons (Crunchyroll, LRT and the like) look in the skin.

It lists the same shapes real add-ons produce: a root menu, a show catalogue
(content=tvshows), an episode list with show info, an episode list with almost
nothing (as many add-ons do), movies, plain videos, and a folder with no
content type at all. Everything plays the dev sample video.

    python tools/make_demo_addon.py      (then enable it: kodidev enable-addon)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON = ROOT / "dev" / "kodi" / "portable_data" / "addons" / "plugin.video.oakdemo"

ADDON_XML = """<?xml version="1.0" encoding="UTF-8"?>
<addon id="plugin.video.oakdemo" name="Oak Demo Stream" version="1.0.0" provider-name="dev">
  <requires><import addon="xbmc.python" version="3.0.0"/></requires>
  <extension point="xbmc.python.pluginsource" library="main.py"><provides>video</provides></extension>
  <extension point="xbmc.addon.metadata">
    <summary lang="en_GB">Fake streaming add-on for skin testing</summary>
    <platform>all</platform>
  </extension>
</addon>
"""

MAIN_PY = r'''
import sys, os
from urllib.parse import parse_qsl, urlencode
import xbmcgui, xbmcplugin

BASE, HANDLE = sys.argv[0], int(sys.argv[1])
ARGS = dict(parse_qsl(sys.argv[2][1:]))
LIB = r"__LIB__"
VIDEO = r"__VIDEO__"


def url(**q):
    return BASE + "?" + urlencode(q)


def art_for(i, kind):
    movies = sorted(os.listdir(os.path.join(LIB, "Movies")))
    m = movies[i % len(movies)]
    base = os.path.join(LIB, "Movies", m, m)
    return {"poster": base + "-poster.png", "fanart": base + "-fanart.png",
            "thumb": base + ("-landscape.png" if kind != "poster" else "-poster.png"),
            "landscape": base + "-landscape.png"}


def folder(label, query, plot="", art=None, info=None):
    li = xbmcgui.ListItem(label)
    tag = li.getVideoInfoTag()
    tag.setPlot(plot)
    if info:
        info(tag)
    if art:
        li.setArt(art)
    xbmcplugin.addDirectoryItem(HANDLE, url(**query), li, isFolder=True)


def playable(label, art=None, info=None):
    li = xbmcgui.ListItem(label)
    li.setProperty("IsPlayable", "true")
    if art:
        li.setArt(art)
    if info:
        info(li.getVideoInfoTag())
    xbmcplugin.addDirectoryItem(HANDLE, url(play="1"), li, isFolder=False)


SHOWS = [("Ember Academy", "Students at a school for fire mages compete for a single scholarship.", "Anime"),
         ("Dune Runners", "Couriers race across a desert planet with cargo nobody will name.", "Sci-Fi"),
         ("Vilnius Nights", "A late-night radio host takes calls from the city's insomniacs.", "Drama"),
         ("Paper Lanterns", "A small village festival, told by the families who run it.", "Slice of life")]

route = ARGS.get("r", "root")

if "play" in ARGS:
    xbmcplugin.setResolvedUrl(HANDLE, True, xbmcgui.ListItem(path=VIDEO))
elif route == "root":
    folder("Popular series", {"r": "shows"}, "Content type: tvshows (poster grid)")
    folder("Movies", {"r": "movies"}, "Content type: movies")
    folder("Simulcasts: Ember Academy", {"r": "eps", "show": "0"}, "Content type: episodes, with show info")
    folder("Latest clips", {"r": "clips"}, "Content type: videos")
    folder("Bare episode list", {"r": "bare"}, "Content type: episodes, almost no info")
    folder("Categories", {"r": "cats"}, "No content type at all")
    xbmcplugin.endOfDirectory(HANDLE)
elif route == "shows":
    xbmcplugin.setContent(HANDLE, "tvshows")
    for i, (t, plot, genre) in enumerate(SHOWS):
        def info(tag, t=t, genre=genre):
            tag.setMediaType("tvshow"); tag.setTvShowTitle(t); tag.setGenres([genre]); tag.setYear(2024 + i % 2)
        folder(t, {"r": "eps", "show": str(i)}, plot, art_for(i, "poster"), info)
    xbmcplugin.endOfDirectory(HANDLE)
elif route == "eps":
    s = int(ARGS.get("show", 0)); title, plot, genre = SHOWS[s]
    xbmcplugin.setContent(HANDLE, "episodes")
    xbmcplugin.setPluginCategory(HANDLE, title)
    for e in range(1, 9):
        def info(tag, e=e):
            tag.setMediaType("episode"); tag.setTvShowTitle(title); tag.setSeason(1); tag.setEpisode(e)
            tag.setTitle(f"Episode {e}: " + ["Spark", "Kindling", "Smoke", "Draft", "Flare", "Ash", "Ember", "Hearth"][e - 1])
            tag.setPlot(f"{plot} Part {e}."); tag.setDuration(24 * 60)
        playable(f"Episode {e}", {**art_for(s + e, "thumb"), "tvshow.fanart": art_for(s, "")["fanart"]}, info)
    xbmcplugin.endOfDirectory(HANDLE)
elif route == "bare":
    xbmcplugin.setContent(HANDLE, "episodes")
    for e in range(1, 7):
        playable(f"Dune Runners - E{e:02d}", {"thumb": art_for(e, "thumb")["thumb"]},
                 lambda tag, e=e: tag.setMediaType("episode"))
    xbmcplugin.endOfDirectory(HANDLE)
elif route == "movies":
    xbmcplugin.setContent(HANDLE, "movies")
    for i, t in enumerate(["Night Train to Kaunas", "The Glass Orchard", "Low Orbit", "Silent Harbour", "Red Lantern"]):
        def info(tag, i=i):
            tag.setMediaType("movie"); tag.setYear(2020 + i); tag.setGenres(["Drama"]); tag.setDuration(100 * 60)
            tag.setPlot("A film streamed from the demo add-on.")
        playable(t, art_for(i + 3, "poster"), info)
    xbmcplugin.endOfDirectory(HANDLE)
elif route == "clips":
    xbmcplugin.setContent(HANDLE, "videos")
    for i in range(1, 7):
        playable(f"Clip {i}: behind the scenes", {"thumb": art_for(i, "thumb")["thumb"]},
                 lambda tag: (tag.setPlot("Short clip."), tag.setDuration(90)))
    xbmcplugin.endOfDirectory(HANDLE)
elif route == "cats":
    for c in ["Action", "Comedy", "Drama", "Romance", "Sports"]:
        folder(c, {"r": "clips"})
    xbmcplugin.endOfDirectory(HANDLE)
'''


def main():
    ADDON.mkdir(parents=True, exist_ok=True)
    (ADDON / "addon.xml").write_text(ADDON_XML, encoding="utf-8", newline="\n")
    lib = ROOT / "dev" / "library"
    (ADDON / "main.py").write_text(MAIN_PY.replace("__LIB__", str(lib)).replace("__VIDEO__", str(ROOT / "dev" / "sample.avi")),
                                   encoding="utf-8", newline="\n")
    print(f"wrote {ADDON}")


if __name__ == "__main__":
    main()
