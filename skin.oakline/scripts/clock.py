"""Clock format for Oakline.

    RunScript(special://skin/scripts/clock.py)          # first start: switch Kodi to 24 h, once
    RunScript(special://skin/scripts/clock.py,toggle)   # Skin settings: flip 12 h / 24 h

Kodi formats every time it shows from its own setting
(Settings > Interface > Regional > Use 24-hour clock), so the skin sets that
setting instead of formatting the clock itself. On first start it is set to
24 hours once; after that the user's choice is left alone.
"""
import json
import sys

import xbmc

SETTING = "locale.use24hourclock"
DONE = "oak_clock24_done"


def rpc(method, params):
    return json.loads(xbmc.executeJSONRPC(json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "toggle":
        # an AM/PM marker means the clock is on 12 hours right now
        twelve = xbmc.getInfoLabel("System.Time(xx)") != ""
        rpc("Settings.SetSettingValue", {"setting": SETTING, "value": "24hours" if twelve else "12hours"})
        return
    if xbmc.getCondVisibility(f"Skin.HasSetting({DONE})"):
        return
    rpc("Settings.SetSettingValue", {"setting": SETTING, "value": "24hours"})
    xbmc.executebuiltin(f"Skin.SetBool({DONE})")


main()
