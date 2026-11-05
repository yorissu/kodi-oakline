"""The player's controls by remote: pause brings up the buttons, skipping keeps
the bare timeline, Back really closes them, and the button row stops at its ends.

    python tools/playertest.py       (dev Kodi running; ends with "0 failed")
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kodidev as k  # noqa: E402

VIDEO = k.ROOT / "dev" / "folders" / "Northbound.avi"
fails = 0


# real key presses through Kodi's keyboard keymap, as a remote's buttons arrive
BUTTONS = {"pause": "space", "select": "return", "back": "backspace", "left": "left", "right": "right", "up": "up", "down": "down"}


def press(name):
    k.rpc("Input.ButtonEvent", {"button": BUTTONS[name], "keymap": "KB", "holdtime": 0})


def state():
    r = k.rpc("XBMC.GetInfoLabels", {"labels": ["System.CurrentControlId"]})
    b = k.rpc("XBMC.GetInfoBooleans", {"booleans": ["Window.IsActive(videoosd)", "Window.IsVisible(seekbar)", "Player.Paused", "Player.HasVideo"]})
    return {"osd": b["Window.IsActive(videoosd)"], "bar": b["Window.IsVisible(seekbar)"], "paused": b["Player.Paused"],
            "video": b["Player.HasVideo"], "id": r["System.CurrentControlId"]}


def step(tag, action, wait=1.5, **want):
    global fails
    if action:
        press(action)
    time.sleep(wait)
    s = state()
    bad = {key: (s[key], v) for key, v in want.items() if s[key] != v}
    fails += bool(bad)
    print(f"{'FAIL' if bad else 'ok  '} {tag:<40} osd={s['osd']!s:<5} bar={s['bar']!s:<5} paused={s['paused']!s:<5} focus={s['id']}" + (f"   wanted {bad}" if bad else ""))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    k.window("home"); time.sleep(1.5)
    k.builtin(f"PlayMedia({VIDEO})"); time.sleep(5)
    step("playing: nothing on screen", None, 0, video=True, osd=False, paused=False)
    step("Pause key -> buttons, Play focused", "pause", osd=True, paused=True, id="702")
    step("OK -> resumes, buttons stay", "select", osd=True, paused=False)
    step("Back -> buttons close", "back", osd=False, paused=False)
    step("Right (skip) -> timeline only", "right", 2, osd=False, bar=True)
    time.sleep(4)
    step("Pause key again -> buttons", "pause", osd=True, paused=True, id="702")
    step("Back while paused -> buttons close", "back", osd=False, paused=True)
    step("  ...and stay closed", None, 3, osd=False, paused=True)
    step("OK while paused -> buttons", "select", osd=True, paused=True)
    for _ in range(4):
        press("left"); time.sleep(.4)
    step("Left to the first button, once more", "left", .6, id="701")
    for _ in range(9):
        press("right"); time.sleep(.4)
    step("Right to the last button, once more", "right", .6, id="707")
    k.builtin("SetFocus(702)"); time.sleep(.5)
    step("Play button -> resumes", "select", osd=True, paused=False)
    step("Pause button -> pauses, buttons stay", "select", osd=True, paused=True, id="702")
    k.builtin("PlayerControl(Stop)"); time.sleep(2)
    k.window("home")
    print(f"\n{fails} failed")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
