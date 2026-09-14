"""Read a work out of the published TEI, in the shape the pipeline expects.

The working copy keeps every poem twice: once as the parsed JSON the pipeline writes and reads, and
once as the TEI that is published. This repository publishes only the TEI -- shipping the JSON as well
would be fifty megabytes of the same poems in a second format, and a corpus that carries two copies of
its texts will eventually carry two different copies.

So the scripts that need parsed poems read them from the TEI here. The shape returned is the same one
`data/works/<slug>.json` has in the working copy, so nothing downstream knows the difference:

    {"slug": ..., "title": ..., "author": ...,
     "sections": [{"id": ..., "title": ..., "stanzas": [[line, line, ...], ...]}, ...]}
"""
import json
import os
import xml.etree.ElementTree as ET

from _paths import TEI as TEI_DIR, WORKS

NS = "{http://www.tei-c.org/ns/1.0}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def _text(el):
    """The line as printed, with any inline markup flattened out of the way."""
    return "".join(el.itertext()).strip()


def work(slug):
    """One work, or None if this repository does not carry it."""
    path = os.path.join(TEI_DIR, slug + ".xml")
    if not os.path.exists(path):
        return None
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return None
    root = tree.getroot()

    def header(tag):
        el = root.find(".//%stitleStmt/%s" % (NS, NS + tag))
        return _text(el) if el is not None else ""

    sections = []
    body = root.find(".//%sbody" % NS)
    if body is None:
        return None
    for div in body.iter(NS + "div"):
        stanzas = []
        for lg in div.iter(NS + "lg"):
            if lg.get("type") != "stanza":
                continue
            lines = [_text(l) for l in lg.findall(NS + "l")]
            if lines:
                stanzas.append(lines)
        if not stanzas:
            continue
        head = div.find(NS + "head")
        sections.append({
            "id": div.get(XML_ID) or "",
            "title": _text(head) if head is not None else "",
            "stable": div.get("n") or "",
            "stanzas": stanzas,
        })
    return {"slug": slug, "title": header("title"), "author": header("author"),
            "sections": sections}


def slugs():
    """Every work this repository carries."""
    if not os.path.isdir(TEI_DIR):
        return []
    return sorted(f[:-4] for f in os.listdir(TEI_DIR) if f.endswith(".xml"))


def load_work(slug):
    """One work's poems, from wherever this tree keeps them.

    The working copy has the parsed JSON beside the rest of the pipeline's output and reads that; this
    repository has only the TEI, and the same poems come back out of it in the same shape. Every script
    that needs poems goes through here, so neither tree is a special case anywhere else.
    """
    path = os.path.join(WORKS, slug + ".json")
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            return None
    return work(slug)
