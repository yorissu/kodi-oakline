"""Dev harness for the Oakline skin: a portable Kodi under dev/kodi, the skin
linked in from the project, a fake library, and a JSON-RPC remote.

    python tools/kodidev.py setup      # profile, sources, links (Kodi closed)
    python tools/kodidev.py enable     # enable add-ons, set library content, select skin (Kodi closed)
    python tools/kodidev.py start      # launch Kodi in portable mode
    python tools/kodidev.py stop
    python tools/kodidev.py scan       # scan library, then seed watched/resume state
    python tools/kodidev.py seed
    python tools/kodidev.py reload     # copy skin into Kodi, then ReloadSkin()
    python tools/kodidev.py shot NAME  # screenshot to dev/shots/NAME.png
    python tools/kodidev.py keys down down right select   # remote presses
    python tools/kodidev.py builtin "ActivateWindow(Home)"
    python tools/kodidev.py log [N]    # tail kodi.log
"""
import base64
import json
import secrets
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEV = ROOT / "dev"
KODI = DEV / "kodi"
DATA = KODI / "portable_data"
USERDATA = DATA / "userdata"
CONFIG = DEV / "devconfig.json"
SHOTS = DEV / "shots"
LIB = DEV / "library"
HELPER = "script.oakline.dev"


def config():
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps({"port": 8089, "user": "kodi", "password": secrets.token_urlsafe(12)}, indent=2), encoding="utf-8", newline="\n")
    return json.loads(CONFIG.read_text())


# ---------------------------------------------------------------- setup

def sync():
    """Mirror the skin into Kodi's add-ons folder. (D: has no junction support, so copy.)"""
    r = subprocess.run(["robocopy", str(ROOT / "skin.oakline"), str(DATA / "addons" / "skin.oakline"), "/MIR", "/NJH", "/NJS", "/NFL", "/NDL", "/NP"],
                       capture_output=True, text=True)
    if r.returncode >= 8:
        sys.exit(r.stdout + r.stderr)
    # skin.oakline/addon.xml holds the placeholder 0.0.0 (the version comes from the git tag, see
    # build_zip.py); Kodi treats 0.0.0 as no version and uninstalls the skin, so the copy gets a real one
    sys.path.insert(0, str(ROOT))
    import build_zip
    version = build_zip.git_version()
    if version.startswith("0.0.0"):
        version = "0.0.1~dev"
    copy = DATA / "addons" / "skin.oakline" / "addon.xml"
    text = copy.read_text(encoding="utf-8")
    copy.write_text(build_zip.VERSION_ATTR.sub(lambda m: m.group(1) + version + m.group(3), text, count=1), encoding="utf-8", newline="\n")


