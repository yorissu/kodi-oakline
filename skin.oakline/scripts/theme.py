"""Oakline's colour themes: light, dark, or auto (light by day, dark at night,
like homed). Kodi keeps the colours in Settings > Interface > Skin > Colours;
the mode and the two times are skin strings:

    oak_theme_mode    "auto", or empty for a fixed theme
    oak_day_begins    HH:MM, 07:00 until changed
    oak_night_begins  HH:MM, 21:00 until changed; day runs from one to the other

    RunScript(special://skin/scripts/theme.py,light|dark)   fixed theme
    RunScript(special://skin/scripts/theme.py,auto)         by time of day
    RunScript(special://skin/scripts/theme.py)              flip (fixed)
    RunScript(special://skin/scripts/theme.py,time,day|night)  pick a time
    RunScript(special://skin/scripts/theme.py,tick)         apply what is due now
    RunScript(special://skin/scripts/theme.py,startup)      Startup.xml: tick, plus a one-off fix

In auto, each tick applies the theme for the time of day and sets a Kodi alarm
for the next change. Changing the colours reloads the skin, so while a video
plays or a dialog is open the change waits (Window(home).Property(oak_theme_pending);
a skin timer ticks again once that is over).
"""
import datetime
import json
import sys

import xbmc
import xbmcgui

SETTING = "lookandfeel.skincolors"
DARK, LIGHT = "SKINDEFAULT", "light"
DEFAULTS = {"day": "07:00", "night": "21:00"}
HOME = xbmcgui.Window(10000)
ALARM = "oak_theme"


def rpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}))).get("result")


def colours():
    r = rpc("Settings.GetSettingValue", {"setting": SETTING})
    return LIGHT if r and r.get("value") == LIGHT else DARK


def skin_string(name):
    return xbmc.getInfoLabel(f"Skin.String({name})")


def minutes(which):
    """Day or night start, in minutes after midnight."""
    text = skin_string(f"oak_{which}_begins") or DEFAULTS[which]
    try:
        h, m = (int(x) for x in text.strip().split(":")[:2])
        if 0 <= h < 24 and 0 <= m < 60:
            return h * 60 + m
    except ValueError:
        pass
    h, m = DEFAULTS[which].split(":")
    return int(h) * 60 + int(m)


def is_day(now):
    day, night, t = minutes("day"), minutes("night"), now.hour * 60 + now.minute
    if day == night:
        return True
    if day < night:
        return day <= t < night
    return t >= day or t < night  # day runs past midnight


def apply(value):
    """Set the colours unless they already are; wait while it would interrupt."""
    if colours() == value:
        HOME.clearProperty("oak_theme_pending")
        return
    if xbmc.getCondVisibility("Player.HasVideo | System.HasActiveModalDialog"):
        HOME.setProperty("oak_theme_pending", "1")
        return
    HOME.clearProperty("oak_theme_pending")
    rpc("Settings.SetSettingValue", {"setting": SETTING, "value": value})


def schedule(now):
    """A Kodi alarm for the next day or night start."""
    xbmc.executebuiltin(f"CancelAlarm({ALARM},true)")
    t = now.hour * 60 + now.minute
    waits = [(m - t) % (24 * 60) or 24 * 60 for m in (minutes("day"), minutes("night"))]
    seconds = min(waits) * 60 - now.second + 5  # just after the minute begins
    h, rest = divmod(seconds, 3600)
    xbmc.executebuiltin(f"AlarmClock({ALARM},RunScript(special://skin/scripts/theme.py,tick),{h}:{rest // 60:02d}:{rest % 60:02d},silent)")


def tick():
    if skin_string("oak_theme_mode") != "auto":
        xbmc.executebuiltin(f"CancelAlarm({ALARM},true)")
        HOME.clearProperty("oak_theme_pending")
        return
    now = datetime.datetime.now()
    schedule(now)  # first: changing the colours reloads the skin
    apply(LIGHT if is_day(now) else DARK)


def fixed(value):
    xbmc.executebuiltin("Skin.Reset(oak_theme_mode)")
    tick()  # cancels the alarm
    rpc("Settings.SetSettingValue", {"setting": SETTING, "value": value})


def pick_time(which):
    heading = "Day begins" if which == "day" else "Night begins"
    current = skin_string(f"oak_{which}_begins") or DEFAULTS[which]
    text = xbmcgui.Dialog().numeric(2, heading, current)
    try:
        h, m = (int(x) for x in text.strip().split(":")[:2])
    except ValueError:
        return
    if not (0 <= h < 24 and 0 <= m < 60):
        return
    other = minutes("night" if which == "day" else "day")
    if h * 60 + m == other:
        xbmcgui.Dialog().notification("Theme", "Day and night can't begin at the same time", xbmcgui.NOTIFICATION_WARNING, 4000)
        return
    xbmc.executebuiltin(f"Skin.SetString(oak_{which}_begins,{h:02d}:{m:02d})")
    xbmc.sleep(100)
    tick()


def startup():
    """Once: Oakline 1.3.3 briefly switched "Show parent folder items" off around
    the top of Movies and Music; if Kodi closed meanwhile it stayed off. Back on."""
    if not xbmc.getCondVisibility("Skin.HasSetting(oak_parent_items_restored)"):
        rpc("Settings.SetSettingValue", {"setting": "filelists.showparentdiritems", "value": True})
        xbmc.executebuiltin("Skin.SetBool(oak_parent_items_restored)")


def main():
    args = [a.lower() for a in sys.argv[1:]]
    want = args[0] if args else ""
    if want == "tick":
        tick()
    elif want == "startup":
        startup()
        tick()
    elif want == "auto":
        xbmc.executebuiltin("Skin.SetString(oak_theme_mode,auto)")
        xbmc.sleep(100)
        tick()
    elif want == "time" and len(args) > 1 and args[1] in DEFAULTS:
        pick_time(args[1])
    elif want in ("dark", "light"):
        fixed(LIGHT if want == "light" else DARK)
    else:
        fixed(DARK if colours() == LIGHT else LIGHT)


main()
