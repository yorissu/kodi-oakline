"""Settings > Appearance by remote keys only, with an expected result per step.

    python tools/appearancetest.py      (dev Kodi running; ends with FAILED STEPS: 0)
"""

import datetime, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kodidev as k

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SHOT = [sys.executable, str(Path(__file__).resolve().parent / "kodidev.py"), "shot"]
fails = 0


def alive():
    for _ in range(40):
        try:
            k.rpc("JSONRPC.Ping"); return
        except Exception:
            time.sleep(1)


def state():
    r = k.rpc("XBMC.GetInfoLabels", {"labels": ["System.CurrentWindow", "System.CurrentControlId", "Skin.String(oak_theme_mode)", "Skin.CurrentColourTheme", "Skin.String(oak_day_begins)"]})
    return {"win": r["System.CurrentWindow"], "id": r["System.CurrentControlId"], "mode": r["Skin.String(oak_theme_mode)"] or "-",
            "colours": "light" if r["Skin.CurrentColourTheme"] == "light" else "dark", "day": r["Skin.String(oak_day_begins)"] or "-"}


def step(tag, action, wait=.8, **want):
    global fails
    if action:
        if action in k.KEYS:
            k.rpc(k.KEYS[action])
        else:
            k.rpc("Input.SendText", {"text": action, "done": True})
    time.sleep(wait); alive()
    if wait > 3:
        time.sleep(1.5)
    s = state()
    bad = {key: (s[key], v) for key, v in want.items() if s[key] != v}
    fails += bool(bad)
    print(f"{'FAIL' if bad else 'ok  '} {tag:<30} {s['win']:<14} id={s['id']:<5} mode={s['mode']:<5} colours={s['colours']:<6}" + (f"   wanted {bad}" if bad else ""))


k.builtin("RunScript(special://skin/scripts/theme.py,dark)"); time.sleep(6); alive()
k.builtin("Skin.Reset(oak_day_begins)"); k.builtin("Skin.Reset(oak_night_begins)")
k.window("home"); time.sleep(2)
k.builtin("ActivateWindow(Settings)"); time.sleep(2)
for kname in ("right", "right", "down"):
    k.rpc(k.KEYS[kname]); time.sleep(.6)
step("open Appearance", "select", 2.5, win="Skin Settings", id="9002")
step("up -> Done", "up", id="9099")
step("down from Done -> list", "down", id="9002")
step("right -> Done", "right", id="9099")
step("left -> list", "left", id="9002")
step("down -> Light", "down", id="9003")
step("select Light", "select", 6, id="9003", colours="light", mode="-")
step("down -> Auto", "down", id="9007")
day_now = datetime.datetime.now().hour in range(7, 21)
step("select Auto", "select", 6, id="9007", mode="auto", colours="light" if day_now else "dark")
step("down -> Day begins", "down", id="9008")
step("down -> Night begins", "down", id="9009")
step("down -> 24-hour clock", "down", id="9006")
step("down -> Videos folder", "down", id="9005")
step("down -> Interface", "down", id="9004")
step("down at the end stays", "down", id="9004")
for _ in range(4):
    k.rpc("Input.Up"); time.sleep(.5)
step("back up to Day begins", None, id="9008")
step("select Day begins", "select", 1.5, win="Numeric Input")
step("type 06:15", "06:15", 3, win="Skin Settings", id="9008", day="06:15", mode="auto")
step("up -> Auto", "up", id="9007")
step("up -> Light", "up", id="9003")
step("up -> Dark", "up", id="9002")
step("select Dark", "select", 6, id="9002", colours="dark", mode="-")
subprocess.run(SHOT + ["appearance"], capture_output=True)
step("down -> Light", "down", id="9003")
step("down -> Auto", "down", id="9007")
step("down -> Day begins", "down", id="9008")
step("down -> Night begins", "down", id="9009")
step("down -> clock", "down", id="9006")
c0 = k.rpc("Settings.GetSettingValue", {"setting": "locale.use24hourclock"})["value"]
step("select clock", "select", 1.5, id="9006")
c1 = k.rpc("Settings.GetSettingValue", {"setting": "locale.use24hourclock"})["value"]
step("select clock again", "select", 1.5, id="9006")
c2 = k.rpc("Settings.GetSettingValue", {"setting": "locale.use24hourclock"})["value"]
print("     24h clock:", c0, "->", c1, "->", c2)
fails += not (c0 == c2 != c1)
for _ in range(5):
    k.rpc("Input.Up"); time.sleep(.5)
step("up x5 -> Dark", None, id="9002")
step("up -> Done", "up", id="9099")
step("select Done", "select", 1.5, win="Settings")
print("FAILED STEPS:", fails)