def write_helper():
    """A tiny script add-on so JSON-RPC can run any builtin (ReloadSkin, TakeScreenshot...)."""
    d = DATA / "addons" / HELPER
    d.mkdir(parents=True, exist_ok=True)
    (d / "addon.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<addon id="{HELPER}" name="Oakline dev helper" version="1.0.0" provider-name="dev">
  <requires><import addon="xbmc.python" version="3.0.0"/></requires>
  <extension point="xbmc.python.script" library="default.py"><provides>executable</provides></extension>
  <extension point="xbmc.addon.metadata"><summary lang="en_GB">Runs builtins for the skin dev harness</summary><platform>all</platform></extension>
</addon>
""", encoding="utf-8", newline="\n")
    # each argument is a builtin, or "py:<code>" to run Python inside Kodi (e.g. open a dialog)
    (d / "default.py").write_text("import sys, xbmc, xbmcgui\n"
                                  "for b in sys.argv[1:]:\n"
                                  "    exec(b[3:]) if b.startswith('py:') else xbmc.executebuiltin(b, True)\n", encoding="utf-8", newline="\n")


def setup():
    cfg = config()
    USERDATA.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    sync()
    write_helper()
    gs = USERDATA / "guisettings.xml"
    if not gs.exists():
        gs.write_text(f"""<settings version="2">
    <setting id="services.webserver">true</setting>
    <setting id="services.webserverport">{cfg['port']}</setting>
    <setting id="services.webserverauthentication">true</setting>
    <setting id="services.webserverusername">{cfg['user']}</setting>
    <setting id="services.webserverpassword">{cfg['password']}</setting>
    <setting id="videoscreen.screenmode">WINDOW</setting>
    <setting id="window.width">1600</setting>
    <setting id="window.height">900</setting>
    <setting id="general.addonupdates">2</setting>
    <setting id="general.addonnotifications">false</setting>
</settings>
""", encoding="utf-8", newline="\n")
    (USERDATA / "sources.xml").write_text(f"""<sources>
    <video>
        <default pathversion="1"></default>
        <source><name>Movies</name><path pathversion="1">{LIB / 'Movies'}\\</path><allowsharing>true</allowsharing></source>
        <source><name>TV</name><path pathversion="1">{LIB / 'TV'}\\</path><allowsharing>true</allowsharing></source>
    </video>
</sources>
""", encoding="utf-8", newline="\n")
    print("setup done; start Kodi once, quit it, then run `enable`")


def db(prefix):
    found = sorted((USERDATA / "Database").glob(f"{prefix}*.db"))
    if not found:
        sys.exit(f"no {prefix}*.db yet - start Kodi once first")
    return sqlite3.connect(found[-1])


def enable():
    with db("Addons") as c:
        for addon in ("skin.oakline", HELPER):
            c.execute("UPDATE installed SET enabled=1, disabledReason=0 WHERE addonID=?", (addon,))
        print(c.execute("SELECT addonID, enabled FROM installed WHERE addonID IN (?,?)", ("skin.oakline", HELPER)).fetchall())
    with db("MyVideos") as c:
        for sub, content, recursive in (("Movies", "movies", 2147483647), ("TV", "tvshows", 0)):
            path = f"{LIB / sub}\\"
            c.execute("DELETE FROM path WHERE strPath=?", (path,))
            c.execute("INSERT INTO path (strPath, strContent, strScraper, scanRecursive, useFolderNames, strSettings, noUpdate, exclude, allAudio) "
                      "VALUES (?,?,?,?,0,'',0,0,0)", (path, content, "metadata.local", recursive))
    gs = USERDATA / "guisettings.xml"
    text = gs.read_text(encoding="utf-8")
    import re
    if 'id="lookandfeel.skin"' in text:
        text = re.sub(r'<setting id="lookandfeel.skin"[^>]*>[^<]*</setting>', '<setting id="lookandfeel.skin">skin.oakline</setting>', text)
    else:
        text = text.replace("</settings>", '    <setting id="lookandfeel.skin">skin.oakline</setting>\n</settings>')
    gs.write_text(text, encoding="utf-8", newline="\n")
    print("skin selected; start Kodi")


# ---------------------------------------------------------------- running

def start():
    subprocess.Popen([str(KODI / "kodi.exe"), "-p"], cwd=KODI)
    for _ in range(60):
        try:
            rpc("JSONRPC.Ping")
            print("kodi is up")
            return
        except Exception:
            time.sleep(1)
    print("kodi did not answer on JSON-RPC")


def rpc(method, params=None):
    cfg = config()
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{cfg['port']}/jsonrpc", body, {"Content-Type": "application/json"})
    token = base64.b64encode(f"{cfg['user']}:{cfg['password']}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.loads(r.read())
    if "error" in res:
        raise RuntimeError(res["error"])
    return res.get("result")


def builtin(*cmds):
    rpc("Addons.ExecuteAddon", {"addonid": HELPER, "params": list(cmds), "wait": True})


def stop():
    try:
        rpc("Application.Quit")
    except Exception as e:
        print("quit:", e)


def scan():
    rpc("VideoLibrary.Scan")
    for _ in range(60):
        time.sleep(2)
        if not rpc("XBMC.GetInfoBooleans", {"booleans": ["Library.IsScanningVideo"]})["Library.IsScanningVideo"]:
            break
    movies = rpc("VideoLibrary.GetMovies").get("limits", {}).get("total")
    eps = rpc("VideoLibrary.GetEpisodes").get("limits", {}).get("total")
    print(f"library: {movies} movies, {eps} episodes")


def seed():
    """Watched counts and resume points so every home row has content."""
    # The scanner doesn't pick up local movie art here, so set it directly.
    found = rpc("VideoLibrary.GetMovies", {"properties": ["file"]})["movies"]
    for m in found:
        base = m["file"].rsplit(".", 1)[0]
        rpc("VideoLibrary.SetMovieDetails", {"movieid": m["movieid"], "art": {
            "poster": f"{base}-poster.png", "fanart": f"{base}-fanart.png", "landscape": f"{base}-landscape.png"}})
    movies = {m["label"]: m["movieid"] for m in found}
    for i, (title, plays) in enumerate([("Northbound", 6), ("Atlas of Small Things", 5), ("Undertow", 4), ("Saltwater", 3), ("Kestrel", 2), ("Orchard", 1)]):
        rpc("VideoLibrary.SetMovieDetails", {"movieid": movies[title], "playcount": plays, "lastplayed": f"2026-10-{10 + i:02d} 20:00:00"})
    for i, (title, frac) in enumerate([("Paper Moons", .41), ("Midsummer Signal", .27)]):
        rpc("VideoLibrary.SetMovieDetails", {"movieid": movies[title], "resume": {"position": 6360 * frac, "total": 6360},
                                             "lastplayed": f"2026-10-2{i} 21:00:00"})
    eps = rpc("VideoLibrary.GetEpisodes", {"properties": ["showtitle", "season", "episode"]})["episodes"]
    resume = {("Harbor Lights", 2, 1): (.62, 22), ("Copper Age", 1, 3): (.18, 21), ("Glass Mountain", 1, 1): (.85, 19)}
    for e in eps:
        key = (e["showtitle"], e["season"], e["episode"])
        if key[0] == "Harbor Lights" and key[1] == 1:
            rpc("VideoLibrary.SetEpisodeDetails", {"episodeid": e["episodeid"], "playcount": 1})
        if key in resume:
            frac, day = resume[key]
            rpc("VideoLibrary.SetEpisodeDetails", {"episodeid": e["episodeid"], "resume": {"position": 3000 * frac, "total": 3000},
                                                   "lastplayed": f"2026-10-{day} 22:00:00"})
    print("seeded watched and resume state")


def shot(name="shot"):
    SHOTS.mkdir(parents=True, exist_ok=True)
    out = SHOTS / f"{name}.png"
    out.unlink(missing_ok=True)
    builtin(f"TakeScreenshot({out},sync)")
    for _ in range(20):
        if out.exists():
            print(out)
            return
        time.sleep(.25)
    print("no screenshot written")


KEYS = {"up": "Input.Up", "down": "Input.Down", "left": "Input.Left", "right": "Input.Right",
        "select": "Input.Select", "back": "Input.Back", "info": "Input.Info", "home": "Input.Home", "menu": "Input.ContextMenu", "osd": "Input.ShowOSD"}


def keys(*names):
    for n in names:
        rpc(KEYS[n])
        time.sleep(.35)


def log(n="40"):
    path = next(p for p in (DATA / "kodi.log", DATA / "temp" / "kodi.log") if p.exists())
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    print("\n".join(lines[-int(n):]))


def window(name, *params):
    """Open a Kodi window by name over JSON-RPC (no busy-dialog deadlock)."""
    args = {"window": name}
    if params:
        args["parameters"] = list(params)
    rpc("GUI.ActivateWindow", args)


def theme(name="SKINDEFAULT"):
    """Switch the colour theme: SKINDEFAULT (dark) or light."""
    rpc("Settings.SetSettingValue", {"setting": "lookandfeel.skincolors", "value": name})


def call(method, params="{}"):
    print(json.dumps(rpc(method, json.loads(params)), indent=1))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd, *args = sys.argv[1:] or ["help"]
    fn = {"setup": setup, "enable": enable, "start": start, "stop": stop, "scan": scan, "seed": seed,
          "sync": sync, "reload": lambda: (sync(), builtin("ReloadSkin()")), "shot": shot, "keys": keys, "builtin": builtin, "log": log,
          "window": window, "theme": theme, "rpc": call}.get(cmd)
    if not fn:
        print(__doc__)
    else:
        fn(*args)
