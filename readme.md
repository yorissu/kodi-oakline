# Oakline for Kodi

A Kodi skin for the living-room TV in flat navy, gray, warm white and oak: no gradients, no rounded corners. Top tabs, a Movies page that browses your own videos folder, Music, Add-ons, light and dark themes that can follow the time of day, and every Kodi setting still in reach. Works on Kodi 21 (Omega) or newer, LibreELEC on a Raspberry Pi included, and is used with a TV remote.

## Installation

Done once, in Kodi, with the remote. Menu names are from Kodi 21 with the default skin.

1. **Allow outside add-ons:** Settings → System → Add-ons → switch on **Unknown sources** → Yes.
2. **Add the source:** Settings → File manager → **Add source** → `<None>` → type `https://yorissu.github.io/kodi-oakline/` → OK → name it `oakline` → OK.
   (Tip: the Kore or Yatse phone apps let you type this on your phone.)
3. **Install the repository:** Add-ons → add-on browser (box icon, top left) → **Install from zip file** → `oakline` → `repository.oakline-….zip`.
4. **Install the skin:** add-on browser → **Install from repository** → Oakline repository → Look and feel → Skin → **Oakline** → Install → Yes to switch.

Until the repository is published on GitHub, install `dist/skin.oakline-<version>.zip` with **Install from zip file** instead (see Building).

## Usage

- **Home:** a preview of the focused item and rows: your videos folder A–Z, recently added, and genre rows from Kodi's library when it has them. Until a videos folder is chosen, a setup card asks for one.
- **Movies:** browses the videos folder you pick (Settings → Appearance → Videos folder). A video file plays; a folder is a show and opens to the videos inside it. Back at the top goes Home: Movies never climbs above your folder. Folder tiles show a frame of the show's first video when Kodi has one.
- **Music:** albums; Back at the top goes Home.
- **Add-ons, More:** video add-ons, and everything else Kodi has (library screens, pictures, games, playlists, weather, Video files to browse anywhere).
- **Options:** Up from any list shows chips (Sort, Order, Layout, Filter, Options); Options opens a side panel with the rest.
- **Lists stop at their ends:** pressing past the first or last item does nothing, in every list.
- **Playing a video:** pausing brings up the controls (Play selected, so OK resumes); skipping with the arrows shows the timeline only; OK opens the controls any time, Back closes them.
- **Settings → Appearance:** Dark, Light, or Auto (light by day, dark at night, with the times of day and night to choose), the 24-hour clock, and the videos folder.
- **Updates:** Kodi installs new releases automatically.

Kodi settings the skin expects (Settings → Media → Videos): **Default select action** = Show information (selecting a movie opens its details), **Show "All seasons" item** off, and **Extract thumbnails from video files** on for the folder frames.

## Building

Needs only Python 3. In the project folder:

```bash
python build_zip.py
```

This checks the skin (`tools/skincheck.py`: XML, textures and their case, includes, colours, focus dead ends, wrapping lists) and writes `dist/` with two zips and `SHA256SUMS`:

- `skin.oakline-<version>.zip`, the skin. Install it on a Kodi with **Install from zip file** to try it.
- `repository.oakline-<version>.zip`, the repository add-on that points Kodi at the update site.

**Versions.** The skin's version comes from the git tag; `addon.xml` only holds a placeholder.

- `python build_zip.py --tag v1.3.8` builds version `1.3.8`, exactly what the release will contain.
- `python build_zip.py --tag v1.4.0-rc.2` builds the pre-release `1.4.0~rc.2`. Kodi needs the `~` to sort it below `1.4.0`; the tag and the zip's file name (`…-1.4.0-rc.2.zip`) never have it.
- Without `--tag` the version comes from git (`1.3.9~dev2` = 2 commits after v1.3.8), or is `0.0.0~dev` without git.

The repository add-on keeps its own version (`repository.oakline/addon.xml`, `1.0.0`), raised only when the update site's address changes.

`icon.png` and `license.txt` exist once, next to this readme; the build copies them into both zips.

**Releasing.** Push a tag `vX.Y.Z`: the Release workflow tests, builds, creates the GitHub release and rebuilds the Kodi update site on GitHub Pages. `vX.Y.Z-<suffix>` makes a pre-release that Kodi is never offered.

## Testing

```bash
python -m unittest discover -s tests
```

These need no Kodi: the skin check, no wrapping lists, packaging and the update site. What the skin does on screen is tested with a portable Kodi on Windows:

```bash
python tools/kodidev.py start       # launch the test Kodi (portable, own profile in dev/kodi/portable_data)
python tools/navtest.py             # every screen: something focused on open and after each arrow key
python tools/wraptest.py            # 26 screens: pressing past both ends of a list stops there
python tools/appearancetest.py      # Settings > Appearance by remote keys, step by step
python tools/playertest.py          # player controls: pause brings up the buttons, Back closes them
python tools/kodidev.py stop
```

The test Kodi only runs while your own Kodi is closed (Windows allows one). It browses fake data only: `dev/folders` (a stand-in videos folder) and a generated library.

## Developing

`dev/` (the portable Kodi and its fake library) stays on this machine and is not in git.

```bash
python tools/kodidev.py reload      # copy the skin into the test Kodi + ReloadSkin()
python tools/kodidev.py shot home   # screenshot -> dev/shots/home.png
python tools/kodidev.py keys down right select back
python tools/kodidev.py log 200
python tools/make_folder_previews.py   # regenerate the folder-frame loaders and timers
python tools/make_keyboard.py       # regenerate DialogKeyboard.xml
python tools/make_numeric.py        # regenerate DialogNumeric.xml (number pad)
python tools/nowrap.py --fix        # give a new list stops at its ends
```

After adding a window file Kodi had already failed to load, restart Kodi: reload doesn't clear that, and an open media window stays empty after a reload. The D: drive can't hold junctions, so `reload` mirrors the skin into Kodi's add-ons with robocopy. Remote control goes through Kodi's JSON-RPC web server on port 8089; the generated login is in `dev/devconfig.json`.

Rebuilding the test setup from scratch:

```bash
python tools/make_media.py          # icons + flat textures into the skin
python tools/make_library.py        # fake movies/shows with palette artwork
python tools/make_music.py          # fake music library (short tagged tracks, covers)
python tools/make_video.py          # a playable test video, for the player screens
python tools/kodidev.py setup       # profile, sources (Kodi closed)
python tools/kodidev.py start && python tools/kodidev.py stop   # creates the databases
python tools/kodidev.py enable      # enable the skin, set library content, select the skin
python tools/kodidev.py start
python tools/kodidev.py scan && python tools/kodidev.py seed
python tools/make_demo_addon.py     # a fake video add-on with the listings streaming add-ons produce
```

Things learned about Kodi skinning along the way:

- Every child of a grouplist needs an id: Kodi links neighbours by id, so one without (a heading label) is a dead end for Up/Down.
- A list wraps when the move past its edge has no target; give both ends an action (`noop`), a grid all four.
- Changing the colour theme reloads the skin and resets focus.
- Inside a list layout, `Container(x).ListItemAbsolute(n)` answers for the layout's own item: pass data through window properties.
- Texture names are case-sensitive on the Pi.
