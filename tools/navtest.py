"""Walk every Oakline screen in the dev Kodi and check it can be used with a remote.

    python tools/navtest.py            # all screens
    python tools/navtest.py home 1152  # just these

For each screen: open it, check something has focus, then press
Up until the tab bar (9000) is reached, Down back into the screen, and
Left/Right, recording where focus goes. A screenshot of each lands in
dev/shots/nav/. Ends with a table and a list of problems; Kodi log lines
about focus or skin errors seen during the run are listed too.

Needs the dev Kodi running (python tools/kodidev.py start).
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kodidev as k  # noqa: E402

SHOTS = k.SHOTS / "nav"
BAR = {"9000", "9094", "9095", "9096", "9097", "9098"}
# Oakline 1.x is Estuary restyled: no tab bar, so the bar checks are off
TOP_BAR = True

# name: (how to open, has the top bar)
SCREENS = {
    "home": (("window", "home"), True),
    "movies": (("window", "videos", "videodb://movies/titles/"), True),
    "tvshows": (("window", "videos", "videodb://tvshows/titles/"), True),
    "showpage": (("window", "videos", "videodb://tvshows/titles/1/"), True),
    "music": (("window", "music", "musicdb://albums/"), True),
    "musiclib": (("window", "music", "musicdb://"), True),
    "videofiles": (("builtin", "SetProperty(oak_section,files,home)", "ActivateWindow(Videos,sources://video/,return)"), True),  # as More > Video files does
    "addonbrowser": (("window", "addonbrowser", "addons://user/"), True),
    "addonsroot": (("window", "addonbrowser"), True),
    "search": (("builtin", "ActivateWindow(1151)"), True),
    "musicvideos": (("window", "videos", "videodb://musicvideos/titles/"), True),
    "settings": (("window", "settings"), True),
    "playersettings": (("builtin", "ActivateWindow(PlayerSettings)"), True),
    "systeminfo": (("window", "systeminfo"), True),
    "profiles": (("window", "profiles"), True),
    "eventlog": (("builtin", "ActivateWindow(EventLog,events://,return)"), True),
    "filemanager": (("window", "filemanager"), True),
    "pictures": (("window", "pictures"), True),
    "programs": (("window", "programs"), True),
    "games": (("window", "games"), True),
    "favourites": (("window", "favouritesbrowser"), True),
    "videoplaylist": (("window", "videoplaylist"), True),
    "weather": (("window", "weather"), True),
    "skinsettings": (("window", "skinsettings"), False),
}


def labels(*names):
    return k.rpc("XBMC.GetInfoLabels", {"labels": list(names)})


def state():
    r = labels("System.CurrentWindow", "System.CurrentControlId", "System.CurrentControl")
    return r["System.CurrentWindow"], r["System.CurrentControlId"], r["System.CurrentControl"]


def press(key):
    k.rpc(k.KEYS[key])
    time.sleep(.45)
    return state()[1]


def open_screen(how):
    kind, *args = how
    if kind == "window":
        k.window(*args)
    else:
        k.builtin(*args)
    time.sleep(2.2)


def log_mark():
    path = next(p for p in (k.DATA / "kodi.log", k.DATA / "temp" / "kodi.log") if p.exists())
    return path, path.stat().st_size


def log_since(mark):
    path, size = mark
    with open(path, encoding="utf-8", errors="replace") as f:
        f.seek(size)
        text = f.read()
    keep = ("has been asked to focus", "Skin has invalid include", "Unable to load", "XML error", "no such control",
            "CGUIWindowManager", "Exception")
    return [ln.split("> ", 1)[-1].strip() for ln in text.splitlines()
            if any(x in ln for x in keep) and "ffmpeg" not in ln]


def clear_dialogs():
    for _ in range(4):
        if not k.rpc("XBMC.GetInfoBooleans", {"booleans": ["System.HasActiveModalDialog"]})["System.HasActiveModalDialog"]:
            return
        k.rpc("Input.Back")
        time.sleep(.5)


def test(name):
    clear_dialogs()
    how, has_bar = SCREENS[name]
    has_bar = has_bar and TOP_BAR
    k.window("home")
    time.sleep(1)
    mark = log_mark()
    open_screen(how)
    win, start, label = state()
    k.keys("right", "left")  # wake the renderer for the screenshot, then return
    win, start, label = state()
    SHOTS.mkdir(parents=True, exist_ok=True)
    k.shot(f"nav/{name}")
    problems = []
    if not start:
        problems.append("nothing focused on open")
    path = []
    reached = False
    if has_bar:
        for _ in range(6):
            c = press("up")
            path.append(c)
            if c in BAR:
                reached = True
                break
        if not reached:
            problems.append("Up never reaches the tab bar")
        down = press("down")
        path.append(f"v{down}")
        if reached and (down in BAR or not down):
            problems.append("Down from the tab bar doesn't go back into the screen")
    else:
        # Estuary-based skin: every arrow must leave something focused
        for key in ("down", "up"):
            c = press(key)
            path.append(f"{key[0]}{c}")
            if not c:
                problems.append(f"nothing focused after {key}")
    right = press("right")
    left = press("left")
    path += [f">{right}", f"<{left}"]
    if not right or not left:
        problems.append("nothing focused after Left/Right")
    log = log_since(mark)
    return {"name": name, "window": win, "start": start, "label": label, "path": " ".join(path),
            "problems": problems, "log": sorted(set(log))}


def main():
    names = sys.argv[1:] or list(SCREENS)
    results = []
    for n in names:
        try:
            results.append(test(n))
        except Exception as e:  # keep going: one broken screen shouldn't hide the rest
            results.append({"name": n, "window": "?", "start": "", "label": "", "path": "", "problems": [f"error: {e}"], "log": []})
        r = results[-1]
        print(f"{r['name']:<15} {r['window']:<18} focus {r['start'] or '-':<6} {r['path']:<40} {'OK' if not r['problems'] else '; '.join(r['problems'])}")
    k.window("home")
    bad = [r for r in results if r["problems"] or r["log"]]
    print(f"\n{len(results) - len(bad)}/{len(results)} screens clean")
    for r in bad:
        for p in r["problems"]:
            print(f"  {r['name']}: {p}")
        for ln in r["log"]:
            print(f"  {r['name']} log: {ln}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
