"""Make every list in the skin stop at its ends instead of wrapping round.

    python tools/nowrap.py          # report lists that would wrap
    python tools/nowrap.py --fix    # add the missing <onup>/<ondown> (or
                                    # <onleft>/<onright>) noop to each

Kodi wraps a list, panel or grouplist round to the other end when the move
past its edge has no target. The user wants every list to stop there instead,
so each container needs an explicit action at both ends of its direction:
noop when nothing else should happen. Hidden helper lists (left -4000) are
skipped. A wraplist always wraps by design; there are none in the skin.
"""
import re
import sys
from pathlib import Path

XML = Path(__file__).resolve().parent.parent / "skin.oakline" / "xml"
CONTAINERS = ("list", "panel", "fixedlist", "wraplist", "grouplist")
TAG = re.compile(r"<control\b[^>]*?/>|<control\b[^>]*>|</control>")


def containers(text):
    """(type, id, open_end, close_start, direct_child_text) per container, by nesting."""
    stack, out = [], []
    for m in TAG.finditer(text):
        tok = m.group(0)
        if tok.endswith("/>"):
            continue
        if tok.startswith("</"):
            start, open_tag, open_end = stack.pop()
            ctype = re.search(r'type="([^"]+)"', open_tag)
            if ctype and ctype.group(1) in CONTAINERS:
                body = text[open_end:m.start()]
                # direct children only: blank out nested controls and layouts/content
                direct = re.sub(r"<control\b.*?</control>", "", body, flags=re.S)
                direct = re.sub(r"<(itemlayout|focusedlayout|content)\b.*?</\1>", "", direct, flags=re.S)
                cid = re.search(r'id="([^"]*)"', open_tag)
                out.append((ctype.group(1), cid.group(1) if cid else "", open_end, direct))
            continue
        stack.append((m.start(), tok, m.end()))
    return out


def missing(ctype, direct):
    if re.search(r"<left>\s*-4000\s*</left>", direct):
        return []
    horizontal = re.search(r"<orientation>\s*horizontal\s*</orientation>", direct)
    ends = ("onleft", "onright") if horizontal else ("onup", "ondown")
    if ctype == "panel":
        ends = ("onup", "ondown", "onleft", "onright")  # a grid wraps both ways
    # an end with a single conditional action still wraps when the condition
    # doesn't hold: it needs one without a condition, or a pair of conditional
    # ones that between them cover every case (A / !A)
    def covered(e):
        return re.search(rf"<{e}>", direct) or len(re.findall(rf"<{e} condition=", direct)) >= 2
    return [e for e in ends if not covered(e)]


def main():
    fix = "--fix" in sys.argv
    total = 0
    for path in sorted(XML.glob("*.xml")):
        if path.name in ("Includes_Folders.xml", "Timers.xml", "Font.xml"):
            continue
        text = path.read_text(encoding="utf-8")
        inserts = []
        for ctype, cid, open_end, direct in containers(text):
            need = missing(ctype, direct)
            if not need:
                continue
            total += len(need)
            line = text.count("\n", 0, open_end) + 1
            print(f"{path.name}:{line}  {ctype} {cid or '(no id)'}: wraps at {' and '.join(need)}")
            indent = re.match(r"\r?\n([\t ]*)", text[open_end:])
            pad = indent.group(1) if indent else "\t"
            nl = "\r\n" if "\r\n" in text[open_end:open_end + 4] else "\n"
            inserts.append((open_end, "".join(f"{nl}{pad}<{e}>noop</{e}>" for e in need)))
        if fix and inserts:
            for pos, add in sorted(inserts, reverse=True):
                text = text[:pos] + add + text[pos:]
            path.write_text(text, encoding="utf-8", newline="")
    print(f"{total} list ends {'fixed' if fix else 'wrap'}")
    return total


if __name__ == "__main__":
    sys.exit(0 if main() == 0 or "--fix" in sys.argv else 1)
