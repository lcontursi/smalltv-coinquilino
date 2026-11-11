"""Il manuale (docs/manual, docs/manuale) e i README: ogni collegamento interno porta a un file e a
un titolo che esistono; le due lingue hanno le stesse pagine."""
import glob
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..")


def slug(title):
    s = title.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def anchors(path):
    text = open(path, encoding="utf-8").read()
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return {slug(m) for m in re.findall(r"^#+\s+(.+)$", text, re.M)}


def test_internal_links_resolve():
    files = glob.glob(os.path.join(ROOT, "docs", "manua*", "*.md")) + \
        [os.path.join(ROOT, "README.md"), os.path.join(ROOT, "README.it.md")]
    bad = []
    for f in files:
        text = re.sub(r"```.*?```", "", open(f, encoding="utf-8").read(), flags=re.S)
        for link in re.findall(r"\]\(([^)\s]+)\)", text):
            if link.startswith(("http", "mailto:")):
                continue
            path, _, frag = link.partition("#")
            target = os.path.normpath(os.path.join(os.path.dirname(f), path)) if path else f
            if not os.path.exists(target):
                bad.append((os.path.basename(f), link))
            elif frag and target.endswith(".md") and frag not in anchors(target):
                bad.append((os.path.basename(f), link))
    assert not bad, bad


def test_both_languages_have_every_page():
    en = glob.glob(os.path.join(ROOT, "docs", "manual", "*.md"))
    it = glob.glob(os.path.join(ROOT, "docs", "manuale", "*.md"))
    assert len(en) == len(it) == 9
