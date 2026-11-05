"""No list wraps round: on each screen, press past both ends of a list and
check the cursor stops at the end instead of coming back from the other side.

    python tools/wraptest.py         (dev Kodi running; ends with "0 wrapped")

A list wraps when, pressing one way, the cursor reaches something it already
passed on the way (it came round from the other end).
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kodidev as k  # noqa: E402

FOLDER = str(k.ROOT / "dev" / "folders") + "\\"
KEYS = {"down": "Input.Down", "up": "Input.Up", "left": "Input.Left", "right": "Input.Right"}
OPPOSITE = {"down": "up", "up": "down", "left": "right", "right": "left"}


def where():
    r = k.rpc("XBMC.GetInfoLabels", {"labels": ["System.CurrentWindow", "System.CurrentControlId", "System.CurrentControl", "ListItem.Label", "Container.CurrentItem"]})
    return (r["System.CurrentWindow"], r["System.CurrentControlId"], r["Container.CurrentItem"] if r["ListItem.Label"] else "", r["ListItem.Label"] or r["System.CurrentControl"])


def clear():
    for _ in range(5):
        if not k.rpc("XBMC.GetInfoBooleans", {"booleans": ["System.HasActiveModalDialog"]})["System.HasActiveModalDialog"]:
            break
        k.rpc("Input.Back"); time.sleep(.6)


def press(direction, times):
    """Positions visited pressing one way; stops early once the cursor stays put."""
    seen = [where()]
    for _ in range(times):
        k.rpc(KEYS[direction]); time.sleep(.35)
        seen.append(where())
        if seen[-1] == seen[-2] == seen[-3 if len(seen) > 2 else -2]:
            break
    return seen


def wrapped(seen):
    """True if the walk came back to a place it had left (not just staying put)."""
    path = [p for i, p in enumerate(seen) if i == 0 or p != seen[i - 1]]
    return len(path) != len(set(path))


def check(name, open_screen, direction, times=30):
    clear()
    k.window("home"); time.sleep(1.2)
    open_screen(); time.sleep(2.5)
    a = press(direction, times)
    b = press(OPPOSITE[direction], times)
    bad = wrapped(a) or wrapped(b)
    end_a, end_b = a[-1], b[-1]
    print(f"{'WRAPS' if bad else 'ok   '} {name:<34} {direction:>5}: stops at {end_a[1]}:{end_a[3][:22]!r:<26} {OPPOSITE[direction]:>5}: stops at {end_b[1]}:{end_b[3][:22]!r}")
    if bad:
        print("      ", " > ".join(f"{p[1]}:{p[3][:12]}" for p in a))
        print("      ", " > ".join(f"{p[1]}:{p[3][:12]}" for p in b))
    clear()
    return bad


def builtin(*cmds):
    def run():
        for c in cmds:
            k.builtin(c); time.sleep(.8)
    return run


def videos(path, section="movies", focus=None, view=None):
    def run():
        k.builtin(f"SetProperty(oak_section,{section},home)")
        k.window("videos", path); time.sleep(2.5)
        if view:
            k.builtin(f"Container.SetViewMode({view})"); time.sleep(1.5)
        if focus:
            k.builtin(f"SetFocus({focus})"); time.sleep(.6)
    return run


def py(code):
    return builtin(f'RunScript(script.oakline.dev,"py:{code}")')


SCREENS = [
    ("Movies folder, list", videos(FOLDER, view=50), "down"),
    ("Movies folder, posters", videos(FOLDER, view=500), "right"),
    ("Movie library, posters", videos("videodb://movies/titles/", "files", view=500), "down"),
    ("Music albums", builtin("SetProperty(oak_section,music,home)", "ActivateWindow(Music,musicdb://albums/,return)"), "down"),
    ("Movies: option chips", videos(FOLDER, focus=9040), "right"),
    ("Movies: Options panel", lambda: (videos(FOLDER, focus=9046)(), k.rpc("Input.Select"), time.sleep(1)), "down"),
    ("Top tabs", builtin("SetFocus(9000,0,absolute)"), "right"),
    ("Home row: Movies and shows", builtin("SetFocus(8600)"), "right"),
    ("Home rows, top to bottom", builtin("SetFocus(8600)"), "down"),
    ("Settings cards", builtin("ActivateWindow(Settings)"), "down"),
    ("Settings > Player: categories", builtin("ActivateWindow(PlayerSettings)"), "down"),
    ("Settings > Player: settings", builtin("ActivateWindow(PlayerSettings)", "SetFocus(5)"), "down"),
    ("Settings > Interface: settings", builtin("ActivateWindow(InterfaceSettings)", "SetFocus(5)"), "down"),
    ("Skin settings", builtin("ActivateWindow(SkinSettings)"), "down"),
    ("System info: categories", builtin("ActivateWindow(SystemInfo)"), "down"),
    ("Add-ons page", builtin("ActivateWindow(1152)"), "down"),
    ("Add-ons page: categories", builtin("ActivateWindow(1152)", "SetFocus(9200)"), "right"),
    ("More page", builtin("ActivateWindow(1154)"), "down"),
    ("Add-on browser", builtin("ActivateWindow(AddonBrowser,addons://user/,return)"), "down"),
    ("Profiles", builtin("ActivateWindow(Profiles)"), "down"),
    ("Event log", builtin("ActivateWindow(EventLog)", "SetFocus(50)"), "down"),
    ("Dialog: select list", py("xbmcgui.Dialog().select('Pick', ['One', 'Two', 'Three', 'Four'])"), "down"),
    ("Dialog: select buttons", py("xbmcgui.Dialog().multiselect('Pick', ['One', 'Two'])") , "right"),
    ("Dialog: context menu", py("xbmcgui.Dialog().contextmenu(['Play', 'Queue', 'Mark as watched', 'Information'])"), "down"),
    ("Dialog: yes / no", py("xbmcgui.Dialog().yesno('Title', 'Text')"), "right"),
    ("Dialog: video info buttons", videos("videodb://movies/titles/", "files", view=50), "info"),
]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    bad = 0
    for name, opener, direction in SCREENS:
        if direction == "info":
            def opener_info(o=opener):
                o(); k.rpc("Input.Info"); time.sleep(2)
            bad += check(name, opener_info, "right")
        else:
            bad += check(name, opener, direction)
    k.window("home")
    print(f"\n{bad} wrapped")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
