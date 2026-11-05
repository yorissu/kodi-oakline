"""Checks skin.oakline for mistakes that would only show on the TV.

    python tools/skincheck.py        # prints the problems; exit code 1 if there are any

Used by build_zip.py (no zip is written for a broken skin) and by
tests/test_skin.py. It checks that:
  - every XML file parses, and every texture it names exists, with the same
    upper/lower case as the file (Windows doesn't care, the Pi does);
  - every include a window uses is defined, every named colour exists in
    every colour theme, and no window reuses an id of the top bar;
  - every font file exists;
  - no grouplist has a child without an id (a dead end for Up/Down);
  - no list wraps round at its ends (see tools/nowrap.py).
"""
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
SKIN = ROOT / "skin.oakline"
# fonts Kodi itself provides (media/Fonts)
KODI_FONTS = {"arial.ttf", "teletext.ttf"}
# colour names Kodi resolves without a theme entry
KNOWN_COLOURS = {"lightgrey"}


def check():
    """Parse every XML file and make sure referenced textures exist. Returns a list of problems."""
    problems = []
    media = SKIN / "media"
    global MEDIA_EXACT
    MEDIA_EXACT = {p.relative_to(media).as_posix() for p in media.rglob("*") if p.is_file()}
    for xml in sorted((SKIN / "xml").glob("*.xml")) + [SKIN / "addon.xml", *sorted((SKIN / "colors").glob("*.xml"))]:
        is_addon = xml.name == "addon.xml"
        try:
            ElementTree.parse(xml)
        except ElementTree.ParseError as e:
            problems.append(f"{xml.relative_to(ROOT)}: {e}")
            continue
        text = xml.read_text(encoding="utf-8")
        # literal texture names (skip $INFO/$VAR/$PARAM ones, which are resolved at runtime)
        for name in ([] if is_addon else set(re.findall(r">([\w/.-]+\.png)<", text))):
            if not (media / name).exists() and not name.startswith("Default"):
                problems.append(f"{xml.relative_to(ROOT)}: missing texture media/{name}")
            elif (media / name).exists() and name not in MEDIA_EXACT:
                # Windows finds it whatever the case; the Pi (Linux) does not
                problems.append(f"{xml.relative_to(ROOT)}: texture {name} differs in case from the file in media/")
    problems += check_refs()
    problems += check_grouplists()
    problems += check_wrapping()
    for needed in ("addon.xml", "xml/Font.xml", "xml/Home.xml", "colors/defaults.xml"):
        if not (SKIN / needed).exists():
            problems.append(f"missing {needed}")
    for font in set(re.findall(r"<filename>([^<]+)</filename>", (SKIN / "xml" / "Font.xml").read_text(encoding="utf-8"))):
        if not (SKIN / "fonts" / font).exists() and font.lower() not in KODI_FONTS:
            problems.append(f"Font.xml: missing fonts/{font}")
    return problems


def check_refs():
    """Every include a window uses must be defined, and every named colour must
    exist in every colour theme (a theme missing a name draws it white)."""
    problems = []
    xmls = sorted((SKIN / "xml").glob("*.xml"))
    texts = {x: x.read_text(encoding="utf-8") for x in xmls}
    defined = set()
    for t in texts.values():
        defined |= set(re.findall(r'<include name="([^"]+)"', t))
    defined |= {"OptionsNone"}
    for x, t in texts.items():
        used = set(re.findall(r"<include(?: condition=\"[^\"]*\")?>([^<$]+)</include>", t))
        used |= {u for u in re.findall(r'<include content="([^"$]+)"', t)}
        for name in sorted(used - defined):
            problems.append(f"{x.relative_to(ROOT)}: include {name} is not defined")
    # the top bar (include "Rail") owns these ids; a window reusing one breaks focus
    bar_ids = {"9000", "9094", "9095", "9096", "9097", "9098"}
    for x, t in texts.items():
        if 'content="Rail"' in t:
            for i in sorted(bar_ids & set(re.findall(r'id="(\d+)"', t))):
                problems.append(f"{x.relative_to(ROOT)}: id {i} is used by the top bar")
    themes = {}
    for c in sorted((SKIN / "colors").glob("*.xml")):
        themes[c.name] = set(re.findall(r'<color name="([^"]+)"', c.read_text(encoding="utf-8")))
    names = set().union(*themes.values())
    for theme, have in themes.items():
        for missing in sorted(names - have):
            problems.append(f"colors/{theme}: no colour {missing}")
    for x, t in texts.items():
        for name in set(re.findall(r'(?:color>|colordiffuse=")([A-Za-z][A-Za-z0-9]*)[<"]', t)):
            if name not in names and name not in KNOWN_COLOURS and not re.fullmatch(r"[0-9A-Fa-f]{8}", name):
                problems.append(f"{x.relative_to(ROOT)}: colour {name} is not in the themes")
    return problems


def check_wrapping():
    """No list may wrap round at its ends (user rule): see tools/nowrap.py."""
    sys.path.insert(0, str(ROOT / "tools"))
    import nowrap  # noqa: E402
    problems = []
    for path in sorted((SKIN / "xml").glob("*.xml")):
        if path.name in ("Includes_Folders.xml", "Timers.xml", "Font.xml"):
            continue
        text = path.read_text(encoding="utf-8")
        for ctype, cid, open_end, direct in nowrap.containers(text):
            need = nowrap.missing(ctype, direct)
            if need:
                line = text.count(chr(10), 0, open_end) + 1
                problems.append(f"{path.relative_to(ROOT)}:{line}: {ctype} {cid or '(no id)'} wraps at {' and '.join(need)} (python tools/nowrap.py --fix)")
    return problems


def check_grouplists():
    """Kodi links each child of a grouplist to its neighbours by id. A child
    without one (a heading label, a spacer image, a group) is a dead end for
    Up/Down; a child with an id that can't take focus is passed through. So
    every direct child of a grouplist needs an id."""
    problems = []
    for x in sorted((SKIN / "xml").glob("*.xml")):
        try:
            root = ElementTree.parse(x).getroot()
        except ElementTree.ParseError:
            continue
        for gl in root.iter("control"):
            if gl.get("type") != "grouplist":
                continue
            focusable = {"button", "radiobutton", "togglebutton", "edit", "spincontrolex", "sliderex", "list", "panel", "fixedlist", "wraplist", "colorbutton"}
            if not any((c.tag == "control" and c.get("type") in focusable) or c.tag == "include" for c in gl):
                continue  # layout only: nothing in it takes focus
            for child in gl:
                if child.tag == "control" and not child.get("id"):
                    label = child.findtext("label") or child.get("type")
                    problems.append(f"{x.relative_to(ROOT)}: grouplist {gl.get('id', '?')} has a {child.get('type')} without an id ({label[:30]!r}): Up/Down stop there")
                elif child.tag == "include" and child.get("content") == "OptionHeading" and child.find("param[@name='id']") is None:
                    problems.append(f"{x.relative_to(ROOT)}: grouplist {gl.get('id', '?')} has an OptionHeading without an id")
    return problems



def main():
    problems = check()
    for p in problems:
        print("  -", p)
    print(f"{len(problems)} problems" if problems else "Skin check passed.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
