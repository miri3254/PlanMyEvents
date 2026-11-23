"""Extract all textual content from recipe DOCX files into one UTF-8 report."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "מתכונים"
OUTPUT = SOURCE / "כל_המתכונים_טקסט_מלא.md"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def node_text(node: ET.Element) -> str:
    parts: list[str] = []
    for child in node.iter():
        if child.tag == W + "t" and child.text:
            parts.append(child.text)
        elif child.tag == W + "tab":
            parts.append("\t")
        elif child.tag in {W + "br", W + "cr"}:
            parts.append("\n")
    return "".join(parts).strip()


def extract_docx(path: Path) -> str:
    sections: list[str] = []
    with zipfile.ZipFile(path) as archive:
        xml_names = [
            name
            for name in archive.namelist()
            if re.fullmatch(
                r"word/(document|header\d+|footer\d+|footnotes|endnotes|comments)\.xml",
                name,
            )
        ]
        xml_names.sort(key=lambda name: (name != "word/document.xml", name))
        for xml_name in xml_names:
            root = ET.fromstring(archive.read(xml_name))
            lines: list[str] = []
            for node in root.iter():
                if node.tag == W + "p":
                    text = node_text(node)
                    if text:
                        lines.append(text)
            if lines:
                label = "גוף המסמך" if xml_name == "word/document.xml" else xml_name
                sections.append(f"[{label}]\n" + "\n".join(lines))
    return "\n\n".join(sections).strip()


def main() -> None:
    files = sorted(SOURCE.rglob("*.docx"), key=lambda p: str(p.relative_to(SOURCE)))
    chunks = [
        "# כל המתכונים — טקסט מלא",
        "",
        f"מספר קבצים: {len(files)}",
        "",
    ]
    for index, path in enumerate(files, 1):
        relative = path.relative_to(SOURCE)
        chunks.extend(
            [
                f"## {index}. {path.stem.strip()}",
                "",
                f"- תיקייה: `{relative.parent}`",
                f"- קובץ: `{path.name}`",
                f"- נתיב יחסי: `{relative}`",
                "",
                extract_docx(path) or "[לא נמצא טקסט במסמך]",
                "",
                "---",
                "",
            ]
        )
    OUTPUT.write_text("\n".join(chunks), encoding="utf-8-sig")
    print(f"Extracted {len(files)} files to {OUTPUT}")


if __name__ == "__main__":
    main()
